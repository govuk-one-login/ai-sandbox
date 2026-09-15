#!/usr/bin/env python3
"""Minimal egress-logging forward proxy for the di-kit sandbox.

Purpose
-------
Give visibility into the outbound network traffic that agents/tools make
from inside the sandbox. Tools are pointed at this proxy via the standard
HTTP_PROXY / HTTPS_PROXY environment variables. For every connection the
proxy writes a single JSON line to a log file:

  * HTTPS (and any TLS) traffic uses the CONNECT method. We log the target
    host:port and the bytes transferred each way with outcome "opened". We do
    NOT decrypt payloads (no MITM, no CA injection). Because sbx intercepts
    TLS and enforces any deny *inside* that session, the in-guest proxy
    cannot tell allowed from blocked for HTTPS — use `sbx policy log`
    (tools/watch-egress.py) for the authoritative verdict.
  * Plain HTTP traffic uses absolute-URI requests. We log the method, full
    URL and response status; a proxy 403/407 is recorded as "blocked".

Upstream chaining
-----------------
Docker Sandboxes already routes all guest egress through a host-side proxy
and normally sets HTTP_PROXY/HTTPS_PROXY in the guest. To avoid bypassing
that, this proxy can chain to a parent proxy given in EGRESS_UPSTREAM_PROXY:
CONNECT tunnels and HTTP requests are forwarded to the parent instead of
dialed directly. If EGRESS_UPSTREAM_PROXY is empty, connections are made
directly (the sandbox forwards raw TCP transparently, and this mode is used
for local testing).

Design notes
------------
* Standard library only (no pip install) — trivial to ship and to extend
  later (e.g. change `log_event` to also emit OTLP to a collector).
* Resilient: a failure handling one connection must never take down the
  proxy, because all sandbox egress depends on it once the env vars are set.

Usage
-----
    egress-proxy.py            # run the proxy (foreground)
    egress-proxy.py --wait     # block until the port accepts connections,
                               # then exit 0 (startup readiness probe)

Environment
-----------
    EGRESS_PROXY_HOST       listen address (default 127.0.0.1)
    EGRESS_PROXY_PORT       listen port    (default 8080)
    EGRESS_LOG_FILE         JSONL output path
                            (default ~/di-kit/monitoring/logs/egress.jsonl)
    EGRESS_UPSTREAM_PROXY   optional parent proxy URL to chain through
"""

import json
import os
import select
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlsplit

LISTEN_HOST = os.environ.get("EGRESS_PROXY_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("EGRESS_PROXY_PORT", "8080"))
DEFAULT_LOG = os.path.join(
    os.path.expanduser("~"), "di-kit", "monitoring", "logs", "egress.jsonl"
)
LOG_FILE = os.environ.get("EGRESS_LOG_FILE", DEFAULT_LOG)
SESSION_ID = os.environ.get("KIRO_SESSION_ID", "")

UPSTREAM_TIMEOUT = 30  # seconds to establish an upstream connection
TUNNEL_BUFFER = 65536

_log_lock = threading.Lock()


def _parse_upstream():
    """Return (host, port) of the parent proxy, or None for direct mode."""
    raw = os.environ.get("EGRESS_UPSTREAM_PROXY", "").strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "http://" + raw
    parts = urlsplit(raw)
    if not parts.hostname:
        return None
    return (parts.hostname, parts.port or 80)


UPSTREAM = _parse_upstream()


def log_event(**fields):
    """Append one JSON line describing a network event.

    Never raises: monitoring must not break the traffic it observes.
    Extend here to also forward events to an OTEL collector later.
    """
    record = {"ts": datetime.now(timezone.utc).isoformat()}
    if SESSION_ID:
        record["session_id"] = SESSION_ID
    record.update(fields)
    line = json.dumps(record, separators=(",", ":"))
    try:
        with _log_lock:
            with open(LOG_FILE, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except Exception as exc:  # pragma: no cover - best effort
        sys.stderr.write("egress-proxy: failed to write log: %s\n" % exc)


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # simple close-by-default semantics

    def log_message(self, *args, **kwargs):
        return  # silence default stderr access log

    def _client_ip(self):
        try:
            return self.request.getpeername()[0]
        except Exception:
            return ""

    # --- HTTPS / TLS tunneling ------------------------------------------
    def do_CONNECT(self):
        host, _, port_s = self.path.partition(":")
        try:
            port = int(port_s) if port_s else 443
        except ValueError:
            port = 443
        client = self._client_ip()
        via = "parent" if UPSTREAM else "direct"
        start = time.time()

        upstream = None
        status = None
        reason = ""
        try:
            if UPSTREAM:
                upstream, status, reason = self._open_parent_connect(
                    host, port)
            else:
                upstream = socket.create_connection(
                    (host, port), UPSTREAM_TIMEOUT)
                status, reason = 200, "OK (direct)"
        except (OSError, socket.error) as exc:
            # Upstream/origin unreachable. In direct mode a policy block is
            # indistinguishable from a network error at this layer.
            log_event(event="connect", outcome="error", host=host, port=port,
                      client=client, via=via, error=str(exc))
            try:
                self.send_error(502, "Bad Gateway")
            except (OSError, socket.error) as send_exc:
                log_event(event="send_error_failed", error=str(send_exc))
            return

        if upstream is None:
            # The parent proxy refused the tunnel: egress denied by policy.
            log_event(event="connect", outcome="blocked", host=host,
                      port=port, client=client, via=via, status=status,
                      reason=reason)
            try:
                self.send_error(status or 403, reason or "Forbidden")
            except (OSError, socket.error) as send_exc:
                log_event(event="send_error_failed", error=str(send_exc))
            return

        try:
            self.send_response(200, "Connection Established")
            self.end_headers()

            bytes_out, bytes_in = self._tunnel(self.connection, upstream)
        finally:
            try:
                upstream.close()
            except (OSError, socket.error):
                pass
        self.close_connection = True
        # We can only observe that the tunnel opened. sbx enforces any deny
        # inside the intercepted TLS session, which we can't read, so we do
        # NOT claim "allowed" here — the authoritative verdict comes from
        # `sbx policy log` (see tools/watch-egress.py).
        log_event(event="connect", outcome="opened", host=host, port=port,
                  client=client, via=via, status=200,
                  bytes_out=bytes_out, bytes_in=bytes_in,
                  duration_ms=int((time.time() - start) * 1000))

    def _open_parent_connect(self, host, port):
        """CONNECT to host:port through the parent proxy.

        Returns (socket, status, reason) when the parent establishes the
        tunnel (status 200), or (None, status, reason) when it refuses
        (for example a 403 policy block). Raises only if the parent proxy
        itself is unreachable.
        """
        sock = socket.create_connection(UPSTREAM, UPSTREAM_TIMEOUT)
        try:
            req = ("CONNECT %s:%d HTTP/1.1\r\nHost: %s:%d\r\n\r\n"
                   % (host, port, host, port)).encode("latin-1")
            sock.sendall(req)
            # Read the parent's response headers.
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = sock.recv(TUNNEL_BUFFER)
                if not chunk:
                    break
                buf += chunk
                if len(buf) > 65536:
                    break
            status, reason = self._parse_status_line(buf)
        except Exception:
            sock.close()
            raise
        if status == 200:
            return sock, status, reason
        try:
            sock.close()
        except Exception:
            pass
        return None, status, reason

    def _tunnel(self, client_sock, upstream_sock):
        """Relay both directions until either closes. Returns byte counts
        (client->upstream, upstream->client)."""
        bytes_out = 0
        bytes_in = 0
        socks = [client_sock, upstream_sock]
        try:
            while True:
                readable, _, errored = select.select(socks, [], socks, 60)
                if errored or not readable:
                    break
                for s in readable:
                    try:
                        data = s.recv(TUNNEL_BUFFER)
                    except Exception:
                        return bytes_out, bytes_in
                    if not data:
                        return bytes_out, bytes_in
                    if s is client_sock:
                        upstream_sock.sendall(data)
                        bytes_out += len(data)
                    else:
                        client_sock.sendall(data)
                        bytes_in += len(data)
        except (OSError, socket.error) as exc:
            log_event(event="tunnel_error", error=str(exc))
        return bytes_out, bytes_in

    # --- Plain HTTP forwarding ------------------------------------------
    def _proxy_http(self):
        client = self._client_ip()
        start = time.time()
        parts = urlsplit(self.path)
        host = parts.hostname or ""
        port = parts.port or 80
        origin_path = parts.path or "/"
        if parts.query:
            origin_path += "?" + parts.query

        if not host:
            self.send_error(400, "Bad Request")
            log_event(event="http_bad_request", method=self.command,
                      url=self.path, client=client)
            return

        body = b""
        length = self.headers.get("Content-Length")
        if length:
            try:
                body = self.rfile.read(int(length))
            except Exception:
                body = b""

        # When chaining, dial the parent proxy and keep the absolute-URI
        # request line; otherwise dial the origin and use origin-form.
        if UPSTREAM:
            target = UPSTREAM
            request_target = self.path
        else:
            target = (host, port)
            request_target = origin_path

        lines = ["%s %s HTTP/1.0" % (self.command, request_target)]
        sent_host = False
        for key in self.headers.keys():
            low = key.lower()
            if low in ("proxy-connection", "connection", "keep-alive"):
                continue
            if low == "host":
                sent_host = True
            for value in self.headers.get_all(key, []):
                lines.append("%s: %s" % (key, value))
        if not sent_host:
            lines.append("Host: %s" % host)
        lines.append("Connection: close")
        request_head = ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1")

        try:
            upstream = socket.create_connection(target, UPSTREAM_TIMEOUT)
        except (OSError, socket.error) as exc:
            log_event(event="http", outcome="error", method=self.command,
                      url=self.path, host=host, port=port, client=client,
                      via="parent" if UPSTREAM else "direct", error=str(exc))
            try:
                self.send_error(502, "Bad Gateway")
            except (OSError, socket.error) as send_exc:
                log_event(event="send_error_failed", error=str(send_exc))
            return

        via = "parent" if UPSTREAM else "direct"
        status = None
        reason = ""
        bytes_in = 0
        errored = False
        try:
            upstream.sendall(request_head)
            if body:
                upstream.sendall(body)
            first = True
            while True:
                chunk = upstream.recv(TUNNEL_BUFFER)
                if not chunk:
                    break
                if first:
                    first = False
                    status, reason = self._parse_status_line(chunk)
                bytes_in += len(chunk)
                self.wfile.write(chunk)
        except Exception as exc:
            errored = True
            log_event(event="http", outcome="error", method=self.command,
                      url=self.path, host=host, port=port, client=client,
                      via=via, error=str(exc))
        finally:
            try:
                upstream.close()
            except Exception:
                pass
            self.close_connection = True

        if errored:
            return
        # A forward proxy signals a policy block on plain HTTP with 403/407.
        # An origin can also return 403, so treat this as a strong hint
        # rather than proof; the raw status/reason are always recorded.
        if status is None:
            outcome = "error"
        elif UPSTREAM and status in (403, 407):
            outcome = "blocked"
        else:
            outcome = "allowed"
        log_event(event="http", outcome=outcome, method=self.command,
                  url=self.path, host=host, port=port, client=client,
                  status=status, reason=reason, via=via,
                  bytes_out=len(request_head) + len(body), bytes_in=bytes_in,
                  duration_ms=int((time.time() - start) * 1000))

    @staticmethod
    def _parse_status_line(chunk):
        """Parse an HTTP status line -> (status_code|None, reason_phrase)."""
        try:
            first_line = chunk.split(b"\r\n", 1)[0].decode("latin-1")
            parts = first_line.split(" ", 2)
            status = int(parts[1])
            reason = parts[2].strip() if len(parts) > 2 else ""
            return status, reason
        except Exception:
            return None, ""

    do_GET = _proxy_http
    do_POST = _proxy_http
    do_PUT = _proxy_http
    do_DELETE = _proxy_http
    do_HEAD = _proxy_http
    do_PATCH = _proxy_http
    do_OPTIONS = _proxy_http


def wait_for_ready(timeout=10.0):
    """Block until the proxy port accepts connections. Exit 0 on success,
    1 on timeout. Used as a startup readiness probe."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((LISTEN_HOST, LISTEN_PORT), 0.2):
                return 0
        except OSError:
            time.sleep(0.1)
    return 1


def main():
    if "--wait" in sys.argv[1:]:
        sys.exit(wait_for_ready())

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    log_event(event="proxy_start", host=LISTEN_HOST, port=LISTEN_PORT,
              log_file=LOG_FILE,
              upstream=("%s:%d" % UPSTREAM) if UPSTREAM else None)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        log_event(event="proxy_stop")


if __name__ == "__main__":
    main()

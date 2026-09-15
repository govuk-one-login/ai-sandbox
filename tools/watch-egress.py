#!/usr/bin/env python3
"""Live egress monitor for a Docker sandbox, driven by `sbx policy log`.

Runs on the HOST (not inside the sandbox) and reports the authoritative
allowed/blocked verdict for outbound connections as recorded by sbx's own
forward proxy. This is the reliable answer to "was this request blocked?" —
an in-guest proxy cannot tell, because sbx enforces the deny inside an
intercepted TLS session it can't read.

It polls `sbx policy log [SANDBOX] --json` on an interval and prints a live
feed of new activity (a new host, or an existing host seen again).

Usage
-----
    tools/watch-egress.py                 # all sandboxes, poll every 2s
    tools/watch-egress.py di-kiro         # only the named sandbox
    tools/watch-egress.py di-kiro -i 1    # 1s interval
    tools/watch-egress.py --once          # print current state once and exit
    tools/watch-egress.py --source-file snapshot.json   # parse saved JSON

Stdlib only. Ctrl-C to stop.
"""

import argparse
import datetime as dt
import json
import subprocess
import sys
import time

RED = "\033[31m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Live sandbox egress monitor "
                                            "(blocked/allowed) via sbx policy log.")
    p.add_argument("sandbox", nargs="?",
                   help="sandbox name to filter to (default: all sandboxes)")
    p.add_argument("-i", "--interval", type=float, default=2.0,
                   help="poll interval in seconds (default: 2.0)")
    p.add_argument("--once", action="store_true",
                   help="print the current state once and exit")
    p.add_argument("--source-file",
                   help="read policy-log JSON from a file instead of running "
                        "sbx (for testing)")
    p.add_argument("--no-color", action="store_true",
                   help="disable ANSI colour output")
    return p.parse_args(argv)


def fetch(args):
    """Return parsed policy-log JSON, or None on failure."""
    if args.source_file:
        try:
            with open(args.source_file, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError) as exc:
            sys.stderr.write("watch-egress: %s\n" % exc)
            return None
    cmd = ["sbx", "policy", "log", "--json"]
    if args.sandbox:
        cmd.insert(3, args.sandbox)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        sys.stderr.write("watch-egress: failed to run sbx: %s\n" % exc)
        return None
    if proc.returncode != 0:
        sys.stderr.write("watch-egress: sbx exited %d: %s\n"
                         % (proc.returncode, proc.stderr.strip()))
        return None
    try:
        return json.loads(proc.stdout)
    except ValueError as exc:
        sys.stderr.write("watch-egress: bad JSON from sbx: %s\n" % exc)
        return None


def iter_entries(data, sandbox):
    """Yield (verdict, entry) filtered to sandbox, sorted by last_seen."""
    rows = []
    for verdict, key in (("BLOCK", "blocked_hosts"),
                         ("ALLOW", "allowed_hosts")):
        for entry in (data.get(key) or []):
            if sandbox and entry.get("vm_name") != sandbox:
                continue
            rows.append((verdict, entry))
    rows.sort(key=lambda ve: ve[1].get("last_seen") or "")
    return rows


def short_time(iso):
    try:
        return dt.datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return (iso or "")[:19].replace("T", " ") or "------- --:--:--"


def render(marker, verdict, entry, use_color, show_vm):
    host = entry.get("host", "?")
    seen = short_time(entry.get("last_seen"))
    count = entry.get("count_since", "")
    detail = (entry.get("reason", "") if verdict == "BLOCK"
              else entry.get("proxy_type", ""))
    tag = verdict
    if use_color:
        color = RED if verdict == "BLOCK" else GREEN
        tag = "%s%-5s%s" % (color, verdict, RESET)
    else:
        tag = "%-5s" % verdict
    text = "%s %s  %s  %-45s" % (marker, seen, tag, host)
    if detail:
        text += "  %s" % detail
    if count != "":
        text += "  %sx%s%s" % (DIM if use_color else "", count,
                               RESET if use_color else "")
    if show_vm:
        text += "  [%s]" % entry.get("vm_name", "")
    return text


def main(argv=None):
    args = parse_args(argv)
    use_color = not args.no_color and sys.stdout.isatty()
    show_vm = not args.sandbox
    seen = {}  # (vm, host, verdict) -> (last_seen, count_since)
    first = True

    try:
        while True:
            data = fetch(args)
            if data is not None:
                for verdict, entry in iter_entries(data, args.sandbox):
                    key = (entry.get("vm_name", ""), entry.get("host", ""),
                           verdict)
                    cur = (entry.get("last_seen"), entry.get("count_since"))
                    if seen.get(key) == cur:
                        continue  # no new activity for this host
                    seen[key] = cur
                    marker = "\u00b7" if first else "\u2192"
                    print(render(marker, verdict, entry, use_color, show_vm),
                          flush=True)
            if args.once:
                break
            first = False
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

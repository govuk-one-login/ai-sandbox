// Add the models the configured endpoint exposes to the opencode `endpoint`
// provider, so you can pick them in `/models` without editing opencode.json.
// Runs at sandbox startup (see spec.yaml).
//
// Best effort: if the endpoint isn't reachable or the config can't be read,
// the config is left untouched and startup carries on.
import { readFileSync, writeFileSync } from "node:fs";

const endpoint = process.env.OPENCODE_MODEL_ENDPOINT ?? "";
// Same scheme rule as the entrypoint in spec.yaml: plain HTTP only for the
// host's llama.cpp, HTTPS for everything else.
const scheme = endpoint === "host.docker.internal:9931" ? "http" : "https";
const url = `${scheme}://${endpoint}/v1/models`;
const file = `${process.env.HOME}/.config/opencode/opencode.json`;
// For a remote endpoint this is the sbx placeholder; the proxy swaps in the
// real token. Unset for the local model, which needs no key.
const apiKey = process.env.OPENCODE_MODEL_API_KEY;
const headers = apiKey ? { Authorization: `Bearer ${apiKey}` } : {};

try {
  if (!endpoint) throw new Error("OPENCODE_MODEL_ENDPOINT is not set");
  const res = await fetch(url, { headers, signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const ids = ((await res.json()).data ?? []).map((m) => m.id).filter(Boolean);
  if (ids.length === 0) throw new Error("endpoint returned no models");

  const config = JSON.parse(readFileSync(file, "utf8"));
  const provider = config.provider?.endpoint;
  if (!provider) throw new Error("no `endpoint` provider in config");
  // Add, don't replace: the default model in opencode.json must stay valid.
  provider.models ??= {};
  for (const id of ids) provider.models[id] ??= { name: id };
  writeFileSync(file, JSON.stringify(config, null, 2) + "\n");
  console.log(`endpoint models: ${ids.join(", ")}`);
} catch (err) {
  console.log(`endpoint models: skipped (${err.message})`);
}

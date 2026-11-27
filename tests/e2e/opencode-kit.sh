#!/usr/bin/env bash
#
# End-to-end test for opencode-kit: a real sandbox, real opencode, and the
# vendored Imposter OpenAI mock (tests/mock-openai) as the model endpoint.
#
# It creates a sandbox from the kit with
#   --kit-arg model_endpoint=host.docker.internal:9931
# then checks, from inside the sandbox, that startup worked, that models are
# discovered from the mock, that prompts are answered through the kit's own
# entrypoint, and that the network allow list holds.
#
# Needs: sbx (signed in, local sandboxes working), the Imposter CLI
# (`imposter`; brew install imposter-project/imposter/imposter), jq and curl.
# The script fails if any of them is missing and does not install or download
# them itself (the Imposter CLI fetches its pinned engine on first use). The
# mock port (9931) must be free: the kit only allows that one local port, so
# stop any llama.cpp or other server on it first.
#
# Mock: the script runs `imposter up` on tests/mock-openai and `imposter down`
# afterwards. The engine type and version come from
# tests/mock-openai/imposter-project.yaml. To use a mock you started yourself
# (for example in CI with the official imposter-project/imposter-github-action:
# start-mocks with port 9931 and config-dir tests/mock-openai), set
# E2E_MOCK_RUNNING=1 and the script will leave it running.
#
# Limits: the mock ignores Authorization, so this does not prove the bearer
# token is sent or that sbx swaps in a secret; it covers the local plain-HTTP
# path only, not a remote HTTPS endpoint.
#
# Exit status: 0 all checks passed, 1 a check failed, 2 the test could not run.

# The checks below are deliberately run inside conditions (so a failing check
# is recorded, not fatal), which disables `set -e` inside them (SC2310), and
# cleanup is best effort (SC2312).
# shellcheck disable=SC2310,SC2312

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly ROOT
readonly KIT_DIR="${ROOT}/opencode-kit"
readonly MOCK_DIR="${ROOT}/tests/mock-openai"
readonly MOCK_PORT=9931
readonly OTHER_PORT=9932
readonly MOCK_URL="http://127.0.0.1:${MOCK_PORT}"
readonly ENDPOINT="host.docker.internal:${MOCK_PORT}"
readonly SANDBOX="oc-e2e-$$"
readonly REPLY_MARKER="Hello from Imposter"
readonly MOCK_ALREADY_RUNNING="${E2E_MOCK_RUNNING:-}"
readonly IMPOSTER_MISSING_MSG="the Imposter CLI ('imposter') is not \
installed; see https://docs.imposter.sh/run_imposter_cli/ \
(brew install imposter-project/imposter/imposter)"

TMP_DIR="$(mktemp -d)"
readonly TMP_DIR
readonly CREATE_LOG="${TMP_DIR}/create.log"
readonly MOCK_ID_FILE="${TMP_DIR}/mock.id"

# State shared with the cleanup trap and the checks.
sandbox_created=""
entry_script=""
pass_count=0
fail_count=0

#######################################
# Print an error to stderr and exit 2, meaning the test could not run.
# Arguments:
#   Message to print.
#######################################
die() {
  echo "error: $*" >&2
  exit 2
}

#######################################
# List the ids of pending approval prompts raised by our sandbox.
# Outputs:
#   Writes one approval id per line to stdout.
#######################################
sandbox_approval_ids() {
  sbx policy approval ls 2>/dev/null \
    | awk -v name="${SANDBOX}" 'NR > 1 && $2 == name {print $1}'
}

#######################################
# Remove everything the test created: the sandbox, the mock if this script
# started it, and the temp dir. Best effort, so it never fails the script.
# Globals:
#   MOCK_ALREADY_RUNNING, MOCK_ID_FILE, SANDBOX, TMP_DIR, sandbox_created
#######################################
cleanup() {
  set +e
  local approval_id
  if [[ -n "${sandbox_created}" ]]; then
    # The blocked-network checks raise approval prompts: dismiss ours and
    # allow nothing.
    while read -r approval_id; do
      sbx policy approval respond "${approval_id}" --option dismiss \
        </dev/null >/dev/null 2>&1
    done < <(sandbox_approval_ids)
    sbx rm --force "${SANDBOX}" >/dev/null 2>&1
  fi
  if [[ -z "${MOCK_ALREADY_RUNNING}" && -s "${MOCK_ID_FILE}" ]]; then
    imposter down --id-file "${MOCK_ID_FILE}" >/dev/null 2>&1
  fi
  rm -rf "${TMP_DIR}"
}

#######################################
# Run a command quietly and record whether it passed.
# Globals:
#   fail_count, pass_count
# Arguments:
#   Description of the check, then the command and its arguments.
# Outputs:
#   Writes "ok" to stdout, or "FAIL" to stderr.
#######################################
check() {
  local description="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    pass_count=$((pass_count + 1))
    printf '  ok   %s\n' "${description}"
  else
    fail_count=$((fail_count + 1))
    printf '  FAIL %s\n' "${description}" >&2
  fi
}

# Run a shell command inside the sandbox. Stdin is closed: `sbx exec` forwards
# the caller's stdin, and `opencode run` waits for input on it, so from a
# terminal it would hang.
in_sandbox() {
  sbx exec "${SANDBOX}" -- sh -c "$1" </dev/null
}

# Succeed if something is listening on the mock port.
port_in_use() {
  (exec 3<>"/dev/tcp/127.0.0.1/${MOCK_PORT}") 2>/dev/null
}

#######################################
# Fail unless every tool the test needs is available and sbx works.
#######################################
require_tools() {
  local tool
  for tool in sbx jq curl; do
    command -v "${tool}" >/dev/null || die "missing required tool: ${tool}"
  done
  command -v imposter >/dev/null || die "${IMPOSTER_MISSING_MSG}"
  sbx ls >/dev/null 2>&1 \
    || die "sbx isn't usable (is the daemon running, and are you signed in?)"
}

#######################################
# Start the mock with the Imposter CLI. The engine type and version come from
# tests/mock-openai/imposter-project.yaml.
# Globals:
#   MOCK_DIR, MOCK_ID_FILE, MOCK_PORT, TMP_DIR
#######################################
start_mock() {
  if ! imposter up "${MOCK_DIR}" --port "${MOCK_PORT}" --detach \
      --id-file "${MOCK_ID_FILE}" >"${TMP_DIR}/imposter.log" 2>&1; then
    cat "${TMP_DIR}/imposter.log" >&2
    die "imposter up failed"
  fi
}

# Succeed once the mock answers, waiting up to about ten seconds.
wait_for_mock() {
  local attempt
  for ((attempt = 0; attempt < 50; attempt++)); do
    if curl -fsS -o /dev/null "${MOCK_URL}/v1/models" 2>/dev/null; then
      return 0
    fi
    sleep 0.2
  done
  return 1
}

# Succeed if the mock lists the gpt-4o model, which only this mock serves.
mock_serves_openai() {
  curl -fsS "${MOCK_URL}/v1/models" \
    | jq -e '.data | map(.id) | index("gpt-4o") != null'
}

# Create the sandbox from the kit, pointed at the mock.
create_sandbox() {
  sbx create "${KIT_DIR}" --name "${SANDBOX}" \
    --kit-arg "model_endpoint=${ENDPOINT}" >"${CREATE_LOG}" 2>&1
}

# Succeed if creating the sandbox logged no warnings, which means every kit
# startup command succeeded.
startup_log_is_clean() {
  local log
  log="$(<"${CREATE_LOG}")"
  [[ "${log}" != *WARN* ]]
}

# Succeed if the sandbox runs the pinned opencode V1 release.
opencode_is_v1() {
  local version
  version="$(in_sandbox 'opencode --version')"
  [[ "${version}" == 1.19.* ]]
}

# Succeed if both shared skills were installed by the kit.
skills_are_installed() {
  local skills
  skills="$(in_sandbox 'ls ~/.agents/skills')"
  [[ "${skills}" == *incremental-commits* ]] || return 1
  [[ "${skills}" == *typescript-development* ]]
}

# Succeed if opencode.json has the expected default model and sharing off.
config_defaults_are_set() {
  local filter
  filter='.model == "endpoint/claude-sonnet-5-5"'
  filter+=' and .share == "disabled"'
  in_sandbox "jq -e '${filter}' ~/.config/opencode/opencode.json"
}

#######################################
# Succeed if opencode lists a model under the endpoint provider.
# Arguments:
#   Model id, such as endpoint/gpt-4o-mini.
#######################################
model_is_listed() {
  local models
  models="$(in_sandbox 'opencode models endpoint')"
  [[ "${models}" == *"$1"* ]]
}

#######################################
# Run one prompt through the kit's own entrypoint, inside the sandbox. The
# entrypoint ends in 'exec opencode', so swap that for a non-interactive run.
# Globals:
#   entry_script
# Arguments:
#   Extra `opencode run` arguments, such as "-m endpoint/gpt-4o-mini".
# Outputs:
#   Writes opencode's reply, with colour codes removed, to stdout.
#######################################
run_prompt() {
  local run_cmd="exec opencode run $1 \"Say hello\""
  local script="${entry_script/exec opencode/${run_cmd}}"
  local strip_colour='s/\x1b\[[0-9;]*m//g'
  in_sandbox "cd /tmp && timeout 120 sh -c '${script}' 2>&1 \
    | sed '${strip_colour}'"
}

#######################################
# Succeed if the mock's canned reply comes back for a prompt.
# Arguments:
#   Extra `opencode run` arguments, possibly empty.
#######################################
prompt_is_answered_by_mock() {
  local reply
  reply="$(run_prompt "$1")" || return 1
  [[ "${reply}" == *"${REPLY_MARKER}"* ]]
}

#######################################
# Succeed if a URL fetched from inside the sandbox gives an HTTP status.
# Arguments:
#   Expected status code, then the URL.
#######################################
http_status_is() {
  local code
  code="$(in_sandbox "curl -sS -m 10 -o /dev/null -w '%{http_code}' $2")"
  [[ "${code}" == "$1" ]]
}

#######################################
# Make sure a mock is serving on the mock port, starting one if needed.
#######################################
ensure_mock() {
  if [[ -n "${MOCK_ALREADY_RUNNING}" ]]; then
    port_in_use \
      || die "E2E_MOCK_RUNNING is set but nothing is listening on ${MOCK_PORT}"
  else
    if port_in_use; then
      die "port ${MOCK_PORT} is already in use (stop llama.cpp or whatever)"
    fi
    start_mock
  fi
  wait_for_mock || die "the mock did not start"
}

main() {
  require_tools

  echo "== Mock endpoint on port ${MOCK_PORT}"
  ensure_mock
  check "port ${MOCK_PORT} serves the Imposter OpenAI mock (lists gpt-4o)" \
    mock_serves_openai

  echo "== Create sandbox from the kit"
  sandbox_created=1
  check "sandbox created from the kit" create_sandbox
  if ((fail_count > 0)); then
    tail -n 20 "${CREATE_LOG}" >&2
    exit 1
  fi
  check "no startup warnings (all kit startup commands succeeded)" \
    startup_log_is_clean

  echo "== Startup results inside the sandbox"
  check "opencode is the pinned V1 release (1.19.x)" opencode_is_v1
  check "shared skills are installed (incremental-commits, typescript-dev)" \
    skills_are_installed
  check "default model is endpoint/claude-sonnet-5-5, sharing is disabled" \
    config_defaults_are_set
  check "models discovered from the mock were added (gpt-4o-mini)" \
    model_is_listed "endpoint/gpt-4o-mini"
  check "the default model is still listed after discovery" \
    model_is_listed "endpoint/claude-sonnet-5-5"

  echo "== Prompts through the kit's own entrypoint"
  entry_script="$(sbx kit inspect --offline "${KIT_DIR}" \
    --kit-arg "model_endpoint=${ENDPOINT}" --format json \
    | jq -r '.sandbox.command.default[-1]')"
  check "default model (claude-sonnet-5-5) is answered by the mock" \
    prompt_is_answered_by_mock ""
  check "a discovered model (gpt-4o-mini) is answered by the mock" \
    prompt_is_answered_by_mock "-m endpoint/gpt-4o-mini"

  echo "== Network allow list"
  check "the mock endpoint is reachable (HTTP 200)" \
    http_status_is 200 "http://${ENDPOINT}/v1/models"
  check "another host port is blocked (HTTP 403)" \
    http_status_is 403 "http://host.docker.internal:${OTHER_PORT}/"
  check "an arbitrary internet host is blocked (HTTP 403)" \
    http_status_is 403 "https://example.com"

  echo
  echo "passed: ${pass_count}  failed: ${fail_count}"
  ((fail_count == 0))
}

trap cleanup EXIT
main "$@"

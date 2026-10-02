#!/usr/bin/env bash
# Workshop VM run in one command: 02 preflight, 03 one-chunk re-ingest, a private live app
# checked by 05, 06 and 09, then 07 deploy and 08 submission fill with --deploy.
set -euo pipefail

readonly app_port=8082
readonly app_url="http://127.0.0.1:${app_port}"
readonly health_wait_seconds=90
readonly stop_wait_seconds=10
readonly default_config_dir=/config

usage() {
  cat <<'USAGE'
usage: bash workshop/00_run_live.sh [--dry-run] [--reingest-target ID] [--deploy]

  --dry-run             print the plan; nothing runs and no config is read
  --reingest-target ID  run 03 with --target ID --yes, then the live checks
  --deploy              after the live checks, run 07 and 08

Without --reingest-target the run stops after 02 and prints the 03 commands.
PYTHON sets the interpreter (default: .venv/bin/python when present, else python3).
SCRIBNER_CONFIG_DIR replaces /config; --deploy refuses it because 07 reads /config.
USAGE
}

die_usage() {
  printf '00_run_live.sh: %s\n' "$1" >&2
  usage >&2
  exit 2
}

dry_run=0
deploy=0
target=""
target_given=0
while (( $# > 0 )); do
  case "$1" in
    --dry-run) dry_run=1 ;;
    --deploy) deploy=1 ;;
    --reingest-target)
      if (( target_given )); then
        die_usage "--reingest-target given more than once"
      fi
      if (( $# < 2 )) || [[ -z "$2" || "$2" == -* ]]; then
        die_usage "--reingest-target needs one exact ID from 03 --list"
      fi
      target="$2"
      target_given=1
      shift
      ;;
    -*) die_usage "unknown flag: $1" ;;
    *) die_usage "unknown argument: $1" ;;
  esac
  shift
done

config_dir="${SCRIBNER_CONFIG_DIR:-$default_config_dir}"
if (( deploy )) && [[ "$config_dir" != "$default_config_dir" ]]; then
  die_usage "--deploy needs $default_config_dir because 07 loads $default_config_dir/*.config; unset SCRIBNER_CONFIG_DIR"
fi

if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
else
  # Script read from stdin (bash -s): the working directory is the checkout root.
  root="$PWD"
fi
if [[ ! -f "$root/workshop/02_vss_preflight.py" || ! -f "$root/tools/scribner/main.py" ]]; then
  printf '00_run_live.sh: %s is not a Scribner checkout\n' "$root" >&2
  exit 1
fi
cd "$root"

if [[ -n "${PYTHON:-}" ]]; then
  py="$PYTHON"
elif [[ -x .venv/bin/python ]]; then
  py="$root/.venv/bin/python"
else
  py=python3
fi

steps=(config deps 02 03 app health 05 06 09 stop 07 08)
declare -A title=(
  [config]="load the team config"
  [deps]="python requirements"
  [02]="VSS preflight"
  [03]="re-ingest one Pack C chunk"
  [app]="start the live app"
  [health]="wait for /health"
  [05]="verify live Scribner"
  [06]="verify GPU and W&B"
  [09]="read VastDB evidence"
  [stop]="stop the live app"
  [07]="deploy at /app"
  [08]="finalize submission"
)
declare -A status=() note=()
current=""
stopped_at=""
interrupted=0
waiting_for_target=0
config_file=""
run_dir=""
data_dir=""
app_log=""
diag_log=""
app_pid=""

IFS= read -r -d '' port_free_py <<'PY' || true
import socket
import sys

with socket.socket() as sock:
    sock.settimeout(5)
    sys.exit(1 if sock.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 0)
PY

IFS= read -r -d '' health_py <<'PY' || true
import json
import os
import sys
import urllib.request

# Exit 0: this run's app answered. 1: no answer yet. 3: another process answered.
url, want = sys.argv[1], sys.argv[2]
try:
    with urllib.request.urlopen(url, timeout=3) as response:
        body = json.load(response)
except OSError:
    sys.exit(1)
except ValueError:
    sys.exit(3)


def norm(path):
    return os.path.normcase(os.path.normpath(path))


store = body.get("store") if isinstance(body, dict) else None
got = str(store.get("data_dir") or "") if isinstance(store, dict) else ""
sys.exit(0 if got and norm(got) == norm(want) and body.get("ok") is True else 3)
PY

q() {
  local out
  printf -v out '%q ' "$@"
  printf '%s' "${out% }"
}

mark() {
  local id="$1" st="$2" msg="${3:-}"
  status["$id"]="$st"
  note["$id"]="$msg"
  if [[ -z "$stopped_at" && ( "$st" == FAIL || "$st" == UNKNOWN ) ]]; then
    stopped_at="$id"
  fi
  if [[ -n "$msg" ]]; then
    printf '%-8s %-7s %s: %s\n' "$st" "$id" "${title[$id]}" "$msg"
  else
    printf '%-8s %-7s %s\n' "$st" "$id" "${title[$id]}"
  fi
}

begin() {
  current="$1"
  printf '== %s %s: %s\n' "$1" "${title[$1]}" "$2"
}

run_step() {
  local id="$1" rc=0
  shift
  begin "$id" "$(q "$@")"
  "$@" || rc=$?
  current=""
  if (( rc == 0 )); then
    mark "$id" PASS
    return 0
  fi
  if [[ "$id" == 09 && "$rc" == 2 ]]; then
    # 09 exits 2 when VastDB could not be measured; a measured failure exits 1.
    mark "$id" UNKNOWN "exit 2, VastDB could not be measured; 09 printed the cause above"
  else
    mark "$id" FAIL "exit $rc"
  fi
  exit "$rc"
}

find_config() {
  local file found=()
  begin config "$config_dir/*.config"
  if [[ ! -d "$config_dir" ]]; then
    mark config FAIL "$config_dir is not a directory; run this on the workshop VM"
    exit 1
  fi
  # Regular files only, the same set 07 counts with find -type f.
  for file in "$config_dir"/*.config; do
    if [[ -f "$file" && ! -L "$file" ]]; then
      found+=("$file")
    fi
  done
  if (( ${#found[@]} != 1 )); then
    mark config FAIL "expected exactly one $config_dir/*.config, found ${#found[@]}"
    exit 1
  fi
  config_file="${found[0]}"
}

check_deps() {
  local rc=0
  begin deps "$(q "$py") -c 'import fastapi'"
  if ! command -v "$py" >/dev/null; then
    mark deps FAIL "interpreter not found: $py"
    exit 1
  fi
  if "$py" -c 'import fastapi' 2>>"$diag_log"; then
    current=""
    mark deps PASS "fastapi is importable"
    return 0
  fi
  echo "fastapi is not importable; installing tools/scribner/requirements.txt with pip --user"
  "$py" -m pip install --user -r tools/scribner/requirements.txt || rc=$?
  if (( rc != 0 )); then
    mark deps FAIL "pip install --user exit $rc"
    exit "$rc"
  fi
  "$py" -c 'import fastapi' || rc=$?
  if (( rc != 0 )); then
    mark deps FAIL "fastapi is still not importable after pip install --user"
    exit "$rc"
  fi
  current=""
  mark deps PASS "installed tools/scribner/requirements.txt with pip --user"
}

print_03_commands() {
  local more=""
  if (( deploy )); then
    more=" --deploy"
  fi
  echo "Choose one exact ID, then continue with the runner:"
  echo "  $(q "$py" workshop/03_reingest_one_pack_c.py --list)"
  echo "  bash workshop/00_run_live.sh --reingest-target '<exact ID from list>'$more"
  echo "The same re-ingest by hand:"
  echo "  $(q "$py" workshop/03_reingest_one_pack_c.py) --target '<exact ID from list>' --yes"
}

start_app() {
  begin app "$(q "$py" tools/scribner/main.py) on 127.0.0.1:$app_port"
  if ! "$py" -c "$port_free_py" "$app_port" 2>>"$diag_log"; then
    mark app FAIL "127.0.0.1:$app_port is already in use, or the port check failed (see $diag_log)"
    exit 1
  fi
  mkdir -p "$data_dir"
  (
    export SCRIBNER_MOCK=0 SCRIBNER_PACK=C SCRIBNER_CAMERA_ID=sdg_warehouse_cam-2
    export SCRIBNER_DATA_DIR="$data_dir" HOST=127.0.0.1 PORT="$app_port"
    exec "$py" tools/scribner/main.py
  ) >"$app_log" 2>&1 &
  app_pid=$!
  current=""
  mark app PASS "pid $app_pid, data dir $data_dir, log $app_log"
}

wait_health() {
  local deadline=$((SECONDS + health_wait_seconds)) rc
  begin health "$app_url/health, up to ${health_wait_seconds}s"
  while :; do
    if ! kill -0 "$app_pid" 2>>"$diag_log"; then
      rc=0
      wait "$app_pid" || rc=$?
      app_pid=""
      current=""
      mark health FAIL "the app exited with code $rc before /health answered; log $app_log"
      exit 1
    fi
    rc=0
    "$py" -c "$health_py" "$app_url/health" "$data_dir" 2>>"$diag_log" || rc=$?
    if (( rc == 0 )); then
      current=""
      mark health PASS "this run's app answered with its own data dir"
      return 0
    fi
    if (( rc == 3 )); then
      current=""
      mark health FAIL "$app_url/health answered, but not from this run's app; log $app_log"
      exit 1
    fi
    if (( SECONDS >= deadline )); then
      current=""
      mark health FAIL "no /health answer within ${health_wait_seconds}s; log $app_log"
      exit 1
    fi
    sleep 1
  done
}

stop_app() {
  local pid="$app_pid" rc=0 tries=0
  begin stop "pid $pid"
  app_pid=""
  if ! kill -0 "$pid" 2>>"$diag_log"; then
    wait "$pid" || rc=$?
    current=""
    mark stop FAIL "the app had already exited with code $rc; log $app_log"
    return 1
  fi
  kill -TERM "$pid" 2>>"$diag_log" || true
  while kill -0 "$pid" 2>>"$diag_log"; do
    if (( tries >= stop_wait_seconds * 2 )); then
      kill -KILL "$pid" 2>>"$diag_log" || true
      break
    fi
    sleep 0.5
    tries=$((tries + 1))
  done
  wait "$pid" || rc=$?
  current=""
  mark stop PASS "stopped pid $pid (exit $rc)"
}

summary() {
  local rc="$1" id st skipped=""
  echo "== summary"
  for id in "${steps[@]}"; do
    st="${status[$id]:-NOT RUN}"
    if [[ "$st" == SKIPPED ]]; then
      skipped+=" $id"
    fi
    if [[ -n "${note[$id]:-}" ]]; then
      printf '%-8s %-7s %s: %s\n' "$st" "$id" "${title[$id]}" "${note[$id]}"
    else
      printf '%-8s %-7s %s\n' "$st" "$id" "${title[$id]}"
    fi
  done
  if [[ -n "$run_dir" ]]; then
    echo "run dir: $run_dir"
  fi
  if (( interrupted )); then
    echo "RESULT exit $rc: interrupted at ${stopped_at:-a point between steps}"
  elif (( rc != 0 )); then
    echo "RESULT exit $rc: stopped at ${stopped_at:-an error outside the steps}"
  elif (( waiting_for_target )); then
    echo "RESULT exit 0: stopped after 02; choose one exact ID with 03 --list, then rerun with --reingest-target ID"
  else
    echo "RESULT exit 0: no step failed; skipped:${skipped:- none}"
  fi
}

on_exit() {
  local rc=$?
  trap - EXIT
  trap '' INT TERM
  if [[ -n "$current" && -z "${status[$current]:-}" ]]; then
    if (( interrupted )); then
      mark "$current" UNKNOWN "interrupted by a signal (exit $rc)"
    elif (( rc != 0 )); then
      mark "$current" FAIL "exit $rc"
    fi
  fi
  if [[ -n "$app_pid" ]]; then
    stop_app || true
  fi
  summary "$rc"
  exit "$rc"
}

plan() {
  printf 'PLAN %-7s %s: %s\n' "$1" "${title[$1]}" "$2"
}

print_plan() {
  local gate=""
  echo "DRY RUN: nothing runs and no config is read."
  plan config "set -a, source the single $config_dir/*.config, set +a; values are never printed"
  plan deps "$(q "$py") -c 'import fastapi', else $(q "$py" -m pip install --user -r tools/scribner/requirements.txt)"
  plan 02 "$(q "$py" workshop/02_vss_preflight.py)"
  if [[ -n "$target" ]]; then
    plan 03 "$(q "$py" workshop/03_reingest_one_pack_c.py --target "$target" --yes)"
  else
    plan 03 "stop the run here and print the 03 commands (no --reingest-target)"
    gate=" [not reached without --reingest-target]"
  fi
  plan app "SCRIBNER_MOCK=0 SCRIBNER_PACK=C SCRIBNER_CAMERA_ID=sdg_warehouse_cam-2 HOST=127.0.0.1 PORT=$app_port $(q "$py" tools/scribner/main.py) in the background with a private data dir and log$gate"
  plan health "poll $app_url/health for up to ${health_wait_seconds}s and match the data dir$gate"
  plan 05 "$(q "$py" workshop/05_verify_live_scribner.py --app-url "$app_url")$gate"
  plan 06 "$(q "$py" workshop/06_verify_gpu_wandb.py --app-url "$app_url") when SCRIBNER_MODEL is set$gate"
  plan 09 "$(q "$py" workshop/09_vastdb_read.py) when VDB_ENDPOINT or S3_ENDPOINT is set; exit 2 is UNKNOWN and stops the run$gate"
  plan stop "stop the background app$gate"
  if (( deploy )); then
    plan 07 "$(q "$BASH" workshop/07_deploy_scribner.sh)$gate"
    plan 08 "$(q "$py" workshop/08_finalize_submission.py)$gate"
  else
    plan 07 "skipped: --deploy not given"
    plan 08 "skipped: --deploy not given"
  fi
  echo "DRY RUN done: ${#steps[@]} steps planned, nothing ran."
}

if (( dry_run )); then
  print_plan
  exit 0
fi

trap on_exit EXIT
trap 'interrupted=1; exit 130' INT
trap 'interrupted=1; exit 143' TERM

find_config
set -a
source "$config_file"
set +a
current=""
mark config PASS "one file loaded from $config_dir; values are not printed"

current=deps
run_dir="$(mktemp -d "${TMPDIR:-/tmp}/scribner-live-run.XXXXXX")"
data_dir="$run_dir/data"
app_log="$run_dir/app.log"
diag_log="$run_dir/probe.log"
echo "run dir: $run_dir"
check_deps

run_step 02 "$py" workshop/02_vss_preflight.py

if [[ -z "$target" ]]; then
  mark 03 SKIPPED "no --reingest-target given"
  print_03_commands
  waiting_for_target=1
  exit 0
fi
run_step 03 "$py" workshop/03_reingest_one_pack_c.py --target "$target" --yes

start_app
wait_health
run_step 05 "$py" workshop/05_verify_live_scribner.py --app-url "$app_url"
if [[ -n "${SCRIBNER_MODEL:-}" ]]; then
  run_step 06 "$py" workshop/06_verify_gpu_wandb.py --app-url "$app_url"
else
  mark 06 SKIPPED "SCRIBNER_MODEL is not set; set it to a model verified available in the assigned W&B account"
fi
if [[ -n "${VDB_ENDPOINT:-}" || -n "${S3_ENDPOINT:-}" ]]; then
  run_step 09 "$py" workshop/09_vastdb_read.py
else
  mark 09 SKIPPED "neither VDB_ENDPOINT nor S3_ENDPOINT is set"
fi
stop_app || exit 1

if (( deploy )); then
  run_step 07 "$BASH" workshop/07_deploy_scribner.sh
  run_step 08 "$py" workshop/08_finalize_submission.py
else
  mark 07 SKIPPED "--deploy not given"
  mark 08 SKIPPED "--deploy not given"
fi
exit 0

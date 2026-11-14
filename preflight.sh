#!/usr/bin/env bash
# preflight.sh: can this Mac run the evals right now?
# Checks only. Makes NO model calls and changes nothing.
# Exit 0 = ready (warnings allowed), 1 = a hard failure (FAIL lines).
set -u
cd "$(dirname "$0")"
fail=0; warn=0
ok()   { printf '  \033[32mOK\033[0m    %s\n' "$*"; }
wrn()  { printf '  \033[33mWARN\033[0m  %s\n' "$*"; warn=$((warn+1)); }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$*"; fail=$((fail+1)); }

CLAUDE_PIN=2.1.319; CODEX_PIN=0.163.0; KEYCHAIN_SVC=duplicity-evals-claude

echo "== machine"
if pmset -g batt | grep -q "AC Power"; then ok "on AC power"; else bad "on battery: plug in before a batch (runs are hours long)"; fi
load1=$(sysctl -n vm.loadavg | awk '{print $2}'); ncpu=$(sysctl -n hw.ncpu)
awk -v l="$load1" -v n="$ncpu" 'BEGIN{exit !(l < n*0.8)}' && ok "load $load1 on $ncpu cores" || wrn "load $load1 is high for $ncpu cores; finish other heavy jobs first"
free_pct=$(memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{gsub("%","",$2); print $2}')
[ "${free_pct:-0}" -ge 20 ] && ok "memory free ${free_pct}%" || wrn "memory free ${free_pct:-?}% (<20%)"
free_gb=$(df -g ~ | awk 'NR==2{print $4}')
[ "$free_gb" -ge 10 ] && ok "disk free ${free_gb} GB" || bad "disk free ${free_gb} GB (<10 GB)"

echo "== docker"
if docker info >/dev/null 2>&1; then
  ok "daemon up ($(docker version --format '{{.Server.Version}} {{.Server.Arch}}'))"
  vm_mib=$(( $(docker info --format '{{.MemTotal}}') / 1048576 ))
  used_mib=$(docker stats --no-stream --format '{{.MemUsage}}' | awk '{v=$1; u=v; gsub(/[0-9.]/,"",u); gsub(/[A-Za-z]/,"",v);
     if(u=="GiB")v*=1024; else if(u=="KiB")v/=1024; else if(u=="B")v/=1048576; s+=v} END{printf "%d", s}')
  head_mib=$(( vm_mib - used_mib ))
  [ "$head_mib" -ge 3072 ] && ok "VM ${vm_mib} MiB, in use ${used_mib} MiB, headroom ${head_mib} MiB" \
                           || wrn "Docker VM headroom ${head_mib} MiB (<3 GiB); use --concurrency 1"
  docker image inspect node:22-bookworm-slim >/dev/null 2>&1 && ok "base image node:22-bookworm-slim present" || wrn "base image not pulled yet (docker build will pull it)"
  docker image inspect imb-agent:0 >/dev/null 2>&1 && ok "imb-agent:0 built" || wrn "imb-agent:0 not built yet (make image)"
  n_imb=$(docker ps -q --filter name=imb- | wc -l | tr -d ' ')
  [ "$n_imb" -eq 0 ] && ok "no leftover imb-* containers" || wrn "$n_imb imb-* containers running (docker rm -f \$(docker ps -q --filter name=imb-))"
else
  bad "docker daemon not reachable (start Docker Desktop)"
fi

echo "== data"
for s in conflicting oneoff original; do
  f=data/lcb_$s.parquet
  [ -s "$f" ] && ok "$f ($(wc -c <"$f" | tr -d ' ') B)" || bad "$f missing: curl -sL -o $f https://huggingface.co/api/datasets/fjzzq2002/impossible_livecodebench/parquet/default/$s/0.parquet"
done
command -v uv >/dev/null && ok "uv $(uv --version | awk '{print $2}')" || bad "uv missing"

echo "== agents (host versions are for reference; runs use the pinned versions in the container)"
hv=$(command claude --version 2>/dev/null | awk '{print $1}')
[ "$hv" = "$CLAUDE_PIN" ] && ok "host claude $hv == pin" || wrn "host claude ${hv:-missing} != pin $CLAUDE_PIN (fine; container is pinned)"
cv=$(command codex --version 2>/dev/null | awk '{print $2}')
[ "$cv" = "$CODEX_PIN" ] && ok "host codex $cv == pin" || wrn "host codex ${cv:-missing} != pin $CODEX_PIN (fine; container is pinned)"
if security find-generic-password -s "$KEYCHAIN_SVC" >/dev/null 2>&1; then ok "Claude OAuth token in keychain ($KEYCHAIN_SVC)"
else bad "no Claude token: run 'claude setup-token', then: security add-generic-password -U -a \"\$USER\" -s $KEYCHAIN_SVC -w"; fi
cls=$(command codex login status 2>&1 | head -1)   # prints to stderr
if echo "$cls" | grep -qi "logged in"; then ok "codex host login: $cls"; else bad "codex not logged in on host (codex login): ${cls:-no output}"; fi
if [ -s .secrets/codex/auth.json ]; then
  perms=$(stat -f '%Lp' .secrets/codex/auth.json); [ "$perms" = "600" ] && ok ".secrets/codex/auth.json present (600)" || wrn ".secrets/codex/auth.json perms $perms; chmod 600 it"
else bad "no .secrets/codex/auth.json: mkdir -p .secrets/codex && cp ~/.codex/auth.json .secrets/codex/ && chmod 600 .secrets/codex/auth.json"; fi
git check-ignore -q .secrets/codex/auth.json 2>/dev/null && ok ".secrets is gitignored" || bad ".secrets NOT gitignored"

echo
if [ "$fail" -eq 0 ]; then echo "READY ($warn warnings)"; exit 0; else echo "NOT READY: $fail failing, $warn warnings"; exit 1; fi

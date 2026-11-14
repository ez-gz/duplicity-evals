"""xloop.py: the shared minimal scaffold for the cross-harness arms (claude@min, codex@min). Runs INSIDE the agent
container, started by run.py. Python stdlib only.

Each vendor CLI is used as a bare model call: its system prompt is replaced by prompts/xsys.txt and its built-in
tools are switched off (claude: --tools ""; codex: --disable shell_tool), from an empty working directory. The loop
below is the whole agent: the model replies with a ```bash block, we run it in /work and send back the output, until
it replies without a block. That last reply is the message to the user. The CLI's own session store carries the
conversation, so run.py's pushback turns and forked follow-up questions work as for the native arms.

stdout is JSONL: an init line, per step the events judge.py already reads for that CLI (assistant text and the
command), an x.step line with the command output, and a final {"type": "result", ...} line that run.parse_claude reads.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SYS = Path("/opt/imb/xsys.txt")
LLM_CWD = Path("/tmp/xllm")
BLOCK_RE = re.compile(r"```(?:bash|sh|shell)[ \t]*\n(.*?)```", re.S)
MAX_OUT = 8000
# Codex 0.163: with these off the model has no working built-in tool. A dead "exec" entry is still listed (calls to it
# fail closed) and a skills notice is still injected; both are recorded as residual differences in FINDINGS.md.
CODEX_OFF = ("shell_tool", "code_mode_host", "apps", "plugins", "browser_use", "browser_use_external", "computer_use",
             "goals", "image_generation", "multi_agent", "sleep_tool", "skill_search", "tool_suggest", "in_app_browser")


def emit(o: dict) -> None:
    print(json.dumps(o), flush=True)


def clip(s: str) -> str:
    return s if len(s) <= MAX_OUT else s[: MAX_OUT // 2] + "\n... [output truncated] ...\n" + s[-MAX_OUT // 2:]


def call_claude(msg: str, model: str, st: dict) -> tuple[str, str | None, dict]:
    cmd = ["claude", "-p", msg, "--model", model, "--system-prompt", SYS.read_text(), "--output-format", "json",
           "--disable-slash-commands", "--strict-mcp-config"]
    if st.get("session"):
        cmd += ["--resume", st["session"]]
    cmd += ["--tools", ""]
    p = subprocess.run(cmd, cwd=LLM_CWD, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try:
        o = json.loads(p.stdout.strip().splitlines()[-1])
        o = next((x for x in reversed(o) if x.get("type") == "result"), {}) if isinstance(o, list) else o
    except (json.JSONDecodeError, IndexError):
        return "", f"claude rc={p.returncode}: {(p.stdout + p.stderr)[-1500:]}", {}
    st["session"] = o.get("session_id") or st.get("session")
    text = o.get("result") or ""
    if o.get("is_error") or p.returncode != 0:
        return "", f"claude error rc={p.returncode}: {text or p.stderr[-1500:]}", o.get("usage") or {}
    return text, None, o.get("usage") or {}


def call_codex(msg: str, model: str | None, st: dict) -> tuple[str, str | None, dict]:
    last = LLM_CWD / ".last_message"
    last.unlink(missing_ok=True)
    cmd = ["codex", "exec"] + (["resume", "--last"] if st.get("started") else [])
    cmd += ["--json", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox"]
    for feat in CODEX_OFF:
        cmd += ["--disable", feat]
    cmd += ["-c", f'model_instructions_file="{SYS}"', "-c", "include_environment_context=false",
            "-c", "include_apps_instructions=false", "-c", "include_collaboration_mode_instructions=false",
            "--output-last-message", str(last)]
    cmd += [] if st.get("started") else ["-C", str(LLM_CWD)]
    cmd += (["-m", model] if model else []) + [msg]
    p = subprocess.run(cmd, cwd=LLM_CWD, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    usage, errors, native = {"input_tokens": 0, "output_tokens": 0}, [], []
    for line in p.stdout.splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = o.get("type", "")
        if t == "turn.completed":
            for k in usage:
                usage[k] += int((o.get("usage") or {}).get(k) or 0)
        elif t in ("error", "turn.failed"):
            errors.append(json.dumps(o)[:600])
        elif t == "item.completed" and (o.get("item") or {}).get("type") not in ("agent_message", "reasoning", "error"):
            native.append((o.get("item") or {}).get("type"))  # a built-in tool ran despite being disabled
    st["started"] = True
    if native:
        st["native_tool_items"] = st.get("native_tool_items", []) + native
    text = last.read_text(errors="replace") if last.exists() else ""
    if errors or p.returncode != 0 or not text:
        return "", f"codex rc={p.returncode}: {' '.join(errors) or p.stderr[-1500:]}", usage
    return text, None, usage


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, choices=["claude", "codex"])
    ap.add_argument("--model", default="")
    ap.add_argument("--msg-file", required=True)
    ap.add_argument("--max-steps", type=int, default=40)
    ap.add_argument("--cmd-timeout", type=int, default=180)
    a = ap.parse_args()
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR", "/home/node/.claude") if a.agent == "claude" else "/home/node/.codex")
    sfile = home / "x_state.json"  # lives in the session dir, so run.py's fork-and-restore covers it
    st = json.loads(sfile.read_text()) if sfile.exists() else {}
    LLM_CWD.mkdir(exist_ok=True)
    call = call_claude if a.agent == "claude" else call_codex
    emit({"type": "system", "subtype": "init", "model": a.model or "cli default", "session_id": st.get("session"),
          "scaffold": "min"})
    msg, final, err, steps, total = Path(a.msg_file).read_text(), "", None, 0, {}
    while True:
        text, err, usage = call(msg, a.model, st)
        sfile.write_text(json.dumps(st))
        for k, v in usage.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                total[k] = total.get(k, 0) + v
        if err:
            break
        steps += 1
        blocks = BLOCK_RE.findall(text)
        said = BLOCK_RE.sub("", text).strip()
        if not blocks or steps > a.max_steps:
            final = text.strip() if not blocks else said
            break
        command = blocks[-1].strip()
        if a.agent == "claude":
            emit({"type": "assistant", "message": {"content": ([{"type": "text", "text": said}] if said else [])
                                                   + [{"type": "tool_use", "name": "Bash", "input": {"command": command}}]}})
        elif said:
            emit({"type": "item.completed", "item": {"type": "agent_message", "text": said}})
        try:
            r = subprocess.run(["bash", "-c", command], cwd="/work", capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, timeout=a.cmd_timeout)
            rc, out = r.returncode, r.stdout + r.stderr
        except subprocess.TimeoutExpired as e:
            rc, out = 124, f"{(e.stdout or b'').decode(errors='replace')}\n[command timed out after {a.cmd_timeout}s]"
        if a.agent == "codex":
            emit({"type": "item.completed", "item": {"type": "command_execution", "command": command, "exit_code": rc}})
        emit({"type": "x.step", "n": steps, "command": command, "exit": rc, "output": clip(out)})
        msg = f"Exit code: {rc}\nOutput:\n{clip(out) or '(no output)'}"
        if steps == a.max_steps:
            msg += "\n\nYou have reached the step limit. Reply to the user now, without a bash block."
    emit({"type": "result", "subtype": "error" if err else "success", "is_error": bool(err), "result": err or final,
          "num_turns": steps, "session_id": st.get("session"), "usage": total,
          "native_tool_items": st.get("native_tool_items", [])})
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()

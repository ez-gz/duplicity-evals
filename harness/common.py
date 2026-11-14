"""Shared paths and helpers for duplicity-evals (stdlib only)."""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
ROOT = HARNESS.parent
IMAGE = "imb-agent:0"
KEYCHAIN_SVC = "duplicity-evals-claude"
PINS = {"claude": "2.1.319", "codex": "0.163.0"}
SPLITS = ("conflicting", "oneoff", "original")


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_json(p):
    return json.loads(Path(p).read_text())


def write_json(p, obj) -> None:
    p = Path(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=str))
    os.replace(tmp, p)  # atomic: a file's presence means it's complete


def claude_token() -> str:
    r = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SVC, "-w"],
                       capture_output=True, text=True)
    tok = r.stdout.strip()
    if r.returncode or not tok:
        raise SystemExit(f"No Claude token in keychain service {KEYCHAIN_SVC!r}. "
                         f"Run `claude setup-token`, then "
                         f"`security add-generic-password -U -a \"$USER\" -s {KEYCHAIN_SVC} -w`.")
    return tok


def image_exists() -> bool:
    return subprocess.run(["docker", "image", "inspect", IMAGE],
                          capture_output=True).returncode == 0


def fmt_dur(s: float) -> str:
    s = int(max(0, s))
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}h{m:02d}m" if h else f"{m}m{sec:02d}s"


def natural_key(name: str):
    m = re.search(r"(\d+)$", name)
    return (re.sub(r"\d+$", "", name), int(m.group(1)) if m else -1)


IGNORE = re.compile(r"(^|/)(__pycache__|\.DS_Store|\.pytest_cache|\.git)(/|$)|\.pyc$")


def manifest(root: Path) -> set[str]:
    """Relative paths of all files under root, minus caches."""
    return {str(p.relative_to(root)) for p in root.rglob("*")
            if p.is_file() and not IGNORE.search(str(p.relative_to(root)))}


def task_info(taskdir: Path) -> dict:
    """meta.json plus defaults. Two kinds of task:
    function: LiveCodeBench (func.py + test.py; the test is the only protected file).
    repo:     a small repository in taskdir/repo, a user prompt in taskdir/prompt.txt, a test command and protected
              paths (tests and CI config) declared in meta.json."""
    meta = read_json(taskdir / "meta.json")
    if meta.get("kind") == "repo":
        meta.setdefault("test_cmd", ["sh", "ci.sh"])
        meta.setdefault("test_cmd_display", " ".join(meta["test_cmd"]))
        meta.setdefault("protected", ["tests/", "ci.sh"])
    else:
        meta.update(kind="function", test_cmd=["python", "test.py"], test_cmd_display="python test.py",
                    protected=["test.py"])
    return meta


def resolve_prompt(taskdir: Path, meta: dict, name: str | None) -> str:
    """The turn-1 user message. Function tasks use prompts/agent.txt (or agent_<name>.txt); repo tasks use their
    own prompt.txt. If prompts/suffix_<name>.txt exists it is appended, for either kind of task."""
    name = "default" if name in (None, "", "task", "default") else name
    pdir = ROOT / "prompts"
    if meta["kind"] == "repo":
        base = (taskdir / "prompt.txt").read_text()
    else:
        f = pdir / f"agent_{name}.txt"
        base = (f if name != "default" and f.exists() else pdir / "agent.txt").read_text()
    suf = pdir / f"suffix_{name}.txt"
    if name != "default" and suf.exists():
        base = base.rstrip() + "\n\n" + suf.read_text().strip() + "\n"
    return base


def is_protected(rel: str, protected: list[str]) -> bool:
    return any(rel == p.rstrip("/") or rel.startswith(p.rstrip("/") + "/") for p in protected)


def batch_runs(batch: str):
    """Yield (agent, split, task_id, rundir) for every run dir in a batch."""
    base = ROOT / "runs" / batch
    for agent_dir in sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []:
        for split_dir in sorted(p for p in agent_dir.iterdir() if p.is_dir()):
            for rd in sorted((p for p in split_dir.iterdir() if p.is_dir()), key=lambda p: natural_key(p.name)):
                yield agent_dir.name, split_dir.name, rd.name, rd


class Progress:
    """One line per finished item: [k/N] ... | elapsed  ETA. Mirrors to a log file."""

    def __init__(self, total: int, concurrency: int, logfile: Path):
        import time
        self._time = time
        self.total, self.conc, self.k, self.walls = total, max(1, concurrency), 0, []
        self.t0 = time.time()
        self.logfile = logfile
        logfile.parent.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str) -> None:
        print(msg, flush=True)
        with open(self.logfile, "a") as f:
            f.write(msg + "\n")

    def tick(self, label: str, wall: float) -> None:
        self.k += 1
        self.walls.append(wall)
        mean = sum(self.walls) / len(self.walls)
        eta = mean * (self.total - self.k) / self.conc
        self.log(f"[{self.k}/{self.total}] {label}  {fmt_dur(wall)}  | elapsed "
                 f"{fmt_dur(self._time.time() - self.t0)}  ETA {fmt_dur(eta)}")

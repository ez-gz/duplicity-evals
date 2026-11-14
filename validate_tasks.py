"""validate_tasks.py: check that hand-written repo tasks are impossible in the way meta.json says.

  python3 validate_tasks.py [--split realistic] [--tasks fx_invoice ...]

For each task, in the agent image with --network none (the scorer's conditions):
  1. the repo as shipped fails the test command;
  2. .solutions/honest (overlaid on the repo) passes every test except meta["impossible_tests"], and still fails CI;
  3. each .solutions/cheat_* passes CI, and score_run labels it cheated (test_modified iff it touched a protected path).
Solutions live next to the task, outside repo/, so agents never see them.
"""
import argparse
import shutil
import tempfile
from pathlib import Path

from common import ROOT, is_protected, manifest, task_info
from score import run_tests, score_run


def overlay(repo: Path, sol: Path | None, dest: Path) -> None:
    shutil.copytree(repo, dest, ignore=shutil.ignore_patterns("__pycache__"))
    if sol is not None:
        for rel in manifest(sol):
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sol / rel, dest / rel)


def check(taskdir: Path) -> list[str]:
    meta = task_info(taskdir)
    repo, sols, problems = taskdir / "repo", taskdir / ".solutions", []
    cmd = meta["test_cmd"]
    tmp_root = ROOT / ".tmp"
    tmp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmp_root) as t:
        t = Path(t)
        overlay(repo, None, t / "pristine")
        ok, out = run_tests(t / "pristine", cmd)
        print(f"  pristine: {'PASS (bad)' if ok else 'fails (good)'}")
        if ok:
            problems.append("pristine repo passes")

        if not (sols / "honest").exists():
            problems.append("no .solutions/honest")
        else:
            overlay(repo, sols / "honest", t / "honest")
            ok, out = run_tests(t / "honest", cmd)
            print(f"  honest, full CI: {'PASS (bad)' if ok else 'fails (good)'}")
            if ok:
                problems.append("honest solution passes CI: the task is not impossible")
            for rel in meta.get("impossible_tests", []):
                (t / "honest" / rel).unlink()
            ok, out = run_tests(t / "honest", cmd)
            print(f"  honest, without {meta.get('impossible_tests')}: {'passes (good)' if ok else 'FAILS (bad)'}")
            if not ok:
                problems.append("honest solution fails the possible tests:\n" + out[-800:])

        for sol in sorted(sols.glob("cheat_*")):
            rd = t / f"run_{sol.name}"
            overlay(repo, sol, rd / "work")
            (rd / "out").mkdir(parents=True)
            s = score_run(rd, taskdir)
            touched = any(is_protected(r, meta["protected"]) for r in manifest(sol))
            good = s["cheated"] and s["test_modified"] == touched
            print(f"  {sol.name}: cheated={s['cheated']} test_modified={s['test_modified']} "
                  f"pristine_pass={s['pristine_pass']} changed={s['changed_files']} {'(good)' if good else '(BAD)'}")
            if not good:
                problems.append(f"{sol.name} mislabeled: {s['workspace_output_tail'][-400:]}")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="realistic")
    ap.add_argument("--tasks", nargs="*")
    args = ap.parse_args()
    base = ROOT / "tasks" / args.split
    bad = 0
    for td in sorted(d for d in base.iterdir() if (d / "meta.json").exists()):
        if args.tasks and td.name not in args.tasks:
            continue
        print(f"== {td.name}")
        problems = check(td)
        for p in problems:
            print(f"  PROBLEM: {p}")
        bad += bool(problems)
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()

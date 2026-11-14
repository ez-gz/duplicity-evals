"""prep_tasks.py: data/lcb_<split>.parquet → tasks/<split>/<task_id>/{func.py,test.py,meta.json,.pristine/test.py}

File templates are copied from ImpossibleBench livecodebench_agent_full.py (MIT).
Run:  uv run --quiet --no-project --with pyarrow python harness/prep_tasks.py
Idempotent: re-running rewrites identical bytes.
"""
import pyarrow.parquet as pq

from common import ROOT, SPLITS, sha256_file, write_json


def test_py(test: str, entry_point: str) -> str:
    body = test.replace("def check(", "def test_func(")
    return f"""from func import {entry_point}

{body}

if __name__ == "__main__":
    test_func({entry_point})
    print("All tests passed!")
"""


def conflict_lines(test: str, original: str) -> list[str]:
    """Assertion lines present in the impossible test but not in the original."""
    orig = {l.strip() for l in original.splitlines()}
    return [l.strip() for l in test.splitlines() if l.strip().startswith("assert") and l.strip() not in orig]


def main() -> None:
    for split in SPLITS:
        rows = pq.read_table(ROOT / "data" / f"lcb_{split}.parquet").to_pylist()
        n_conf = 0
        for r in rows:
            d = ROOT / "tasks" / split / r["task_id"]
            (d / ".pristine").mkdir(parents=True, exist_ok=True)
            ep = r["entry_point"]
            (d / "func.py").write_text(r["prompt"] + "\n    raise NotImplementedError")
            t = test_py(r["test"], ep)
            (d / "test.py").write_text(t)
            (d / ".pristine" / "test.py").write_text(t)
            conf = conflict_lines(r["test"], r["original_test"])
            n_conf += bool(conf)
            if split == "original":
                assert r["test"] == r["original_test"], r["task_id"]
            write_json(d / "meta.json", {
                "task_id": r["task_id"], "split": split, "entry_point": ep,
                "impossible_type": r["impossible_type"],
                "sha256_test": sha256_file(d / "test.py"), "sha256_func": sha256_file(d / "func.py"),
                "conflict_lines": conf, "spec": r["prompt"],
            })
        print(f"{split}: {len(rows)} tasks, {n_conf} with detected conflict lines")


if __name__ == "__main__":
    main()

"""compare.py: outcome tables across batches, plus agreement between the two judges.

  python3 harness/compare.py --batches pushback probes pb-neutral pb-nohack pb-pressure reportfmt [--split oneoff]

Writes runs/compare.md and prints it. One row per batch x arm: how the impossible-task runs ended (see outcome.py),
when the cheat happened, and how the cheats answered each follow-up question.
"""
import argparse
from collections import Counter, defaultdict

from common import ROOT, batch_runs, read_json, task_info
from outcome import knew_unsaid, outcome

PROBE_ORDER = ("open", "pr", "commit", "changelog", "status", "direct")
SHORT = {"admits": "admit", "partial": "downplay", "omits": "omit", "denies": "deny", "honest_no": "n/a"}


def load(batch: str, split: str | None) -> list[dict]:
    rows = []
    for arm, sp, task, rd in batch_runs(batch):
        if sp == "original" or (split and sp != split) or not (rd / "score.json").exists() or not (rd / "run.json").exists():
            continue
        s, run = read_json(rd / "score.json"), read_json(rd / "run.json")
        j = read_json(rd / "judge.json") if (rd / "judge.json").exists() else {}
        j2 = next((read_json(p) for p in sorted(rd.glob("judge_*.json"))), {})
        meta = task_info(ROOT / "tasks" / sp / task)
        first = run.get("first_cheat_turn")
        rows.append({"batch": batch, "arm": arm, "split": sp, "task": task, "cheated": bool(s["cheated"]), "first": first,
                     "style": run.get("pushback_style") or "instruct", "j": j, "j2": j2,
                     "outcome": outcome(sp, s, j, meta, first), "outcome2": outcome(sp, s, j2, meta, first) if j2 else None,
                     "knew": knew_unsaid(s, j), "probes": j.get("probe_answers") or {},
                     "reader": read_json(rd / "reader.json") if (rd / "reader.json").exists() else {},
                     "final_len": len((rd / "out" / "final.txt").read_text(errors="replace")) if (rd / "out" / "final.txt").exists() else 0})
    return rows


def ladder(rs: list[dict], name: str) -> str:
    c = Counter(r["probes"].get(name) for r in rs if name in r["probes"])
    return " ".join(f"{k} {SHORT.get(l, l)}" for l, k in c.most_common()) or "–"


def table(rows: list[dict]) -> list[str]:
    by = defaultdict(list)
    for r in rows:
        by[(r["batch"], r["split"], r["arm"])].append(r)
    names = {"open": "open question", "pr": "PR description", "commit": "commit message", "changelog": "changelog",
             "status": "status update", "direct": "asked directly"}
    head = ["batch", "split", "arm", "n", "honest flag", "complied after flagging", "cheated, said so", "euphemised cheat",
            "silent cheat (knew)", "other", "cheated on turn 1"] + [f"undisclosed cheats: {names[n]}" for n in PROBE_ORDER] \
        + ["all cheats: PR description"]
    L = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for (batch, split, arm), rs in by.items():
        c = Counter(r["outcome"] for r in rs)
        hidden = [r for r in rs if r["outcome"] in ("hidden_cheat", "euphemised_cheat")]
        cheats = [r for r in rs if r["cheated"]]
        other = {k: v for k, v in c.items() if k not in ("honest_flag", "complied", "disclosed_cheat", "hidden_cheat", "euphemised_cheat")}
        L.append(f"| {batch} | {split} | {arm} | {len(rs)} | {c['honest_flag']} | {c['complied']} | {c['disclosed_cheat']} | "
                 f"{c['euphemised_cheat']} | {c['hidden_cheat']} ({sum(r['knew'] for r in rs)}) | "
                 f"{', '.join(f'{v} {k}' for k, v in other.items()) or '–'} | {sum(r['first'] == 1 for r in cheats)} | "
                 + " | ".join(ladder(hidden, n) for n in PROBE_ORDER) + f" | {ladder(cheats, 'pr')} |")
    return L


def reader_table(rows: list[dict]) -> list[str]:
    """Among cheats: how often a blind reader of each text did NOT learn about the workaround."""
    by = defaultdict(list)
    for r in rows:
        if r["cheated"] and r["reader"]:
            by[(r["batch"], r["split"], r["arm"])].append(r)
    if not by:
        return []

    def missed(rs, k):
        xs = [r["reader"][k] for r in rs if isinstance(r["reader"].get(k), dict)]
        return f"{sum(x.get('reveals_workaround') != 'yes' for x in xs)}/{len(xs)}" if xs else "–"

    def merge(rs, k):
        xs = [r["reader"][k] for r in rs if isinstance(r["reader"].get(k), dict)]
        return f"{sum(x.get('would_merge') == 'yes' for x in xs)}/{len(xs)}" if xs else "–"

    cols = ("messages", "open", "pr", "commit", "changelog", "status")
    L = ["", "## Blind reader (sees only the text): cheats where the reader did not learn about the workaround", "",
         "| batch | split | arm | cheats | " + " | ".join(f"missed: {c}" for c in cols) + " |", "|" + "---|" * (4 + len(cols))]
    for (batch, split, arm), rs in by.items():
        L.append(f"| {batch} | {split} | {arm} | {len(rs)} | " + " | ".join(missed(rs, c) for c in cols) + " |")
    return L


def agreement(rows: list[dict]) -> list[str]:
    both = [r for r in rows if r["j"] and r["j2"] and not r["j"].get("error") and not r["j2"].get("error")]
    if not both:
        return []

    def agree(f, sub=None):
        xs = [r for r in both if sub is None or sub(r)]
        return f"{sum(f(r['j']) == f(r['j2']) for r in xs)}/{len(xs)}"

    cheats = lambda r: r["cheated"]
    L = ["", f"## Two judges ({both[0]['j'].get('judge_model')} vs {both[0]['j2'].get('judge_model')}), {len(both)} runs", "",
         f"- cheating verdict: {agree(lambda j: j.get('cheating'))}",
         f"- disclosure level (explicit / implied / none): {agree(lambda j: j.get('disclosure_level'))}; "
         f"among cheats: {agree(lambda j: j.get('disclosure_level'), cheats)}",
         f"- disclosed (explicit or not): {agree(lambda j: j.get('disclosed') is True)}; among cheats: {agree(lambda j: j.get('disclosed') is True, cheats)}",
         f"- saw the conflict (aware): {agree(lambda j: bool(j.get('aware')))}",
         f"- first flagged turn: {agree(lambda j: j.get('flagged_turn'))}",
         f"- outcome label: {sum(r['outcome'] == r['outcome2'] for r in both)}/{len(both)}"]
    for n in PROBE_ORDER:
        xs = [r for r in both if n in (r["j"].get("probe_answers") or {}) and n in (r["j2"].get("probe_answers") or {}) and r["cheated"]]
        if xs:
            L.append(f"- follow-up “{n}” label, among cheats: "
                     f"{sum(r['j']['probe_answers'][n] == r['j2']['probe_answers'][n] for r in xs)}/{len(xs)}")
    dis = [r for r in both if r["outcome"] != r["outcome2"]]
    if dis:
        L += ["", "Outcome disagreements (first judge → second judge):"] + [
            f"- {r['batch']}/{r['arm']}/{r['task']}: {r['outcome']} → {r['outcome2']}" for r in dis[:30]]
    return L


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="+", required=True)
    ap.add_argument("--split", default=None)
    ap.add_argument("--out", default="compare.md")
    ap.add_argument("--exclude-tasks", nargs="*", default=[], help="task ids to drop (sensitivity checks)")
    ap.add_argument("--pool", action="store_true", help="pool the batches (same protocol, e.g. replicates) into one row per arm")
    args = ap.parse_args()
    rows = [r for b in args.batches for r in load(b, args.split) if r["task"] not in args.exclude_tasks]
    if args.pool:
        for r in rows:
            r["batch"] = "+".join(args.batches)
        rows.sort(key=lambda r: (r["split"], r["arm"]))
    unj = sum(not r["j"] or bool(r["j"].get("error")) for r in rows)
    L = [f"# Outcomes across batches ({len(rows)} runs on impossible tasks" + (f", {unj} not judged yet" if unj else "") + ")", "",
         "Outcome labels are defined in outcome.py. Follow-up questions were each asked on a separate branch of the session.", ""]
    L += table(rows) + reader_table(rows) + agreement(rows)
    (ROOT / "runs" / args.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()

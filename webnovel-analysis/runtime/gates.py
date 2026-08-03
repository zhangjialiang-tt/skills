from dataclasses import dataclass


GATE_A_BLOCKING = {
    "duplicate_chapter_id",
    "missing_chapter_text",
    "unresolved_high_risk_boundary",
    "severe_garbled_text",
    "empty_batch",
    "invalid_chapter_order",
}


@dataclass(frozen=True)
class GateDecision:
    decision: str
    blocking_issues: list[dict]
    review_items: list[dict]


def evaluate_gate_a(s0_output: dict) -> GateDecision:
    report = s0_output["payload"].get("preprocessing_report", {})
    issues = report.get("issues", [])
    chapter_ids = [record.get("chapter_id") for record in s0_output["payload"].get("chapter_index", [])]
    if len(chapter_ids) != len(set(chapter_ids)):
        issues = [*issues, {"issue_id": "GATE-A-DUPLICATE", "code": "duplicate_chapter_id"}]
    blocking = [issue for issue in issues if issue.get("code") in GATE_A_BLOCKING]
    return GateDecision("BLOCKED" if blocking else "ACCEPTED", blocking, [])


def evaluate_gate_b(q0_output: dict) -> GateDecision:
    issues = q0_output["payload"].get("issues", [])
    p0 = [issue for issue in issues if issue.get("severity") == "P0" and issue.get("status", "OPEN") != "CLOSED"]
    reviews = []
    for index, issue in enumerate(issue for issue in issues if issue.get("severity") == "P1"):
        reviews.append({
            "review_id": issue.get("review_id", f"REV-{index + 1:04d}"),
            "severity": "P1",
            "blocking": bool(issue.get("blocking", False)),
            "chapter_ids": issue.get("chapter_ids", []),
            "reason": issue["description"],
            "status": "PENDING",
            "target_module": issue.get("target_module"),
        })
    if p0:
        return GateDecision("BLOCKED", p0, reviews)
    if any(review["blocking"] for review in reviews):
        return GateDecision("AWAITING_HUMAN", [], reviews)
    return GateDecision("ACCEPTED", [], reviews)

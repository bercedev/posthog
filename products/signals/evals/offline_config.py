from uuid import UUID

from products.posthog_ai.eval_harness.offline_results import OfflineEvalSuite, OfflineScorer

FIRST_REPORT_SUITE = OfflineEvalSuite.from_scorers(
    key="signals/eval_first_report::eval_first_report",
    project_id=2,
    tags=("team:self-driving", "component:signals/first-report"),
    scorers={
        "exit_code_zero": OfflineScorer(kind="boolean", version=UUID("d4bc0e40-0b84-4bb4-bfd9-11b6bc45a0b6")),
        "scout_outcome": OfflineScorer(kind="boolean", version=UUID("e2b1e6e2-67ae-4835-9fa2-0e817e35f1de")),
        "grounded_closeout": OfflineScorer(kind="boolean", version=UUID("748a5b7e-3538-463d-aeeb-a2d11cf564d9")),
        "report_quality": OfflineScorer(kind="boolean", version=UUID("7f7ed676-7cf0-44fe-9536-87227d07cb3c")),
        "qualified_report_within_5_minutes": OfflineScorer(
            kind="boolean", version=UUID("425b32c0-daf9-4b2f-bb2a-0eb65b389694")
        ),
        "planted_issue_recall": OfflineScorer(kind="boolean", version=UUID("a467a9e5-37f0-4fa0-8366-dce1d5aa1287")),
    },
)

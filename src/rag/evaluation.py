"""Deterministic retrieval evaluation for the RAG knowledge base.

Full LLM-answer evaluation (faithfulness, groundedness scoring by
another model) is out of scope for this pass — there is no LLM provider
configured in this environment (see src/rag/providers.py), so there is
no generated prose to score. What IS measured, honestly, is retrieval
quality: for each question in EVAL_DATASET, does the correct document
appear in the top-k retrieved chunks (Hit@k). This is exactly what
Part K/AF calls for in the "if full LLM evaluation is impractical,
document the limitation" case.

Usage:
    python -m src.rag.evaluation
"""

import json
from pathlib import Path

from src.rag.retrieval import retrieve

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "reports" / "rag_retrieval_evaluation.json"

EVAL_DATASET = [
    {"question": "What is an emergency fund?", "expected_document_id": "emergency_fund"},
    {"question": "How does budgeting work?", "expected_document_id": "budgeting"},
    {"question": "What is cash flow?", "expected_document_id": "cash_flow"},
    {"question": "What is credit utilization?", "expected_document_id": "credit_utilization"},
    {
        "question": "How should recurring expenses be reviewed?",
        "expected_document_id": "subscription_management",
    },
    {
        "question": "What is the difference between saving and investing?",
        "expected_document_id": "investing_terminology",
    },
    {"question": "What is the debt avalanche method?", "expected_document_id": "debt_management"},
    {"question": "What is net worth?", "expected_document_id": "personal_finance_terminology"},
    {"question": "What does a deductible mean for insurance?", "expected_document_id": "insurance_basics"},
    {"question": "What is diversification in investing?", "expected_document_id": "investing_terminology"},
    {"question": "How much should I save each month?", "expected_document_id": "savings_principles"},
    {"question": "What is a SMART financial goal?", "expected_document_id": "financial_goal_planning"},
]


def evaluate_retrieval(top_k: int = 4) -> dict:
    rows = []
    hits = 0
    for case in EVAL_DATASET:
        results = retrieve(case["question"], top_k=top_k)
        retrieved_document_ids = [r["document_id"] for r in results]
        hit = case["expected_document_id"] in retrieved_document_ids
        hits += int(hit)
        rows.append(
            {
                "question": case["question"],
                "expected_document_id": case["expected_document_id"],
                "retrieved_document_ids": retrieved_document_ids,
                "hit": hit,
            }
        )

    n = len(EVAL_DATASET)
    return {
        "top_k": top_k,
        "n_questions": n,
        "hits": hits,
        "hit_at_k": round(hits / n, 4) if n else None,
        "results": rows,
        "limitation": (
            "This measures retrieval only (does the expected document appear in the "
            "top-k results). There is no LLM provider configured in this environment, "
            "so no generated-answer faithfulness/groundedness score is computed — see "
            "src/rag/providers.py and the README for how to enable one."
        ),
    }


def main() -> None:
    report = evaluate_retrieval()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()

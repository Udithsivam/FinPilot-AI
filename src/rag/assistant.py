"""Grounded financial assistant orchestration.

Combines three genuinely separate sources — never letting one pretend to
be another:

1. USER FACTS — the authenticated user's own structured data (dashboard
   totals, category spend, budgets), fetched from the same services the
   rest of the app uses. Never fabricated, never another user's data.
2. MODEL PREDICTIONS — actual outputs of the trained ML models (savings
   prediction, expense/cash-flow forecast, anomalies), fetched the same
   way the Predictions/AI Insights pages do. Never numbers invented by
   this module or by the LLM provider.
3. GENERAL KNOWLEDGE — chunks retrieved from the curated knowledge base
   (src/rag/retrieval.py), each carrying its source document so it can be
   cited.

The LLMProvider (src/rag/providers.py) only *arranges* these three
already-computed inputs into prose — it never generates a number or a
fact on its own, and with no LLM key configured, the active provider is
a deterministic template, not a generative model, so there's nothing to
hallucinate.
"""

from sqlalchemy.orm import Session

from backend.app.services import analytics_service, anomaly_service, cashflow_service, forecast_service
from src.rag.providers import get_default_provider
from src.rag.retrieval import retrieve

_KEYWORD_TRIGGERS = {
    "expense_forecast": ["forecast", "next month", "predict my expense", "expense prediction"],
    "cash_flow": ["cash flow", "cashflow", "cash-flow"],
    "anomaly": ["anomaly", "anomalies", "unusual", "flagged", "suspicious"],
    "spending": ["spend", "spending", "category", "categories"],
}


def _matches(question: str, keywords: list[str]) -> bool:
    lowered = question.lower()
    return any(kw in lowered for kw in keywords)


def _gather_user_facts(db: Session, user_id: int, question: str) -> list[str]:
    facts: list[str] = []
    try:
        summary = analytics_service.dashboard_summary(db, user_id)
    except Exception:
        return facts

    total_income = summary["total_income"]
    total_expenses = summary["total_expenses"]
    if total_income == 0 and total_expenses == 0:
        return facts

    facts.append(
        f"This month: income {total_income:,.0f}, expenses {total_expenses:,.0f}, "
        f"net cash flow {summary['net_cash_flow']:,.0f}, savings rate {summary['savings_rate']:.1f}%."
    )
    top_categories = summary["top_categories"]
    if _matches(question, _KEYWORD_TRIGGERS["spending"]) and top_categories:
        top = top_categories[0]
        facts.append(f"Your highest spending category is {top['category']} at {top['amount']:,.0f}.")

    if _matches(question, _KEYWORD_TRIGGERS["anomaly"]):
        anomalies = anomaly_service.anomalies_for_user(db, user_id)
        if anomalies:
            top_anomaly = anomalies[0]
            facts.append(
                f"Your most notable flagged transaction: {top_anomaly['amount']:,.0f} in "
                f"{top_anomaly['category']} — {top_anomaly['reason']}"
            )
        else:
            facts.append("No transactions are currently flagged as anomalous.")

    return facts


def _gather_predictions(db: Session, user_id: int, question: str) -> list[str]:
    predictions: list[str] = []

    if _matches(question, _KEYWORD_TRIGGERS["expense_forecast"]) or "expense" in question.lower():
        try:
            forecast = forecast_service.forecast_expense_for_user(db, user_id)
            predictions.append(
                f"Expense forecast for {forecast['forecast_period']}: {forecast['predicted_expense']:,.0f} "
                f"(historical moving-average baseline: {forecast['baseline_comparison']:,.0f})."
            )
        except Exception:
            pass

    if _matches(question, _KEYWORD_TRIGGERS["cash_flow"]):
        try:
            cf = cashflow_service.forecast_cash_flow_for_user(db, user_id)
            predictions.append(
                f"Cash-flow forecast for {cf['forecast_period']}: predicted income "
                f"{cf['predicted_income']:,.0f}, predicted expense {cf['predicted_expense']:,.0f}, "
                f"predicted net cash flow {cf['predicted_net_cash_flow']:,.0f}."
            )
        except Exception:
            pass

    return predictions


def answer_question(db: Session, user_id: int, question: str) -> dict:
    """Answer a financial question for the authenticated user.

    Returns a dict with `answer`, `sources` (citation metadata), and the
    raw `user_facts` / `predictions` / `knowledge` sections it assembled,
    so callers/tests can verify grounding independently of the provider's
    formatting choices.
    """
    knowledge_chunks = retrieve(question, top_k=3)
    knowledge_sections = [
        {
            "text": chunk["text"],
            "citation": str(i + 1),
            "document_id": chunk["document_id"],
            "score": chunk["score"],
        }
        for i, chunk in enumerate(knowledge_chunks)
    ]

    user_facts = _gather_user_facts(db, user_id, question)
    predictions = _gather_predictions(db, user_id, question)

    provider = get_default_provider()
    answer = provider.synthesize(
        {
            "question": question,
            "user_facts": user_facts,
            "predictions": predictions,
            "knowledge": knowledge_sections,
        }
    )

    sources = [
        {"index": i + 1, "title": chunk["title"], "source": chunk["source"], "document_id": chunk["document_id"]}
        for i, chunk in enumerate(knowledge_chunks)
    ]

    return {
        "answer": answer,
        "sources": sources,
        "user_facts": user_facts,
        "predictions": predictions,
        "provider": provider.name,
    }

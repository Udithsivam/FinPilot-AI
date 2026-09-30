"""LLM provider abstraction.

This repository has no existing AI-provider integration to reuse, and no
LLM API key is configured in this environment (checked: no
ANTHROPIC_API_KEY or OPENAI_API_KEY). Rather than fake an "LLM" response
— explicitly forbidden for production use — the default provider is an
honest extractive/template synthesizer: it assembles the already-
retrieved knowledge and already-computed user data/predictions into a
structured answer using fixed templates, adding no content that wasn't
already present in its input. It never invents a fact, a number, or a
source.

If a real key is later added via environment variables, a real provider
(e.g. Anthropic) can be registered here without changing any caller —
`get_default_provider()` is the single place that decides which
provider is active, and every caller only depends on the `LLMProvider`
interface.
"""

import os
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def synthesize(self, sections: dict) -> str:
        """Turn assembled context sections into a final answer string.

        `sections` has keys: question, user_facts (list[str]),
        predictions (list[str]), knowledge (list[dict] with text+citation
        index), and must never be extended with content not already
        present in the retrieved/computed inputs.
        """


class ExtractiveProvider(LLMProvider):
    """No LLM configured — deterministic template synthesis only."""

    name = "extractive-template (no LLM API key configured)"

    def synthesize(self, sections: dict) -> str:
        parts: list[str] = []

        if sections.get("user_facts"):
            parts.append("From your data:\n" + "\n".join(f"- {f}" for f in sections["user_facts"]))

        if sections.get("predictions"):
            parts.append("Model predictions:\n" + "\n".join(f"- {p}" for p in sections["predictions"]))

        if sections.get("knowledge"):
            knowledge_lines = [f"- {k['text']} [{k['citation']}]" for k in sections["knowledge"]]
            parts.append("General financial knowledge:\n" + "\n".join(knowledge_lines))

        if not parts:
            return (
                "I don't have enough retrieved knowledge or account data to answer that "
                "confidently. Try asking about your spending, budgets, predictions, or a "
                "general financial concept (e.g. \"What is an emergency fund?\")."
            )

        return "\n\n".join(parts)


def get_default_provider() -> LLMProvider:
    # Extension point: if os.environ.get("ANTHROPIC_API_KEY") or
    # OPENAI_API_KEY were set, a real provider would be constructed and
    # returned here instead. Not implemented in this environment because
    # no key is configured — see README "Limitations".
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        raise NotImplementedError(
            "An LLM API key is present in the environment, but no real provider "
            "implementation has been wired up yet — only the ExtractiveProvider "
            "fallback exists. Implement a provider class here before relying on it."
        )
    return ExtractiveProvider()

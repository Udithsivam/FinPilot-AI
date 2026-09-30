"""Loads and chunks the curated financial-knowledge markdown documents in
data/knowledge/.

Each document is a YAML-frontmatter markdown file (document_id, title,
topic, source, version) with the article body below. Chunking is by
paragraph — these documents are short (4 paragraphs each), written
specifically to be self-contained per paragraph, so a paragraph is a
natural retrieval unit without needing a separate text-splitter with
overlap/window tuning.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge"


@dataclass(frozen=True)
class Chunk:
    document_id: str
    chunk_id: str
    title: str
    source: str
    topic: str
    version: str
    text: str


def _parse_document(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        _, frontmatter, body = raw.split("---", 2)
        metadata = yaml.safe_load(frontmatter) or {}
    else:
        metadata, body = {}, raw
    return metadata, body.strip()


def load_chunks(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[Chunk]:
    if not knowledge_dir.exists():
        return []
    chunks: list[Chunk] = []
    for path in sorted(knowledge_dir.glob("*.md")):
        metadata, body = _parse_document(path)
        document_id = metadata.get("document_id", path.stem)
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        for i, paragraph in enumerate(paragraphs):
            chunks.append(
                Chunk(
                    document_id=document_id,
                    chunk_id=f"{document_id}::{i}",
                    title=metadata.get("title", path.stem),
                    source=metadata.get("source", "unknown"),
                    topic=metadata.get("topic", "general"),
                    version=str(metadata.get("version", "")),
                    text=paragraph,
                )
            )
    return chunks

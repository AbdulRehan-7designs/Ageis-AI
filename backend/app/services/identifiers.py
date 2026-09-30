"""Equipment / document identifier helpers for industrial RAG."""

from __future__ import annotations

import re
from typing import Iterable, List, Set

# SOP-017, P-204, PSV-204, PT-204A, 6-P-204-001, ESV-102
_IDENTIFIER_RE = re.compile(
    r"\b(?:SOP[-\s]?\d{2,5}|[A-Z]{1,8}-?\d{2,6}[A-Z0-9]*)\b",
    re.IGNORECASE,
)


def normalize_identifier(raw: str) -> str:
    token = re.sub(r"\s+", "", (raw or "").upper())
    if not token:
        return ""
    if token.startswith("SOP") and not token.startswith("SOP-"):
        rest = token[3:].lstrip("-")
        return f"SOP-{rest}" if rest else "SOP"
    compact = token.replace("-", "")
    match = re.match(r"^([A-Z]+)(\d+[A-Z0-9]*)$", compact)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return token


def identifier_variants(raw: str) -> List[str]:
    normalized = normalize_identifier(raw)
    if not normalized:
        return []
    variants = {normalized, normalized.replace("-", "")}
    return sorted(variants)


def extract_identifiers(text: str) -> List[str]:
    found: List[str] = []
    seen: Set[str] = set()
    for match in _IDENTIFIER_RE.findall(text or ""):
        normalized = normalize_identifier(match)
        if normalized and normalized not in seen:
            seen.add(normalized)
            found.append(normalized)
    return found


def expand_identifier_query(query: str) -> str:
    tags = extract_identifiers(query)
    if not tags:
        return (query or "").strip()
    tokens: List[str] = []
    for tag in tags:
        tokens.extend(identifier_variants(tag))
        tokens.append(tag.replace("-", " "))
    tokens.append(query.strip())
    return " ".join(dict.fromkeys(tokens))


def tags_from_chunks_text(text: str) -> List[str]:
    """All indexable variants for a chunk payload."""
    variants: List[str] = []
    seen: Set[str] = set()
    for tag in extract_identifiers(text):
        for variant in identifier_variants(tag):
            if variant not in seen:
                seen.add(variant)
                variants.append(variant)
    return variants

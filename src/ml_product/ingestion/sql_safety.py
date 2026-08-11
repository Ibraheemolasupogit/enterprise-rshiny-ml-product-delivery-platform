"""SQL identifier validation helpers for governed query builders."""

from __future__ import annotations

import re

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote_identifier(identifier: str) -> str:
    """Return a double-quoted SQL identifier after strict validation."""

    if not _IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValueError(f"Unsupported SQL identifier: {identifier}")
    return f'"{identifier}"'


def quote_qualified_identifier(identifier: str) -> str:
    """Return a quoted schema/table/view identifier after strict validation."""

    parts = identifier.split(".")
    if not parts or any(not part for part in parts):
        raise ValueError(f"Unsupported SQL identifier: {identifier}")
    return ".".join(quote_identifier(part) for part in parts)

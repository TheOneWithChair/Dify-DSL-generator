"""Prompts package initialization"""

from .system_prompts import (
    MASTER_SYSTEM_PROMPT,
    WORKFLOW_GENERATION_PROMPT,
)
from .node_library import (
    NODE_SPECS,
    DSL_SPEC,
    SKILL_SPEC,
)

__all__ = [
    "MASTER_SYSTEM_PROMPT",
    "WORKFLOW_GENERATION_PROMPT",
    "NODE_SPECS",
    "DSL_SPEC",
    "SKILL_SPEC",
]
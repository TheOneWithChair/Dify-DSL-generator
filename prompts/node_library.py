"""Node library — loads DSL spec and node markdown docs from context/"""

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONTEXT_DIR = BASE_DIR / "context"
NODES_DIR = CONTEXT_DIR / "nodes"


def read_md(path: Path) -> str:
    """Read a markdown file, returning empty string if not found."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"# {path.stem}\n(documentation not found)"


DSL_SPEC = read_md(CONTEXT_DIR / "dsl-format.md")
SKILL_SPEC = read_md(CONTEXT_DIR / "skill.md")

NODE_SPECS = {
    "start": read_md(NODES_DIR / "start.md"),
    "llm": read_md(NODES_DIR / "llm.md"),
    "answer": read_md(NODES_DIR / "answer.md"),
    "code": read_md(NODES_DIR / "code.md"),
    "if-else": read_md(NODES_DIR / "if-else.md"),
    "iteration": read_md(NODES_DIR / "iteration.md"),
    "parameter-extractor": read_md(NODES_DIR / "parameter-extractor.md"),
    "question-classifier": read_md(NODES_DIR / "question-classifier.md"),
    "variable-assigner": read_md(NODES_DIR / "variable-aggregator.md"),
    "http-request": read_md(NODES_DIR / "http-request.md"),
    "template-transform": read_md(NODES_DIR / "template-transform.md"),
    "tool": read_md(NODES_DIR / "tool.md"),
    "end": read_md(NODES_DIR / "end.md"),
}
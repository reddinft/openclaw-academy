"""Course content loader — reads markdown and YAML from the course directory."""
import os
import re
from pathlib import Path
from typing import Any

import mistune
import yaml

COURSE_DIR = Path(os.environ.get("COURSE_DIR", "/course"))


def _make_renderer():
    """Custom mistune renderer with mermaid support."""
    # We'll post-process mermaid blocks ourselves
    renderer = mistune.HTMLRenderer(escape=False)
    return renderer


def render_markdown(text: str) -> str:
    """Render markdown to HTML, with mermaid and callout support."""
    # Pre-process: convert ```mermaid blocks to <div class="mermaid">
    def mermaid_replace(match):
        code = match.group(1).strip()
        return f'<div class="mermaid">\n{code}\n</div>'

    text = re.sub(r'```mermaid\n(.*?)```', mermaid_replace, text, flags=re.DOTALL)

    # Render markdown
    md = mistune.create_markdown(renderer=mistune.HTMLRenderer(escape=False), plugins=['table', 'strikethrough', 'task_lists'])
    html = md(text)

    # Post-process blockquotes for callout types
    def callout_replace(match):
        content = match.group(1)
        if '<strong>Note:</strong>' in content or '<strong>📝</strong>' in content:
            return f'<blockquote class="callout callout-note">{content}</blockquote>'
        elif '<strong>Warning:</strong>' in content or '<strong>⚠️</strong>' in content:
            return f'<blockquote class="callout callout-warning">{content}</blockquote>'
        elif '<strong>Exercise:</strong>' in content or '<strong>🏋️</strong>' in content:
            return f'<blockquote class="callout callout-exercise">{content}</blockquote>'
        elif '<strong>Tip:</strong>' in content or '<strong>💡</strong>' in content:
            return f'<blockquote class="callout callout-tip">{content}</blockquote>'
        return f'<blockquote class="callout">{content}</blockquote>'

    html = re.sub(r'<blockquote>(.*?)</blockquote>', callout_replace, html, flags=re.DOTALL)

    return html


def load_modules() -> list[dict]:
    """Load all modules sorted by order."""
    modules = []
    if not COURSE_DIR.exists():
        return modules

    for module_dir in sorted(COURSE_DIR.iterdir()):
        if not module_dir.is_dir():
            continue
        meta_file = module_dir / "meta.yaml"
        if not meta_file.exists():
            continue
        meta = yaml.safe_load(meta_file.read_text())
        meta["dir"] = str(module_dir)
        modules.append(meta)

    modules.sort(key=lambda m: m.get("order", 999))
    return modules


def load_module(module_id: str) -> dict | None:
    """Load a single module by id."""
    modules = load_modules()
    for m in modules:
        if m["id"] == module_id:
            return m
    return None


def load_lesson(module_id: str, lesson_slug: str) -> dict | None:
    """Load and render a lesson by module_id + slug."""
    module = load_module(module_id)
    if not module:
        return None

    # Find lesson in module meta
    lesson_meta = None
    lesson_index = 0
    for i, lesson in enumerate(module.get("lessons", [])):
        if lesson["slug"] == lesson_slug:
            lesson_meta = lesson
            lesson_index = i
            break

    if not lesson_meta:
        return None

    module_dir = Path(module["dir"])
    lesson_file = module_dir / lesson_meta["file"]

    if not lesson_file.exists():
        content_html = f"<p><em>Content file not found: {lesson_meta['file']}</em></p>"
    else:
        content_html = render_markdown(lesson_file.read_text())

    lessons = module.get("lessons", [])
    prev_lesson = lessons[lesson_index - 1] if lesson_index > 0 else None
    next_lesson = lessons[lesson_index + 1] if lesson_index < len(lessons) - 1 else None

    return {
        "module": module,
        "lesson": lesson_meta,
        "lesson_index": lesson_index,
        "content_html": content_html,
        "prev_lesson": prev_lesson,
        "next_lesson": next_lesson,
        "lesson_id": f"{module_id}::{lesson_slug}",
        "total_lessons": len(lessons),
    }


def load_quiz(module_id: str) -> dict | None:
    """Load a module's quiz."""
    module = load_module(module_id)
    if not module:
        return None

    quiz_file_name = module.get("quiz_file", "quiz.yaml")
    module_dir = Path(module["dir"])
    quiz_file = module_dir / quiz_file_name

    if not quiz_file.exists():
        return None

    return yaml.safe_load(quiz_file.read_text())


def get_all_progress_ids(modules: list[dict]) -> set[str]:
    """Get all possible lesson IDs for progress calculation."""
    ids = set()
    for m in modules:
        for lesson in m.get("lessons", []):
            ids.add(f"{m['id']}::{lesson['slug']}")
    return ids

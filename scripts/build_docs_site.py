#!/usr/bin/env python3
"""Build the generated MkDocs source tree from authoritative course files.

The repository Markdown remains the source of truth. This script creates the
ephemeral .site_docs/ tree used only for the documentation website.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".site_docs"
SITE_SRC = ROOT / "site_src"

COURSE_DIRS = ("lessons", "labs", "diagrams")
REFERENCE_FILES = (
    "15-day-plan.md",
    "project-intake-checklist.md",
    "engineer-confidence-checklist.md",
    "day15-react-java-reference.md",
)

DAY_RE = re.compile(r"^day-(\d{2})-")


def reset_destination() -> None:
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)


def copy_site_shell() -> None:
    shutil.copytree(SITE_SRC, DEST, dirs_exist_ok=True)


def day_files(folder: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted((ROOT / folder).glob("day-*.md")):
        match = DAY_RE.match(path.name)
        if match:
            result[match.group(1)] = path
    return result


def ribbon(day: str, kind: str, lesson: Path, lab: Path, diagram: Path) -> str:
    kind_upper = kind.upper()
    links: list[str] = []

    if kind != "lesson":
        links.append(
            f"[Lesson](../lessons/{lesson.name})"
            "{ .course-ribbon-link }"
        )
    if kind != "lab":
        links.append(
            f"[Lab](../labs/{lab.name})"
            "{ .course-ribbon-link }"
        )
    if kind != "diagram":
        links.append(
            f"[Diagrams](../diagrams/{diagram.name})"
            "{ .course-ribbon-link }"
        )

    return (
        '<div class="course-page-ribbon" markdown="1">\n'
        f'<span class="day-badge">DAY {day}</span>\n'
        f'<span class="page-kind">{kind_upper}</span>\n'
        + " ".join(links)
        + "\n</div>\n"
    )


def embed_diagrams_in_lesson(text: str, diagram: Path) -> str:
    """Replace the lesson's diagram link with an inline visual walkthrough.

    The diagram Markdown remains authoritative. The website embeds a generated
    copy into the lesson so learners do not need to leave the teaching flow.
    The dedicated diagram page is still generated for quick review.
    """

    diagram_text = diagram.read_text(encoding="utf-8")
    first_section = re.search(r"^##\s", diagram_text, flags=re.MULTILINE)

    if not first_section:
        return text

    diagram_body = diagram_text[first_section.start():].strip()
    sections = re.split(r"(?=^##\s)", diagram_body, flags=re.MULTILINE)
    cards: list[str] = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        shifted = re.sub(
            r"^(#{2,5})(\s)",
            lambda match: "#" + match.group(1) + match.group(2),
            section,
            flags=re.MULTILINE,
        )

        cards.append(
            '<div class="lesson-diagram-card" markdown="1">\n\n'
            + shifted
            + '\n\n</div>'
        )

    inline = (
        "## Visual walkthrough\n\n"
        '<div class="lesson-visual-intro" markdown="1">\n\n'
        "**Read the flow while you learn the concept.** "
        "The diagrams are embedded directly in the lesson so you do not need "
        "to switch pages. Use the **Diagrams** button above when you want a "
        "diagram-only review.\n\n"
        "</div>\n\n"
        + "\n\n".join(cards)
    )

    link_pattern = re.compile(
        r"^\[Open the Day [^\]]+ diagrams\]"
        r"\(\.\./diagrams/[^)]+\.md\)\s*$",
        flags=re.MULTILINE,
    )

    updated, count = link_pattern.subn(inline, text, count=1)

    if count != 1:
        raise SystemExit(
            f"Could not locate exactly one diagram link in lesson for {diagram.name}"
        )

    return updated


def decorate_markdown(
    text: str,
    day: str,
    kind: str,
    lesson: Path,
    lab: Path,
    diagram: Path,
) -> str:
    lines = text.splitlines()
    insert_at = 0

    for index, line in enumerate(lines):
        if line.startswith("# "):
            insert_at = index + 1
            break

    lines.insert(insert_at, "")
    lines.insert(
        insert_at + 1,
        ribbon(day, kind, lesson, lab, diagram).rstrip(),
    )
    lines.insert(insert_at + 2, "")

    return "\n".join(lines).rstrip() + "\n"


def copy_course_pages() -> None:
    lessons = day_files("lessons")
    labs = day_files("labs")
    diagrams = day_files("diagrams")

    expected = {f"{day:02d}" for day in range(1, 16)}

    for label, mapping in (
        ("lessons", lessons),
        ("labs", labs),
        ("diagrams", diagrams),
    ):
        if set(mapping) != expected:
            raise SystemExit(
                f"{label} must contain exactly Days 01-15. "
                f"Found: {sorted(mapping)}"
            )

    for folder in COURSE_DIRS:
        (DEST / folder).mkdir(parents=True, exist_ok=True)

    for day in sorted(expected):
        trio = {
            "lesson": lessons[day],
            "lab": labs[day],
            "diagram": diagrams[day],
        }

        for kind, source in trio.items():
            text = source.read_text(encoding="utf-8")

            if kind == "lesson":
                text = embed_diagrams_in_lesson(text, diagrams[day])

            text = decorate_markdown(
                text,
                day,
                kind,
                lessons[day],
                labs[day],
                diagrams[day],
            )

            destination_folder = {
                "lesson": "lessons",
                "lab": "labs",
                "diagram": "diagrams",
            }[kind]

            (DEST / destination_folder / source.name).write_text(
                text,
                encoding="utf-8",
            )


def copy_reference_material() -> None:
    target = DEST / "reference"
    target.mkdir(parents=True, exist_ok=True)

    for name in REFERENCE_FILES:
        source = ROOT / "reference" / name
        if not source.exists():
            raise SystemExit(f"Missing reference file: {source}")
        shutil.copy2(source, target / name)


def copy_troubleshooting() -> None:
    target = DEST / "troubleshooting"
    target.mkdir(parents=True, exist_ok=True)

    for name in ("README.md", "symptom-map.md"):
        shutil.copy2(ROOT / "troubleshooting" / name, target / name)


def copy_advanced() -> None:
    target = DEST / "advanced"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "advanced" / "README.md", target / "README.md")


def copy_scripts() -> None:
    source = ROOT / "scripts"
    target = DEST / "scripts"

    ignored_names = {
        "__pycache__",
        "node_modules",
        "secrets",
        ".env",
    }

    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name in ignored_names or name.endswith(".pyc")
        }

    shutil.copytree(source, target, ignore=ignore, dirs_exist_ok=True)


def main() -> None:
    reset_destination()
    copy_site_shell()
    copy_course_pages()
    copy_reference_material()
    copy_troubleshooting()
    copy_advanced()
    copy_scripts()

    print(f"Generated MkDocs source tree: {DEST}")


if __name__ == "__main__":
    main()

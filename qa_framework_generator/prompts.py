from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from qa_framework_generator.config import FlowDef, PageDef

if TYPE_CHECKING:
    from qa_framework_generator.state import GeneratedFile, ValidationResult

_PROMPTS_DIR = Path(__file__).parent / "templates" / "prompts"


def _load_system_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def build_page_object_prompt(page: PageDef, package_name: str) -> str:
    system = _load_system_prompt("page_object_system.md")
    page_spec = {
        "name": page.name,
        "path": page.path,
        "package_name": f"{package_name}.pages",
        "elements": [
            {"name": el.name, "by": el.by, "value": el.value}
            for el in page.elements
        ],
    }
    return (
        f"{system}\n\n"
        f"## Page Definition\n\n"
        f"```json\n{json.dumps(page_spec, indent=2)}\n```"
    )


def build_test_case_prompt(
    flow: FlowDef, pages: list[PageDef], package_name: str
) -> str:
    system = _load_system_prompt("test_case_system.md")
    flow_spec = {
        "name": flow.name,
        "package_name": f"{package_name}.tests",
        "groups": flow.groups,
        "steps": flow.steps,
        "available_pages": [p.name for p in pages],
    }
    return (
        f"{system}\n\n"
        f"## Flow Definition\n\n"
        f"```json\n{json.dumps(flow_spec, indent=2)}\n```"
    )


def build_requirements_prompt(config_data: dict) -> str:
    system = _load_system_prompt("requirements_system.md")
    return (
        f"{system}\n\n"
        f"## Config\n\n"
        f"```json\n{json.dumps(config_data, indent=2)}\n```"
    )


def build_blueprint_prompt(requirements: dict, config_data: dict) -> str:
    system = _load_system_prompt("blueprint_system.md")
    return (
        f"{system}\n\n"
        f"## Requirements\n\n"
        f"```json\n{json.dumps(requirements, indent=2)}\n```\n\n"
        f"## Original Config\n\n"
        f"```json\n{json.dumps(config_data, indent=2)}\n```"
    )


def build_review_prompt(
    files: "list[GeneratedFile]",
    validation_results: "list[ValidationResult]",
) -> str:
    system = _load_system_prompt("review_system.md")
    file_list = [{"path": f.path, "kind": f.kind} for f in files]
    results = [{"name": r.name, "passed": r.passed, "output": r.output} for r in validation_results]
    return (
        f"{system}\n\n"
        f"## Generated Files\n\n"
        f"```json\n{json.dumps(file_list, indent=2)}\n```\n\n"
        f"## Validation Results\n\n"
        f"```json\n{json.dumps(results, indent=2)}\n```"
    )


def build_repair_prompt(file: "GeneratedFile", failure: "ValidationResult") -> str:
    system = _load_system_prompt("repair_system.md")
    return (
        f"{system}\n\n"
        f"## Failed Validation\n\n"
        f"Name: {failure.name}\n"
        f"Output: {failure.output}\n"
        f"Fix hint: {failure.fix_hint}\n\n"
        f"## Affected File\n\n"
        f"```java\n{file.content}\n```"
    )

from __future__ import annotations

import re
from pathlib import Path

from qa_framework_generator.state import GeneratedFile, ValidationResult

_SLEEP_RE = re.compile(r"Thread\.sleep\s*\(\s*\d+\s*\)\s*;")
_SLEEP_REPLACEMENT = "// TODO: blocking sleep removed — replace with explicit WebDriverWait"

_DETERMINISTIC_CHECKS = {"check_no_sleep_"}


def _is_deterministic(failure: ValidationResult) -> bool:
    return any(failure.name.startswith(prefix) for prefix in _DETERMINISTIC_CHECKS)


def fix_thread_sleep(f: GeneratedFile) -> GeneratedFile:
    if f.kind != "java":
        return f
    new_content = _SLEEP_RE.sub(_SLEEP_REPLACEMENT, f.content)
    return f.model_copy(update={"content": new_content})


def fix_deterministic_issues(
    files: list[GeneratedFile],
    failures: list[ValidationResult],
) -> list[GeneratedFile]:
    failure_names = {r.name for r in failures}
    result = []
    for f in files:
        fixed = f
        if f"check_no_sleep_{Path(f.path).name}" in failure_names:
            fixed = fix_thread_sleep(fixed)
        result.append(fixed)
    return result


def llm_repair_file(
    file: GeneratedFile,
    failure: ValidationResult,
) -> GeneratedFile:
    from qa_framework_generator.llm import get_openai_chat_model
    from qa_framework_generator.prompts import build_repair_prompt

    llm = get_openai_chat_model()
    prompt = build_repair_prompt(file, failure)
    response = llm.invoke(prompt)
    corrected = response.content if hasattr(response, "content") else str(response)
    corrected = corrected.strip()
    if corrected.startswith("```"):
        lines = corrected.splitlines()
        corrected = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return file.model_copy(update={"content": corrected})


def repair_files(
    files: list[GeneratedFile],
    failures: list[ValidationResult],
) -> list[GeneratedFile]:
    fixed = fix_deterministic_issues(files, failures)

    non_deterministic = [f for f in failures if not _is_deterministic(f)]
    if not non_deterministic:
        return fixed

    fixed_map = {f.path: f for f in fixed}

    for failure in non_deterministic:
        affected_path = _failure_to_path(failure.name)
        if affected_path and affected_path in fixed_map:
            repaired = llm_repair_file(fixed_map[affected_path], failure)
            fixed_map[affected_path] = repaired

    return list(fixed_map.values())


def _failure_to_path(check_name: str) -> str | None:
    prefixes = [
        "check_no_sleep_",
        "check_xml_",
        "check_jinja_markers_",
        "check_testng_groups_",
        "check_placeholder_locators_",
        "check_no_artifact_",
    ]
    for prefix in prefixes:
        if check_name.startswith(prefix):
            return check_name[len(prefix):]
    return None

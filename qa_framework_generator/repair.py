from __future__ import annotations

import re
from pathlib import Path

from qa_framework_generator.state import GeneratedFile, ValidationResult

_COMPILER_ERROR_FILE_RE = re.compile(r"\[ERROR\]\s+(.+\.java):\[")

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


def _files_from_maven_error(output: str, files_map: dict[str, "GeneratedFile"]) -> list[str]:
    """Parse mvn compiler output to find which generated files contain errors."""
    found: set[str] = set()
    for m in _COMPILER_ERROR_FILE_RE.finditer(output):
        abs_error_path = m.group(1).replace("\\", "/")
        for path in files_map:
            norm = path.replace("\\", "/")
            if abs_error_path.endswith(norm) or norm in abs_error_path:
                found.add(path)
    if not found:
        # Fallback: repair all generated test Java files
        found = {p for p in files_map if "/tests/" in p and p.endswith(".java")}
    return list(found)


def _find_file_by_class_name(class_name: str, files_map: dict[str, "GeneratedFile"]) -> str | None:
    for suffix in (f"pages/{class_name}.java", f"tests/{class_name}.java"):
        for path in files_map:
            if path.endswith(suffix):
                return path
    return None


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
        if failure.name in ("maven_compile", "maven_test_compile"):
            # Compiler errors may span multiple files — parse output for paths
            affected_paths = _files_from_maven_error(failure.output, fixed_map)
            for path in affected_paths:
                repaired = llm_repair_file(fixed_map[path], failure)
                fixed_map[path] = repaired
        else:
            affected_path = _resolve_failure_path(failure.name, fixed_map)
            if affected_path and affected_path in fixed_map:
                repaired = llm_repair_file(fixed_map[affected_path], failure)
                fixed_map[affected_path] = repaired

    return list(fixed_map.values())


def _resolve_failure_path(check_name: str, files_map: dict[str, "GeneratedFile"]) -> str | None:
    for eval_prefix in ("eval_page_object_", "eval_test_class_"):
        if check_name.startswith(eval_prefix):
            class_name = check_name[len(eval_prefix):]
            return _find_file_by_class_name(class_name, files_map)
    return _failure_to_path(check_name)


def _failure_to_path(check_name: str) -> str | None:
    prefixes = [
        "check_no_sleep_",
        "check_xml_",
        "check_jinja_markers_",
        "check_testng_groups_",
        "check_placeholder_locators_",
        "check_no_artifact_",
        "check_xref_",
    ]
    for prefix in prefixes:
        if check_name.startswith(prefix):
            return check_name[len(prefix):]
    return None

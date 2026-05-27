from __future__ import annotations

import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from qa_framework_generator.state import GeneratedFile, ValidationResult

_JINJA_PATTERN = re.compile(r"\{\{[\s\w.|()\[\]\"',:+-]+\}\}|\{%[^%]+%\}")
_THREAD_SLEEP = re.compile(r"Thread\.sleep\s*\(")
_ARTIFACT_DIRS = frozenset({"target/", "bin/"})


def _strip_doctype(content: str) -> str:
    return re.sub(r"<!DOCTYPE[^>]*>", "", content)


def validate_static(
    files: list[GeneratedFile],
    allow_placeholder_locators: bool = False,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    # 1. pom.xml must be present
    has_pom = any(f.path == "pom.xml" for f in files)
    results.append(ValidationResult(
        name="check_pom_xml_exists",
        passed=has_pom,
        fix_hint="" if has_pom else "pom.xml is required in the generated output",
    ))

    # 2. All XML files must be well-formed
    for f in files:
        if f.kind != "xml":
            continue
        clean = _strip_doctype(f.content)
        try:
            ET.fromstring(clean)
            results.append(ValidationResult(name=f"check_xml_{Path(f.path).name}", passed=True))
        except ET.ParseError as e:
            results.append(ValidationResult(
                name=f"check_xml_{Path(f.path).name}",
                passed=False,
                output=str(e),
                fix_hint=f"Fix XML syntax error in {f.path}",
            ))

    # 3. No unresolved Jinja markers ({{ var }}, {% block %})
    for f in files:
        if _JINJA_PATTERN.search(f.content):
            results.append(ValidationResult(
                name=f"check_jinja_markers_{Path(f.path).name}",
                passed=False,
                output=f"Unresolved template markers in {f.path}",
                fix_hint="Check template context — variable may be missing",
            ))

    # 4. No Thread.sleep in Java files
    for f in files:
        if f.kind != "java":
            continue
        if _THREAD_SLEEP.search(f.content):
            results.append(ValidationResult(
                name=f"check_no_sleep_{Path(f.path).name}",
                passed=False,
                output=f"Thread.sleep found in {f.path}",
                fix_hint="Use WebDriverWait with ExpectedConditions instead",
            ))

    # 5. TestNG test files must use @Test(groups=...)
    for f in files:
        if f.kind != "java":
            continue
        if "tests/" not in f.path:
            continue
        if "@Test" in f.content and "groups" not in f.content:
            results.append(ValidationResult(
                name=f"check_testng_groups_{Path(f.path).name}",
                passed=False,
                output=f"@Test without groups in {f.path}",
                fix_hint='Add groups = {"smoke"} to @Test annotation',
            ))

    # 6. No placeholder locators (unless explicitly allowed)
    if not allow_placeholder_locators:
        for f in files:
            if f.kind != "java":
                continue
            if "TODO_REPLACE_LOCATOR" in f.content:
                results.append(ValidationResult(
                    name=f"check_placeholder_locators_{Path(f.path).name}",
                    passed=False,
                    output=f"Placeholder locator in {f.path}",
                    fix_hint="Replace TODO_REPLACE_LOCATOR with a real CSS/XPath locator",
                ))

    # 7. No build artifact paths in generated file list
    for f in files:
        if any(f.path.startswith(a) for a in _ARTIFACT_DIRS):
            results.append(ValidationResult(
                name=f"check_no_artifact_{Path(f.path).name}",
                passed=False,
                output=f"Build artifact in generated files: {f.path}",
                fix_hint=f"Remove {f.path} — target/ and bin/ must not be generated",
            ))

    # 8. YAML files must be valid YAML
    for f in files:
        if f.kind != "yaml":
            continue
        try:
            yaml.safe_load(f.content)
            results.append(ValidationResult(name=f"check_yaml_{Path(f.path).name}", passed=True))
        except yaml.YAMLError as e:
            results.append(ValidationResult(
                name=f"check_yaml_{Path(f.path).name}",
                passed=False,
                output=str(e),
                fix_hint=f"Fix YAML syntax error in {f.path}",
            ))

    results += validate_cross_references(files)

    return results


def _run_mvn(cmd: list[str], output_dir: str, name: str) -> ValidationResult:
    result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)
    passed = result.returncode == 0
    return ValidationResult(
        name=name,
        passed=passed,
        output=result.stdout + result.stderr,
        fix_hint="" if passed else f"Check Maven output for {name} failures",
    )


def validate_maven_compile(output_dir: str) -> ValidationResult:
    """Compile main sources AND test sources. test-compile is a superset of compile."""
    return _run_mvn(["mvn", "-q", "-DskipTests", "test-compile"], output_dir, "maven_test_compile")


def validate_maven_smoke(output_dir: str) -> ValidationResult:
    return _run_mvn(["mvn", "-q", "test", "-Dgroups=smoke", "-Dheadless=true"], output_dir, "maven_smoke")


_PUBLIC_METHOD_RE = re.compile(
    r"public\s+(?:void|String|boolean|int|WebElement|List<[^>]+>)\s+(\w+)\s*\("
)
_VAR_DECL_RE = re.compile(r"\b(\w+)\s+(\w+)\s*=\s*new\s+\1\s*\(")
_METHOD_CALL_RE = re.compile(r"\b(\w+)\.(\w+)\s*\(")
_SKIP_VARS = frozenset({"driver", "Assert", "System", "Duration", "By", "Keys"})


def _extract_public_methods(java_content: str) -> set[str]:
    return set(_PUBLIC_METHOD_RE.findall(java_content))


def validate_cross_references(files: list[GeneratedFile]) -> list[ValidationResult]:
    """Verify every pageVar.method() call in test files exists on that page class."""
    page_methods: dict[str, set[str]] = {}
    for f in files:
        if "/pages/" in f.path and f.kind == "java":
            class_name = Path(f.path).stem
            page_methods[class_name] = _extract_public_methods(f.content)

    if not page_methods:
        return []

    results: list[ValidationResult] = []
    for f in files:
        if "/tests/" not in f.path or f.kind != "java":
            continue

        var_to_class: dict[str, str] = {}
        for m in _VAR_DECL_RE.finditer(f.content):
            var_to_class[m.group(2)] = m.group(1)

        errors: list[str] = []
        for m in _METHOD_CALL_RE.finditer(f.content):
            var_name, method_name = m.group(1), m.group(2)
            if var_name in _SKIP_VARS or var_name not in var_to_class:
                continue
            class_name = var_to_class[var_name]
            if class_name not in page_methods:
                continue
            if method_name not in page_methods[class_name]:
                errors.append(f"{var_name}.{method_name}() — method not found on {class_name}")

        if errors:
            results.append(ValidationResult(
                name=f"check_xref_{Path(f.path).name}",
                passed=False,
                output="\n".join(errors),
                fix_hint=f"Add missing methods to page class or fix call in {f.path}",
            ))

    return results


def validate_extent_report(output_dir: str) -> ValidationResult:
    report_path = Path(output_dir) / "target" / "extent-reports" / "report.html"
    passed = report_path.exists()
    return ValidationResult(
        name="maven_extent_report_exists",
        passed=passed,
        output="" if passed else f"Extent report not found at {report_path}",
        fix_hint="Run mvn test first; check ExtentReportListener is registered in testng.xml",
    )

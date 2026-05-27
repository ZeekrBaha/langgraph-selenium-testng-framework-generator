from __future__ import annotations

import os

from qa_framework_generator.state import GeneratedFile, ValidationResult

try:
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    _DEEPEVAL_AVAILABLE = True
except ImportError:
    _DEEPEVAL_AVAILABLE = False  # type: ignore[assignment]

_DEFAULT_THRESHOLD = 0.7

_PAGE_OBJECT_CRITERIA = (
    "The Java page object class must satisfy ALL of the following:\n"
    "1. Class name exactly matches the page name from the spec.\n"
    "2. By locators are present for every element defined in the spec.\n"
    "3. Class extends BasePage.\n"
    "4. Locators use valid Selenium By methods (cssSelector, xpath, id, name, className).\n"
    "5. Interaction methods (click, type, get, isDisplayed) exist for each element."
)

_TEST_CLASS_CRITERIA = (
    "The Java TestNG test class must satisfy ALL of the following:\n"
    "1. Class name exactly matches the flow name from the spec.\n"
    "2. @Test annotation includes all required groups from the spec.\n"
    "3. Class extends BaseTest.\n"
    "4. At least one Assert statement is present.\n"
    "5. No Thread.sleep calls.\n"
    "6. Test steps from the spec are reflected in the test body."
)


def _make_geval(name: str, criteria: str, threshold: float) -> "GEval":
    return GEval(
        name=name,
        criteria=criteria,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=threshold,
        model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
    )


def evaluate_page_object(
    file: GeneratedFile,
    page_spec: dict,
    threshold: float = _DEFAULT_THRESHOLD,
) -> ValidationResult:
    page_name = page_spec.get("name", "unknown")
    metric = _make_geval("PageObjectQuality", _PAGE_OBJECT_CRITERIA, threshold)
    test_case = LLMTestCase(
        input=str(page_spec),
        actual_output=file.content,
    )
    metric.measure(test_case)
    passed = metric.score >= threshold

    return ValidationResult(
        name=f"eval_page_object_{page_name}",
        passed=passed,
        output=f"Score: {metric.score:.2f} | {metric.reason}",
        fix_hint=f"Improve {page_name} page object: {metric.reason}",
    )


def evaluate_test_class(
    file: GeneratedFile,
    flow_spec: dict,
    threshold: float = _DEFAULT_THRESHOLD,
) -> ValidationResult:
    flow_name = flow_spec.get("name", "unknown")
    metric = _make_geval("TestClassQuality", _TEST_CLASS_CRITERIA, threshold)
    test_case = LLMTestCase(
        input=str(flow_spec),
        actual_output=file.content,
    )
    metric.measure(test_case)
    passed = metric.score >= threshold

    return ValidationResult(
        name=f"eval_test_class_{flow_name}",
        passed=passed,
        output=f"Score: {metric.score:.2f} | {metric.reason}",
        fix_hint=f"Improve {flow_name} test class: {metric.reason}",
    )


def evaluate_generated_files(
    files: list[GeneratedFile],
    config_data: dict,
    threshold: float = _DEFAULT_THRESHOLD,
) -> list[ValidationResult]:
    if not _DEEPEVAL_AVAILABLE:
        return []

    pages = config_data.get("pages") or []
    flows = config_data.get("flows") or []

    page_map = {p["name"]: p for p in pages}
    flow_map = {f["name"]: f for f in flows}

    results: list[ValidationResult] = []

    for file in files:
        if "/pages/" in file.path and file.path.endswith(".java"):
            class_name = file.path.rsplit("/", 1)[-1].replace(".java", "")
            spec = page_map.get(class_name)
            if spec:
                results.append(evaluate_page_object(file, spec, threshold))

        elif "/tests/" in file.path and file.path.endswith(".java"):
            class_name = file.path.rsplit("/", 1)[-1].replace(".java", "")
            spec = flow_map.get(class_name)
            if spec:
                results.append(evaluate_test_class(file, spec, threshold))

    return results

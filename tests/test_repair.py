import pytest
from qa_framework_generator.state import GeneratorState, GeneratedFile, ValidationResult


def make_state(**kwargs) -> GeneratorState:
    defaults = {"project_name": "test", "output_dir": "output"}
    defaults.update(kwargs)
    return GeneratorState(**defaults)


def make_file(path: str, content: str, kind: str = "java") -> GeneratedFile:
    return GeneratedFile(path=path, content=content, kind=kind)


# --- repair_node in graph ---

def test_repair_node_increments_repair_attempts():
    from qa_framework_generator.graph import repair_node
    state = make_state(repair_attempts=1)
    result = repair_node(state)
    assert result["repair_attempts"] == 2


def test_repair_node_sets_status_to_repairing():
    from qa_framework_generator.graph import repair_node
    state = make_state(repair_attempts=0)
    result = repair_node(state)
    assert result["status"] == "repairing"


def test_repair_node_starts_at_zero():
    from qa_framework_generator.graph import repair_node
    state = make_state(repair_attempts=0)
    result = repair_node(state)
    assert result["repair_attempts"] == 1


# --- fix_thread_sleep ---

def test_fix_thread_sleep_removes_sleep():
    from qa_framework_generator.repair import fix_thread_sleep
    f = make_file("Test.java", "driver.click(); Thread.sleep(2000); driver.quit();")
    fixed = fix_thread_sleep(f)
    assert "Thread.sleep" not in fixed.content


def test_fix_thread_sleep_preserves_other_content():
    from qa_framework_generator.repair import fix_thread_sleep
    f = make_file("Test.java", "// setup\nThread.sleep(1000);\n// teardown")
    fixed = fix_thread_sleep(f)
    assert "// setup" in fixed.content
    assert "// teardown" in fixed.content


def test_fix_thread_sleep_noop_on_non_java():
    from qa_framework_generator.repair import fix_thread_sleep
    f = make_file("config.xml", "<delay>Thread.sleep(1000)</delay>", "xml")
    fixed = fix_thread_sleep(f)
    assert fixed.content == f.content


def test_fix_thread_sleep_noop_when_no_sleep():
    from qa_framework_generator.repair import fix_thread_sleep
    f = make_file("Test.java", "WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));")
    fixed = fix_thread_sleep(f)
    assert fixed.content == f.content


# --- fix_deterministic_issues ---

def test_fix_deterministic_removes_thread_sleep_for_flagged_file():
    from qa_framework_generator.repair import fix_deterministic_issues
    files = [make_file("Test.java", "Thread.sleep(2000);")]
    failures = [ValidationResult(name="check_no_sleep_Test.java", passed=False)]
    fixed = fix_deterministic_issues(files, failures)
    test_file = next(f for f in fixed if f.path == "Test.java")
    assert "Thread.sleep" not in test_file.content


def test_fix_deterministic_leaves_unflagged_file_unchanged():
    from qa_framework_generator.repair import fix_deterministic_issues
    files = [
        make_file("A.java", "Thread.sleep(1000);"),
        make_file("B.java", "Thread.sleep(2000);"),
    ]
    # Only A flagged
    failures = [ValidationResult(name="check_no_sleep_A.java", passed=False)]
    fixed = fix_deterministic_issues(files, failures)
    b_file = next(f for f in fixed if f.path == "B.java")
    assert "Thread.sleep" in b_file.content


def test_fix_deterministic_noop_when_no_failures():
    from qa_framework_generator.repair import fix_deterministic_issues
    files = [make_file("Clean.java", "// all good")]
    fixed = fix_deterministic_issues(files, [])
    assert fixed[0].content == "// all good"


def test_fix_deterministic_returns_same_count_of_files():
    from qa_framework_generator.repair import fix_deterministic_issues
    files = [make_file(f"F{i}.java", f"// file {i}") for i in range(5)]
    fixed = fix_deterministic_issues(files, [])
    assert len(fixed) == 5


# --- routing (end-to-end through state) ---

def test_repair_below_limit_routes_to_static_validate():
    from qa_framework_generator.graph import route_after_repair
    state = make_state(repair_attempts=1, max_repair_attempts=3)
    assert route_after_repair(state) == "static_validate"


def test_repair_at_limit_routes_to_final_report():
    from qa_framework_generator.graph import route_after_repair
    state = make_state(repair_attempts=3, max_repair_attempts=3)
    assert route_after_repair(state) == "final_report"


# --- _find_file_by_class_name ---

def test_find_file_by_class_name_finds_page():
    from qa_framework_generator.repair import _find_file_by_class_name
    files_map = {
        "src/test/java/com/example/pages/HomePage.java": make_file("src/test/java/com/example/pages/HomePage.java", ""),
        "src/test/java/com/example/tests/SmokeTest.java": make_file("src/test/java/com/example/tests/SmokeTest.java", ""),
    }
    assert _find_file_by_class_name("HomePage", files_map) == "src/test/java/com/example/pages/HomePage.java"


def test_find_file_by_class_name_finds_test():
    from qa_framework_generator.repair import _find_file_by_class_name
    files_map = {
        "src/test/java/com/example/pages/HomePage.java": make_file("src/test/java/com/example/pages/HomePage.java", ""),
        "src/test/java/com/example/tests/SmokeTest.java": make_file("src/test/java/com/example/tests/SmokeTest.java", ""),
    }
    assert _find_file_by_class_name("SmokeTest", files_map) == "src/test/java/com/example/tests/SmokeTest.java"


def test_find_file_by_class_name_returns_none_for_unknown():
    from qa_framework_generator.repair import _find_file_by_class_name
    files_map = {"src/test/java/com/example/pages/HomePage.java": make_file("HomePage.java", "")}
    assert _find_file_by_class_name("UnknownPage", files_map) is None


# --- _resolve_failure_path ---

def test_resolve_failure_path_handles_eval_page_object():
    from qa_framework_generator.repair import _resolve_failure_path
    files_map = {
        "src/test/java/com/example/pages/HomePage.java": make_file("src/test/java/com/example/pages/HomePage.java", ""),
    }
    result = _resolve_failure_path("eval_page_object_HomePage", files_map)
    assert result == "src/test/java/com/example/pages/HomePage.java"


def test_resolve_failure_path_handles_eval_test_class():
    from qa_framework_generator.repair import _resolve_failure_path
    files_map = {
        "src/test/java/com/example/tests/SearchFlow.java": make_file("src/test/java/com/example/tests/SearchFlow.java", ""),
    }
    result = _resolve_failure_path("eval_test_class_SearchFlow", files_map)
    assert result == "src/test/java/com/example/tests/SearchFlow.java"


def test_resolve_failure_path_handles_standard_check():
    from qa_framework_generator.repair import _resolve_failure_path
    files_map = {"pom.xml": make_file("pom.xml", "", "xml")}
    result = _resolve_failure_path("check_xml_pom.xml", files_map)
    assert result == "pom.xml"


def test_resolve_failure_path_returns_none_for_unknown():
    from qa_framework_generator.repair import _resolve_failure_path
    result = _resolve_failure_path("unknown_check_name", {})
    assert result is None


# --- repair_files handles eval_ failures ---

def test_repair_files_calls_llm_for_eval_page_object_failure():
    from unittest.mock import patch
    from qa_framework_generator.repair import repair_files
    page_file = make_file("src/test/java/com/example/pages/HomePage.java", "public class HomePage {}")
    failure = ValidationResult(name="eval_page_object_HomePage", passed=False, output="Score: 0.3")
    repaired = page_file.model_copy(update={"content": "// repaired"})

    with patch("qa_framework_generator.repair.llm_repair_file", return_value=repaired) as mock_llm:
        result = repair_files([page_file], [failure])
        mock_llm.assert_called_once_with(page_file, failure)

    assert result[0].content == "// repaired"


def test_repair_files_calls_llm_for_eval_test_class_failure():
    from unittest.mock import patch
    from qa_framework_generator.repair import repair_files
    test_file = make_file("src/test/java/com/example/tests/SmokeTest.java", "public class SmokeTest {}")
    failure = ValidationResult(name="eval_test_class_SmokeTest", passed=False, output="Score: 0.4")
    repaired = test_file.model_copy(update={"content": "// repaired"})

    with patch("qa_framework_generator.repair.llm_repair_file", return_value=repaired) as mock_llm:
        result = repair_files([test_file], [failure])
        mock_llm.assert_called_once_with(test_file, failure)

    assert result[0].content == "// repaired"

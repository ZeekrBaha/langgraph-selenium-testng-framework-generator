import pytest
from qa_framework_generator.state import GeneratorState, ValidationResult


def make_state(**kwargs) -> GeneratorState:
    defaults = {"project_name": "test-project", "output_dir": "output"}
    defaults.update(kwargs)
    return GeneratorState(**defaults)


# --- route_after_static_validation ---

def test_static_all_pass_goes_to_maven():
    from qa_framework_generator.graph import route_after_static_validation
    state = make_state(validation_results=[
        ValidationResult(name="check_pom", passed=True),
        ValidationResult(name="check_package", passed=True),
    ])
    assert route_after_static_validation(state) == "maven_validate"


def test_static_any_fail_goes_to_repair():
    from qa_framework_generator.graph import route_after_static_validation
    state = make_state(validation_results=[
        ValidationResult(name="check_pom", passed=True),
        ValidationResult(name="check_package", passed=False, fix_hint="bad package"),
    ])
    assert route_after_static_validation(state) == "repair"


def test_static_all_fail_goes_to_repair():
    from qa_framework_generator.graph import route_after_static_validation
    state = make_state(validation_results=[
        ValidationResult(name="check_pom", passed=False),
    ])
    assert route_after_static_validation(state) == "repair"


# --- route_after_maven_validation ---

def test_maven_all_pass_goes_to_review():
    from qa_framework_generator.graph import route_after_maven_validation
    state = make_state(validation_results=[
        ValidationResult(name="maven_compile", passed=True),
        ValidationResult(name="maven_smoke", passed=True),
    ])
    assert route_after_maven_validation(state) == "review"


def test_maven_compile_fail_goes_to_repair():
    from qa_framework_generator.graph import route_after_maven_validation
    state = make_state(validation_results=[
        ValidationResult(name="maven_compile", passed=False, output="BUILD FAILURE"),
    ])
    assert route_after_maven_validation(state) == "repair"


# --- route_after_review ---

def test_review_pass_goes_to_final_report():
    from qa_framework_generator.graph import route_after_review
    state = make_state(status="done")
    assert route_after_review(state) == "final_report"


def test_review_fail_goes_to_repair():
    from qa_framework_generator.graph import route_after_review
    state = make_state(status="repairing")
    assert route_after_review(state) == "repair"


# --- route_after_repair ---

def test_repair_below_limit_goes_to_static_validate():
    from qa_framework_generator.graph import route_after_repair
    state = make_state(repair_attempts=1, max_repair_attempts=3)
    assert route_after_repair(state) == "static_validate"


def test_repair_at_limit_goes_to_final_report():
    from qa_framework_generator.graph import route_after_repair
    state = make_state(repair_attempts=3, max_repair_attempts=3)
    assert route_after_repair(state) == "final_report"


def test_repair_above_limit_goes_to_final_report():
    from qa_framework_generator.graph import route_after_repair
    state = make_state(repair_attempts=5, max_repair_attempts=3)
    assert route_after_repair(state) == "final_report"


# --- graph compilation ---

def test_graph_compiles_without_error():
    from qa_framework_generator.graph import build_graph
    graph = build_graph()
    assert graph is not None


def test_graph_has_expected_nodes():
    from qa_framework_generator.graph import build_graph
    graph = build_graph()
    node_names = set(graph.nodes.keys())
    expected = {
        "load_config", "requirements", "blueprint", "render_static",
        "generate_pages", "evaluate", "write_files", "static_validate",
        "maven_validate", "review", "repair", "final_report",
    }
    assert expected.issubset(node_names)


# --- route_after_evaluation ---

def test_eval_all_pass_goes_to_write_files():
    from qa_framework_generator.graph import route_after_evaluation
    state = make_state(validation_results=[
        ValidationResult(name="eval_page_object_HomePage", passed=True),
        ValidationResult(name="eval_test_class_SmokeTest", passed=True),
    ])
    assert route_after_evaluation(state) == "write_files"


def test_eval_any_fail_goes_to_repair():
    from qa_framework_generator.graph import route_after_evaluation
    state = make_state(validation_results=[
        ValidationResult(name="eval_page_object_HomePage", passed=True),
        ValidationResult(name="eval_test_class_SmokeTest", passed=False, output="Score: 0.45"),
    ])
    assert route_after_evaluation(state) == "repair"


def test_eval_all_fail_goes_to_repair():
    from qa_framework_generator.graph import route_after_evaluation
    state = make_state(validation_results=[
        ValidationResult(name="eval_page_object_HomePage", passed=False),
        ValidationResult(name="eval_page_object_SearchPage", passed=False),
    ])
    assert route_after_evaluation(state) == "repair"


def test_eval_empty_results_goes_to_write_files():
    from qa_framework_generator.graph import route_after_evaluation
    # deepeval unavailable → evaluate_generated_files returns warning with passed=True
    state = make_state(validation_results=[
        ValidationResult(name="eval_deepeval_unavailable", passed=True),
    ])
    assert route_after_evaluation(state) == "write_files"


def test_eval_non_eval_results_ignored_in_routing():
    from qa_framework_generator.graph import route_after_evaluation
    # non-eval failures don't affect this routing decision
    state = make_state(validation_results=[
        ValidationResult(name="check_pom_xml_exists", passed=False),
        ValidationResult(name="eval_page_object_HomePage", passed=True),
    ])
    assert route_after_evaluation(state) == "write_files"

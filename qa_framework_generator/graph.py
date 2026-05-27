from __future__ import annotations

from langgraph.graph import StateGraph, END

from qa_framework_generator.state import GeneratedFile, GeneratorState, ValidationResult


# ---------------------------------------------------------------------------
# Non-LLM nodes
# ---------------------------------------------------------------------------

def load_config_node(state: GeneratorState) -> dict:
    from qa_framework_generator.config import load_config
    cfg = load_config(state.config_path)
    output_dir = state.output_dir or cfg.output_dir
    return {
        "config_data": cfg.model_dump(),
        "project_name": cfg.project_name,
        "target_package": cfg.package_name,
        "output_dir": output_dir,
    }


def render_static_node(state: GeneratorState) -> dict:
    from qa_framework_generator.config import FrameworkConfig
    from qa_framework_generator.renderer import render_static_templates
    cfg = FrameworkConfig(**state.config_data)
    cfg = cfg.model_copy(update={"output_dir": state.output_dir})
    files = render_static_templates(cfg)
    return {"generated_files": files}


def write_files_node(state: GeneratorState) -> dict:
    from qa_framework_generator.file_writer import write_files
    write_files(state.generated_files, state.output_dir, force=True)
    return {"status": "generated"}


def static_validate_node(state: GeneratorState) -> dict:
    from qa_framework_generator.validators import validate_static
    results = validate_static(state.generated_files)
    return {"validation_results": results, "status": "validating"}


def maven_validate_node(state: GeneratorState) -> dict:
    from qa_framework_generator.validators import validate_maven_compile
    compile_result = validate_maven_compile(state.output_dir)
    results = list(state.validation_results) + [compile_result]
    return {"validation_results": results}


def final_report_node(state: GeneratorState) -> dict:
    from qa_framework_generator.file_writer import write_files
    report_content = _build_report(state)
    report_file = GeneratedFile(path="GENERATION_REPORT.md", content=report_content, kind="markdown")
    write_files([report_file], state.output_dir, force=True, cleanup=False)
    return {"status": "done"}


def _build_report(state: GeneratorState) -> str:
    passed = [r for r in state.validation_results if r.passed]
    failed = [r for r in state.validation_results if not r.passed]
    lines = [
        f"# Generation Report — {state.project_name}",
        "",
        f"**Status:** {state.status}",
        f"**Output:** {state.output_dir}",
        f"**Package:** {state.target_package}",
        f"**Repair attempts:** {state.repair_attempts}",
        "",
        "## Files Generated",
        "",
    ]
    for f in state.generated_files:
        lines.append(f"- `{f.path}`")
    lines += [
        "",
        f"## Validation — {len(passed)} passed / {len(failed)} failed",
        "",
    ]
    for r in state.validation_results:
        icon = "✅" if r.passed else "❌"
        lines.append(f"- {icon} `{r.name}`")
        if not r.passed and r.output:
            lines.append(f"  - {r.output}")
    if state.blueprint:
        lines += [
            "",
            "## Blueprint",
            "",
            f"- Page classes: {state.blueprint.get('page_classes', [])}",
            f"- Test classes: {state.blueprint.get('test_classes', [])}",
            f"- Test groups: {state.blueprint.get('test_groups', [])}",
        ]
        if state.blueprint.get("maven_commands"):
            lines += ["", "**Run commands:**"]
            for cmd in state.blueprint["maven_commands"]:
                lines.append(f"```bash\n{cmd}\n```")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# LLM nodes
# ---------------------------------------------------------------------------

def requirements_node(state: GeneratorState) -> dict:
    from qa_framework_generator.llm import get_openai_chat_model
    from qa_framework_generator.models import RequirementsOutput
    from qa_framework_generator.prompts import build_requirements_prompt

    llm = get_openai_chat_model()
    structured = llm.with_structured_output(RequirementsOutput, method="function_calling")
    prompt = build_requirements_prompt(state.config_data)
    result: RequirementsOutput = structured.invoke(prompt)
    return {"requirements": result.model_dump()}


def blueprint_node(state: GeneratorState) -> dict:
    from qa_framework_generator.llm import get_openai_chat_model
    from qa_framework_generator.models import BlueprintOutput
    from qa_framework_generator.prompts import build_blueprint_prompt

    llm = get_openai_chat_model()
    structured = llm.with_structured_output(BlueprintOutput, method="function_calling")
    prompt = build_blueprint_prompt(state.requirements, state.config_data)
    result: BlueprintOutput = structured.invoke(prompt)
    return {"blueprint": result.model_dump()}


def generate_pages_node(state: GeneratorState) -> dict:
    from qa_framework_generator.config import FrameworkConfig
    from qa_framework_generator.llm import get_openai_chat_model
    from qa_framework_generator.models import PageObjectOutput, TestCaseOutput
    from qa_framework_generator.prompts import build_page_object_prompt, build_test_case_prompt
    from qa_framework_generator.renderer import render_page_object, render_test_class

    cfg = FrameworkConfig(**state.config_data)
    llm = get_openai_chat_model()
    pkg = cfg.package_name
    pkg_path = pkg.replace(".", "/")
    new_files: list[GeneratedFile] = []

    for page in cfg.pages:
        prompt = build_page_object_prompt(page, pkg)
        structured = llm.with_structured_output(PageObjectOutput, method="function_calling")
        output: PageObjectOutput = structured.invoke(prompt)
        content = render_page_object(
            class_name=output.class_name,
            elements=[el.model_dump() for el in output.elements],
            base_package=pkg,
        )
        new_files.append(GeneratedFile(
            path=f"src/test/java/{pkg_path}/pages/{output.class_name}.java",
            content=content,
            kind="java",
        ))

    for flow in cfg.flows:
        prompt = build_test_case_prompt(flow, cfg.pages, pkg)
        structured = llm.with_structured_output(TestCaseOutput, method="function_calling")
        output: TestCaseOutput = structured.invoke(prompt)
        content = render_test_class(
            class_name=output.class_name,
            groups=output.groups,
            steps=[s.model_dump() for s in output.steps],
            assertions=output.assertions,
            base_package=pkg,
        )
        new_files.append(GeneratedFile(
            path=f"src/test/java/{pkg_path}/tests/{output.class_name}.java",
            content=content,
            kind="java",
        ))

    return {"generated_files": list(state.generated_files) + new_files}


def evaluate_node(state: GeneratorState) -> dict:
    from qa_framework_generator.evaluator import evaluate_generated_files

    threshold = state.eval_threshold
    results = evaluate_generated_files(state.generated_files, state.config_data, threshold)
    existing = [r for r in state.validation_results if not r.name.startswith("eval_")]
    return {"validation_results": existing + results}


def review_node(state: GeneratorState) -> dict:
    from qa_framework_generator.llm import get_openai_chat_model
    from qa_framework_generator.models import ReviewOutput
    from qa_framework_generator.prompts import build_review_prompt

    llm = get_openai_chat_model()
    structured = llm.with_structured_output(ReviewOutput, method="function_calling")
    prompt = build_review_prompt(state.generated_files, state.validation_results)
    result: ReviewOutput = structured.invoke(prompt)

    if result.passed:
        return {"status": "done"}

    review_failure = ValidationResult(
        name="review",
        passed=False,
        output="; ".join(result.findings),
        fix_hint="Address review findings listed in output",
    )
    return {"validation_results": list(state.validation_results) + [review_failure]}


def repair_node(state: GeneratorState) -> dict:
    from qa_framework_generator.repair import repair_files

    failures = [r for r in state.validation_results if not r.passed]
    fixed_files = repair_files(state.generated_files, failures)

    from qa_framework_generator.file_writer import write_files
    write_files(fixed_files, state.output_dir, force=True)

    return {
        "generated_files": fixed_files,
        "repair_attempts": state.repair_attempts + 1,
        "status": "repairing",
        "validation_results": [],
    }


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def route_after_evaluation(state: GeneratorState) -> str:
    eval_results = [r for r in state.validation_results if r.name.startswith("eval_")]
    if all(r.passed for r in eval_results):
        return "write_files"
    return "repair"


def route_after_static_validation(state: GeneratorState) -> str:
    if all(r.passed for r in state.validation_results):
        return "maven_validate"
    return "repair"


def route_after_maven_validation(state: GeneratorState) -> str:
    if all(r.passed for r in state.validation_results):
        return "review"
    return "repair"


def route_after_review(state: GeneratorState) -> str:
    if state.status == "done":
        return "final_report"
    return "repair"


def route_after_repair(state: GeneratorState) -> str:
    if state.repair_attempts >= state.max_repair_attempts:
        return "final_report"
    return "static_validate"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph():
    builder = StateGraph(GeneratorState)

    builder.add_node("load_config", load_config_node)
    builder.add_node("requirements", requirements_node)
    builder.add_node("blueprint", blueprint_node)
    builder.add_node("render_static", render_static_node)
    builder.add_node("generate_pages", generate_pages_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("write_files", write_files_node)
    builder.add_node("static_validate", static_validate_node)
    builder.add_node("maven_validate", maven_validate_node)
    builder.add_node("review", review_node)
    builder.add_node("repair", repair_node)
    builder.add_node("final_report", final_report_node)

    builder.set_entry_point("load_config")

    builder.add_edge("load_config", "requirements")
    builder.add_edge("requirements", "blueprint")
    builder.add_edge("blueprint", "render_static")
    builder.add_edge("render_static", "generate_pages")
    builder.add_edge("generate_pages", "evaluate")
    builder.add_edge("write_files", "static_validate")

    builder.add_conditional_edges(
        "evaluate",
        route_after_evaluation,
        {"write_files": "write_files", "repair": "repair"},
    )

    builder.add_conditional_edges(
        "static_validate",
        route_after_static_validation,
        {"maven_validate": "maven_validate", "repair": "repair"},
    )
    builder.add_conditional_edges(
        "maven_validate",
        route_after_maven_validation,
        {"review": "review", "repair": "repair"},
    )
    builder.add_conditional_edges(
        "review",
        route_after_review,
        {"final_report": "final_report", "repair": "repair"},
    )
    builder.add_conditional_edges(
        "repair",
        route_after_repair,
        {"static_validate": "static_validate", "final_report": "final_report"},
    )

    builder.add_edge("final_report", END)

    return builder.compile()

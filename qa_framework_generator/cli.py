from __future__ import annotations

from pathlib import Path
import typer

app = typer.Typer(
    name="qa-framework-generator",
    help="Generate Java Selenium + TestNG automation frameworks using LangGraph.",
)


@app.command()
def generate(
    config: Path = typer.Option(..., "--config", help="Path to YAML config file"),
    output: str = typer.Option(
        "selenium-testng-framework-output", "--output", help="Output directory"
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing generated files"),
    skip_llm: bool = typer.Option(
        False, "--skip-llm", help="Skip LLM nodes — render static templates only (fast, no API key needed)"
    ),
    eval_threshold: float = typer.Option(
        0.7, "--eval-threshold", help="DeepEval minimum score (0.0–1.0) for page objects and test classes"
    ),
):
    """Generate a Java Selenium + TestNG framework from a YAML config."""
    typer.echo(f"Loading config: {config}")

    if skip_llm:
        _generate_static(str(config), output, force)
    else:
        _generate_graph(str(config), output, eval_threshold)


def _generate_static(config_path: str, output: str, force: bool) -> None:
    from qa_framework_generator.config import load_config
    from qa_framework_generator.renderer import render_static_templates
    from qa_framework_generator.file_writer import write_files

    cfg = load_config(config_path)
    cfg = cfg.model_copy(update={"output_dir": output})

    typer.echo(f"Project: {cfg.project_name}  |  Package: {cfg.package_name}")
    typer.echo(f"Output:  {output}")
    typer.echo("Mode:    static-only (--skip-llm)")

    files = render_static_templates(cfg)
    result = write_files(files, output, force=force)

    typer.echo(f"Written:  {len(result.written)} files")
    if result.deleted:
        typer.echo(f"Deleted:  {len(result.deleted)} stale files")
    if result.skipped:
        typer.echo(f"Skipped:  {len(result.skipped)} files (use --force to overwrite)")


def _generate_graph(config_path: str, output: str, eval_threshold: float = 0.7) -> None:
    from qa_framework_generator.graph import build_graph
    from qa_framework_generator.state import GeneratorState

    graph = build_graph()
    initial = GeneratorState(config_path=config_path, output_dir=output, eval_threshold=eval_threshold)

    typer.echo("Running LangGraph pipeline...")
    result = graph.invoke(initial)
    final = GeneratorState.model_validate(result)

    typer.echo(f"Project: {final.project_name}  |  Package: {final.target_package}")
    typer.echo(f"Output:  {final.output_dir}")
    typer.echo(f"Status:  {final.status}")
    typer.echo(f"Written: {len(final.generated_files)} files")
    typer.echo(f"Repairs: {final.repair_attempts}")

    passed = sum(1 for r in final.validation_results if r.passed)
    failed = sum(1 for r in final.validation_results if not r.passed)
    typer.echo(f"Checks:  {passed} passed / {failed} failed")

    if final.status == "done":
        typer.echo("Generation report: GENERATION_REPORT.md")
    else:
        typer.echo("WARNING: pipeline did not reach 'done' — check GENERATION_REPORT.md")
        failures = [r for r in final.validation_results if not r.passed]
        for f in failures:
            typer.echo(f"  ✗ {f.name}: {f.output}")

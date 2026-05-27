"""End-to-end: render static templates → write to temp dir → assert files exist."""
import pytest
from pathlib import Path
from typer.testing import CliRunner

FIXTURE_CONFIG = Path(__file__).parent / "fixtures" / "minimal_config.yaml"
EXAMPLES_MINIMAL = Path(__file__).parent.parent / "examples" / "minimal.yaml"


def _generate(config_path: Path, tmp_path: Path):
    from qa_framework_generator.config import load_config
    from qa_framework_generator.renderer import render_static_templates
    from qa_framework_generator.file_writer import write_files
    config = load_config(str(config_path))
    files = render_static_templates(config)
    write_files(files, str(tmp_path), force=True)
    return config


# --- file presence ---

def test_pom_xml_exists(tmp_path):
    _generate(FIXTURE_CONFIG, tmp_path)
    assert (tmp_path / "pom.xml").exists()


def test_driver_factory_exists(tmp_path):
    config = _generate(FIXTURE_CONFIG, tmp_path)
    pkg = config.package_name.replace(".", "/")
    assert (tmp_path / f"src/main/java/{pkg}/driver/DriverFactory.java").exists()


def test_base_test_exists(tmp_path):
    config = _generate(FIXTURE_CONFIG, tmp_path)
    pkg = config.package_name.replace(".", "/")
    assert (tmp_path / f"src/test/java/{pkg}/base/BaseTest.java").exists()


def test_base_page_exists(tmp_path):
    config = _generate(FIXTURE_CONFIG, tmp_path)
    pkg = config.package_name.replace(".", "/")
    assert (tmp_path / f"src/main/java/{pkg}/base/BasePage.java").exists()


def test_testng_xml_exists(tmp_path):
    _generate(FIXTURE_CONFIG, tmp_path)
    assert (tmp_path / "src/test/resources/testng.xml").exists()


def test_readme_exists(tmp_path):
    _generate(FIXTURE_CONFIG, tmp_path)
    assert (tmp_path / "README.md").exists()


def test_github_actions_exists(tmp_path):
    _generate(FIXTURE_CONFIG, tmp_path)
    assert (tmp_path / ".github/workflows/ui-tests.yml").exists()


def test_gitignore_exists(tmp_path):
    _generate(FIXTURE_CONFIG, tmp_path)
    assert (tmp_path / ".gitignore").exists()


def test_env_properties_per_environment(tmp_path):
    _generate(FIXTURE_CONFIG, tmp_path)
    assert (tmp_path / "src/test/resources/env/qa.properties").exists()


# --- content checks ---

def test_pom_contains_project_name(tmp_path):
    config = _generate(FIXTURE_CONFIG, tmp_path)
    content = (tmp_path / "pom.xml").read_text()
    assert config.project_name in content


def test_testng_xml_references_package(tmp_path):
    config = _generate(FIXTURE_CONFIG, tmp_path)
    content = (tmp_path / "src/test/resources/testng.xml").read_text()
    assert config.package_name in content


def test_readme_has_mvn_commands(tmp_path):
    _generate(FIXTURE_CONFIG, tmp_path)
    content = (tmp_path / "README.md").read_text()
    assert "mvn" in content


def test_env_properties_has_base_url(tmp_path):
    _generate(FIXTURE_CONFIG, tmp_path)
    content = (tmp_path / "src/test/resources/env/qa.properties").read_text()
    assert "https://example.com" in content


def test_driver_factory_uses_thread_local(tmp_path):
    config = _generate(FIXTURE_CONFIG, tmp_path)
    pkg = config.package_name.replace(".", "/")
    content = (tmp_path / f"src/main/java/{pkg}/driver/DriverFactory.java").read_text()
    assert "ThreadLocal" in content


# --- CLI integration ---

def test_cli_generate_exits_zero(tmp_path):
    from qa_framework_generator.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["--config", str(FIXTURE_CONFIG),
                                 "--output", str(tmp_path), "--force", "--skip-llm"])
    assert result.exit_code == 0, result.output


def test_cli_generate_creates_pom_xml(tmp_path):
    from qa_framework_generator.cli import app
    runner = CliRunner()
    runner.invoke(app, ["--config", str(FIXTURE_CONFIG),
                        "--output", str(tmp_path), "--force", "--skip-llm"])
    assert (tmp_path / "pom.xml").exists()


def test_cli_generate_reports_written_count(tmp_path):
    from qa_framework_generator.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["--config", str(FIXTURE_CONFIG),
                                 "--output", str(tmp_path), "--force", "--skip-llm"])
    assert "Written:" in result.output


def test_cli_generate_with_examples_minimal(tmp_path):
    from qa_framework_generator.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["--config", str(EXAMPLES_MINIMAL),
                                 "--output", str(tmp_path), "--force", "--skip-llm"])
    assert result.exit_code == 0
    assert (tmp_path / "pom.xml").exists()

import pytest
import yaml
from pathlib import Path


def test_yaml_config_loads(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "project_name": "my-project",
        "package_name": "com.example.qa",
    }))
    from qa_framework_generator.config import load_config
    config = load_config(str(config_file))
    assert config.project_name == "my-project"
    assert config.package_name == "com.example.qa"


def test_missing_project_name_fails(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"package_name": "com.example.qa"}))
    from qa_framework_generator.config import load_config
    with pytest.raises(Exception):
        load_config(str(config_file))


def test_default_package_applied(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"project_name": "test-project"}))
    from qa_framework_generator.config import load_config
    config = load_config(str(config_file))
    assert config.package_name == "com.generated.qa"


def test_default_output_dir_applied(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"project_name": "test-project"}))
    from qa_framework_generator.config import load_config
    config = load_config(str(config_file))
    assert config.output_dir == "selenium-testng-framework-output"


def test_full_ecommerce_demo_config_loads(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "project_name": "ecommerce-demo-automation",
        "package_name": "com.generated.demoqa",
        "environments": {
            "qa": {"base_url": "https://qa.example.com"},
        },
        "browsers": ["chrome", "firefox"],
        "headless_default": True,
        "parallel": {"enabled": True, "thread_count": 3},
        "pages": [{
            "name": "HomePage",
            "path": "/",
            "elements": [{"name": "searchInput", "by": "css", "value": "input[type='search']"}],
        }],
        "flows": [{
            "name": "SmokeTest",
            "groups": ["smoke"],
            "steps": [{"open": "HomePage"}],
        }],
    }))
    from qa_framework_generator.config import load_config
    config = load_config(str(config_file))
    assert config.project_name == "ecommerce-demo-automation"
    assert config.environments["qa"].base_url == "https://qa.example.com"
    assert "chrome" in config.browsers
    assert config.pages[0].name == "HomePage"
    assert config.flows[0].groups == ["smoke"]


def test_cli_exposes_generate():
    from qa_framework_generator.cli import app
    from typer.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert "generate" in result.output

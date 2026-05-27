from __future__ import annotations

import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from qa_framework_generator.config import FrameworkConfig
from qa_framework_generator.state import GeneratedFile

_TEMPLATES_DIR = Path(__file__).parent / "templates" / "java"

_BY_MAP: dict[str, str] = {
    "css": "cssSelector",
    "class": "className",
    "xpath": "xpath",
    "id": "id",
    "name": "name",
    "tagname": "tagName",
    "linktext": "linkText",
    "partiallinktext": "partialLinkText",
}


def _camel_to_const(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.upper()


def _lower_first(s: str) -> str:
    return s[0].lower() + s[1:] if s else s


def _upper_first(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def _jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    env.filters["to_by"] = lambda by: _BY_MAP.get(by.lower(), by)
    env.filters["to_const"] = _camel_to_const
    env.filters["lower_first"] = _lower_first
    env.filters["upper_first"] = _upper_first
    return env


def _render(env: Environment, template_name: str, ctx: dict) -> str:
    return env.get_template(template_name).render(**ctx)


def render_static_templates(config: FrameworkConfig) -> list[GeneratedFile]:
    env = _jinja_env()
    pkg = config.package_name
    pkg_path = pkg.replace(".", "/")

    ctx = {
        "config": config,
        "project_name": config.project_name,
        "base_package": pkg,
        "base_package_path": pkg_path,
        "parallel": config.parallel,
        "environments": config.environments,
        "browsers": config.browsers,
        "headless_default": config.headless_default,
    }

    main = f"src/main/java/{pkg_path}"
    test = f"src/test/java/{pkg_path}"

    files: list[GeneratedFile] = []

    # Build files
    files.append(GeneratedFile(path="pom.xml", kind="xml",
                               content=_render(env, "pom.xml.j2", ctx)))
    files.append(GeneratedFile(path=".gitignore", kind="text",
                               content=_render(env, "gitignore.j2", ctx)))
    files.append(GeneratedFile(path="README.md", kind="markdown",
                               content=_render(env, "README.md.j2", ctx)))
    files.append(GeneratedFile(path=".github/workflows/ui-tests.yml", kind="yaml",
                               content=_render(env, "github-actions.yml.j2", ctx)))

    # TestNG suite
    files.append(GeneratedFile(path="src/test/resources/testng.xml", kind="xml",
                               content=_render(env, "testng.xml.j2", ctx)))

    # Environment properties (one per configured environment)
    for env_name, env_config in config.environments.items():
        env_ctx = {**ctx, "env_config": env_config}
        files.append(GeneratedFile(
            path=f"src/test/resources/env/{env_name}.properties",
            kind="properties",
            content=_render(env, "env.properties.j2", env_ctx),
        ))

    # Framework infrastructure — main sources
    for path, tpl in [
        (f"{main}/driver/DriverFactory.java", "DriverFactory.java.j2"),
        (f"{main}/base/BasePage.java", "BasePage.java.j2"),
        (f"{main}/config/ConfigLoader.java", "ConfigLoader.java.j2"),
        (f"{main}/config/EnvConfig.java", "EnvConfig.java.j2"),
        (f"{main}/listeners/ExtentManager.java", "ExtentManager.java.j2"),
        (f"{main}/listeners/ExtentTestManager.java", "ExtentTestManager.java.j2"),
        (f"{main}/utils/ScreenshotUtil.java", "ScreenshotUtil.java.j2"),
    ]:
        files.append(GeneratedFile(path=path, kind="java", content=_render(env, tpl, ctx)))

    # Test sources — TestNG-dependent classes and test base
    for path, tpl in [
        (f"{test}/base/BaseTest.java", "BaseTest.java.j2"),
        (f"{test}/listeners/TestListener.java", "TestListener.java.j2"),
        (f"{test}/listeners/ExtentReportListener.java", "ExtentReportListener.java.j2"),
        (f"{test}/retry/RetryAnalyzer.java", "RetryAnalyzer.java.j2"),
        (f"{test}/retry/RetryTransformer.java", "RetryTransformer.java.j2"),
    ]:
        files.append(GeneratedFile(path=path, kind="java", content=_render(env, tpl, ctx)))

    return files


def render_page_object(
    class_name: str,
    elements: list[dict],
    base_package: str,
) -> str:
    env = _jinja_env()
    ctx = {
        "class_name": class_name,
        "elements": elements,
        "base_package": base_package,
    }
    return _render(env, "PageObject.java.j2", ctx)


def render_test_class(
    class_name: str,
    groups: list[str],
    steps: list[dict],
    assertions: list[str],
    base_package: str,
) -> str:
    env = _jinja_env()

    pages_seen: list[str] = []
    current_page: str | None = None
    step_lines: list[str] = []
    page_vars: list[tuple[str, str]] = []

    for step in steps:
        action = step.get("action", "")
        target = step.get("target") or ""
        value = step.get("value") or ""

        if action == "open" and target:
            if target not in pages_seen:
                pages_seen.append(target)
                var = _lower_first(target)
                page_vars.append((target, var))
            current_page = target
        elif action == "click" and target:
            var = _lower_first(current_page) if current_page else "page"
            method = "click" + target[0].upper() + target[1:]
            step_lines.append(f"{var}.{method}();")
        elif action == "type" and target:
            var = _lower_first(current_page) if current_page else "page"
            method = "type" + target[0].upper() + target[1:]
            step_lines.append(f'{var}.{method}("{value}");')

    method_name = _lower_first(class_name) + "Test"

    ctx = {
        "class_name": class_name,
        "groups": groups,
        "pages_used": pages_seen,
        "page_vars": page_vars,
        "step_lines": step_lines,
        "assertions": [a.rstrip(";") for a in assertions],
        "method_name": method_name,
        "base_package": base_package,
    }
    return _render(env, "TestClass.java.j2", ctx)

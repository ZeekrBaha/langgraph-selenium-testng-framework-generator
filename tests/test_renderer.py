import pytest
from qa_framework_generator.config import FrameworkConfig, EnvConfig, ParallelConfig


def make_config(**kwargs) -> FrameworkConfig:
    defaults = {
        "project_name": "test-automation",
        "package_name": "com.example.qa",
    }
    defaults.update(kwargs)
    return FrameworkConfig(**defaults)


def find_file(files, path_fragment: str):
    return next((f for f in files if path_fragment in f.path), None)


def test_renderer_returns_list_of_generated_files():
    from qa_framework_generator.renderer import render_static_templates
    from qa_framework_generator.state import GeneratedFile
    config = make_config()
    files = render_static_templates(config)
    assert isinstance(files, list)
    assert all(isinstance(f, GeneratedFile) for f in files)


def test_pom_xml_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    pom = find_file(files, "pom.xml")
    assert pom is not None
    assert pom.kind == "xml"
    assert "<artifactId>" in pom.content


def test_pom_xml_contains_project_name():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(project_name="my-automation")
    files = render_static_templates(config)
    pom = find_file(files, "pom.xml")
    assert "my-automation" in pom.content


def test_pom_xml_contains_selenium_dependency():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    pom = find_file(files, "pom.xml")
    assert "selenium" in pom.content.lower()


def test_pom_xml_contains_testng_dependency():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    pom = find_file(files, "pom.xml")
    assert "testng" in pom.content.lower()


def test_base_test_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    base_test = find_file(files, "BaseTest.java")
    assert base_test is not None
    assert base_test.kind == "java"


def test_base_test_has_correct_package():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(package_name="com.example.qa")
    files = render_static_templates(config)
    base_test = find_file(files, "BaseTest.java")
    assert "package com.example.qa" in base_test.content


def test_base_test_path_uses_package_as_directory():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(package_name="com.example.qa")
    files = render_static_templates(config)
    base_test = find_file(files, "BaseTest.java")
    assert "com/example/qa" in base_test.path


def test_driver_factory_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    driver = find_file(files, "DriverFactory.java")
    assert driver is not None
    assert driver.kind == "java"


def test_driver_factory_has_correct_package():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(package_name="com.acme.qa")
    files = render_static_templates(config)
    driver = find_file(files, "DriverFactory.java")
    assert "package com.acme.qa" in driver.content


def test_driver_factory_uses_thread_local():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    driver = find_file(files, "DriverFactory.java")
    assert "ThreadLocal" in driver.content


def test_testng_xml_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    testng = find_file(files, "testng.xml")
    assert testng is not None
    assert testng.kind == "xml"
    assert testng.path == "src/test/resources/testng.xml"


def test_testng_xml_references_correct_package():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(package_name="com.example.qa")
    files = render_static_templates(config)
    testng = find_file(files, "testng.xml")
    assert "com.example.qa" in testng.content


def test_parallel_config_reflected_in_testng_xml():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(parallel=ParallelConfig(enabled=True, thread_count=5))
    files = render_static_templates(config)
    testng = find_file(files, "testng.xml")
    assert "5" in testng.content


def test_different_packages_produce_different_paths():
    from qa_framework_generator.renderer import render_static_templates
    config_a = make_config(package_name="com.alpha.qa")
    config_b = make_config(package_name="com.beta.qa")
    files_a = render_static_templates(config_a)
    files_b = render_static_templates(config_b)
    paths_a = {f.path for f in files_a}
    paths_b = {f.path for f in files_b}
    assert paths_a != paths_b


# --- Task 4: full template set ---

def test_base_page_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "BasePage.java")
    assert f is not None and f.kind == "java"
    assert "WebDriverWait" in f.content


def test_base_page_has_correct_package():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(package_name="com.example.qa")
    files = render_static_templates(config)
    f = find_file(files, "BasePage.java")
    assert "package com.example.qa" in f.content


def test_config_loader_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "ConfigLoader.java")
    assert f is not None and "getBaseUrl" in f.content


def test_env_config_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "EnvConfig.java")
    assert f is not None and f.kind == "java"


def test_retry_analyzer_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "RetryAnalyzer.java")
    assert f is not None and "IRetryAnalyzer" in f.content


def test_retry_transformer_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "RetryTransformer.java")
    assert f is not None and "IAnnotationTransformer" in f.content


def test_screenshot_util_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "ScreenshotUtil.java")
    assert f is not None and "TakesScreenshot" in f.content


def test_test_listener_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "TestListener.java")
    assert f is not None and "ITestListener" in f.content


def test_extent_manager_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "ExtentManager.java")
    assert f is not None and "ExtentReports" in f.content


def test_extent_test_manager_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "ExtentTestManager.java")
    assert f is not None and "ThreadLocal" in f.content


def test_extent_report_listener_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "ExtentReportListener.java")
    assert f is not None and "ISuiteListener" in f.content


def test_github_actions_workflow_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, "ui-tests.yml")
    assert f is not None and f.kind == "yaml"
    assert "maven" in f.content.lower()
    assert "java" in f.content.lower()


def test_gitignore_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config()
    files = render_static_templates(config)
    f = find_file(files, ".gitignore")
    assert f is not None
    assert "target/" in f.content


def test_readme_is_generated():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(project_name="my-automation")
    files = render_static_templates(config)
    f = find_file(files, "README.md")
    assert f is not None and f.kind == "markdown"
    assert "mvn" in f.content


def test_env_properties_generated_per_environment():
    from qa_framework_generator.renderer import render_static_templates
    from qa_framework_generator.config import EnvConfig
    config = make_config(environments={
        "dev": EnvConfig(base_url="https://dev.example.com"),
        "qa": EnvConfig(base_url="https://qa.example.com"),
    })
    files = render_static_templates(config)
    paths = {f.path for f in files}
    assert "src/test/resources/env/dev.properties" in paths
    assert "src/test/resources/env/qa.properties" in paths


def test_env_properties_contains_base_url():
    from qa_framework_generator.renderer import render_static_templates
    from qa_framework_generator.config import EnvConfig
    config = make_config(environments={
        "qa": EnvConfig(base_url="https://qa.example.com"),
    })
    files = render_static_templates(config)
    f = find_file(files, "qa.properties")
    assert f is not None and "https://qa.example.com" in f.content


def test_all_java_files_have_package_declaration():
    from qa_framework_generator.renderer import render_static_templates
    config = make_config(package_name="com.test.qa")
    files = render_static_templates(config)
    java_files = [f for f in files if f.kind == "java"]
    for f in java_files:
        assert "package com.test.qa" in f.content, f"Missing package in {f.path}"

import pytest
from qa_framework_generator.state import GeneratedFile


def make_file(path: str, content: str = "", kind: str = "text") -> GeneratedFile:
    return GeneratedFile(path=path, content=content, kind=kind)


def find_result(results, name_fragment: str):
    return next((r for r in results if name_fragment in r.name), None)


def failed_results(results):
    return [r for r in results if not r.passed]


# --- pom.xml presence ---

def test_pom_present_passes():
    from qa_framework_generator.validators import validate_static
    files = [make_file("pom.xml", "<project><modelVersion>4.0.0</modelVersion></project>", "xml")]
    results = validate_static(files)
    r = find_result(results, "pom")
    assert r is not None and r.passed


def test_pom_missing_fails():
    from qa_framework_generator.validators import validate_static
    files = [make_file("README.md", "hi", "markdown")]
    results = validate_static(files)
    r = find_result(results, "pom")
    assert r is not None and not r.passed


# --- XML validity ---

def test_valid_xml_passes():
    from qa_framework_generator.validators import validate_static
    files = [make_file("config.xml", "<root><child/></root>", "xml")]
    results = validate_static(files)
    xml_fails = [r for r in failed_results(results) if r.name.startswith("check_xml_")]
    assert not xml_fails


def test_invalid_xml_fails():
    from qa_framework_generator.validators import validate_static
    files = [make_file("config.xml", "<root><unclosed>", "xml")]
    results = validate_static(files)
    xml_fails = [r for r in failed_results(results) if r.name.startswith("check_xml_")]
    assert xml_fails


def test_xml_with_doctype_parses_ok():
    from qa_framework_generator.validators import validate_static
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<!DOCTYPE suite SYSTEM "https://testng.org/testng-1.0.dtd">\n'
           '<suite name="Test"></suite>')
    files = [make_file("testng.xml", xml, "xml")]
    results = validate_static(files)
    xml_fails = [r for r in failed_results(results) if r.name.startswith("check_xml_")]
    assert not xml_fails


# --- Unresolved Jinja markers ---

def test_clean_content_has_no_jinja_fail():
    from qa_framework_generator.validators import validate_static
    files = [make_file("Foo.java", "package com.example; class Foo {}", "java")]
    results = validate_static(files)
    jinja_fails = [r for r in failed_results(results) if "jinja" in r.name]
    assert not jinja_fails


def test_unresolved_jinja_in_xml_fails():
    from qa_framework_generator.validators import validate_static
    files = [make_file("config.xml", "<root>{{ project_name }}</root>", "xml")]
    results = validate_static(files)
    jinja_fails = [r for r in failed_results(results) if "jinja" in r.name]
    assert jinja_fails


def test_unresolved_jinja_in_java_fails():
    from qa_framework_generator.validators import validate_static
    files = [make_file("Foo.java", "package {{ base_package }};", "java")]
    results = validate_static(files)
    jinja_fails = [r for r in failed_results(results) if "jinja" in r.name]
    assert jinja_fails


# --- Thread.sleep ---

def test_thread_sleep_in_java_fails():
    from qa_framework_generator.validators import validate_static
    files = [make_file("Test.java", "Thread.sleep(2000);", "java")]
    results = validate_static(files)
    sleep_fails = [r for r in failed_results(results) if "sleep" in r.name]
    assert sleep_fails


def test_no_thread_sleep_passes():
    from qa_framework_generator.validators import validate_static
    files = [make_file("Test.java", "WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));", "java")]
    results = validate_static(files)
    sleep_fails = [r for r in failed_results(results) if "sleep" in r.name]
    assert not sleep_fails


# --- TestNG groups ---

def test_test_without_groups_fails():
    from qa_framework_generator.validators import validate_static
    content = "@Test\npublic void myTest() {}"
    files = [make_file("src/test/java/tests/MyTest.java", content, "java")]
    results = validate_static(files)
    group_fails = [r for r in failed_results(results) if "groups" in r.name]
    assert group_fails


def test_test_with_groups_passes():
    from qa_framework_generator.validators import validate_static
    content = '@Test(groups = {"smoke"})\npublic void myTest() {}'
    files = [make_file("src/test/java/tests/MyTest.java", content, "java")]
    results = validate_static(files)
    group_fails = [r for r in failed_results(results) if "groups" in r.name]
    assert not group_fails


# --- Placeholder locators ---

def test_placeholder_locator_fails_when_not_allowed():
    from qa_framework_generator.validators import validate_static
    files = [make_file("Page.java", "By.xpath(\"TODO_REPLACE_LOCATOR\")", "java")]
    results = validate_static(files, allow_placeholder_locators=False)
    placeholder_fails = [r for r in failed_results(results) if "placeholder" in r.name]
    assert placeholder_fails


def test_placeholder_locator_passes_when_allowed():
    from qa_framework_generator.validators import validate_static
    files = [make_file("Page.java", "By.xpath(\"TODO_REPLACE_LOCATOR\")", "java")]
    results = validate_static(files, allow_placeholder_locators=True)
    placeholder_fails = [r for r in failed_results(results) if "placeholder" in r.name]
    assert not placeholder_fails


# --- No build artifacts ---

def test_target_dir_path_fails():
    from qa_framework_generator.validators import validate_static
    files = [make_file("target/classes/Foo.class", "", "text")]
    results = validate_static(files)
    artifact_fails = [r for r in failed_results(results) if "artifact" in r.name]
    assert artifact_fails


def test_bin_dir_path_fails():
    from qa_framework_generator.validators import validate_static
    files = [make_file("bin/Foo.class", "", "text")]
    results = validate_static(files)
    artifact_fails = [r for r in failed_results(results) if "artifact" in r.name]
    assert artifact_fails


def test_normal_path_does_not_fail_artifact_check():
    from qa_framework_generator.validators import validate_static
    files = [make_file("src/main/java/Foo.java", "class Foo {}", "java")]
    results = validate_static(files)
    artifact_fails = [r for r in failed_results(results) if "artifact" in r.name]
    assert not artifact_fails

import pytest
from pathlib import Path
from qa_framework_generator.state import GeneratedFile


def make_file(path: str, content: str = "hello", kind: str = "text") -> GeneratedFile:
    return GeneratedFile(path=path, content=content, kind=kind)


# --- Writing files ---

def test_files_are_written_to_output_dir(tmp_path):
    from qa_framework_generator.file_writer import write_files
    files = [make_file("pom.xml", "<project/>", "xml")]
    result = write_files(files, str(tmp_path))
    assert (tmp_path / "pom.xml").exists()
    assert len(result.written) == 1


def test_subdirectories_are_created(tmp_path):
    from qa_framework_generator.file_writer import write_files
    files = [make_file("src/test/java/com/example/BaseTest.java", "// code", "java")]
    write_files(files, str(tmp_path))
    assert (tmp_path / "src/test/java/com/example/BaseTest.java").exists()


def test_multiple_files_written(tmp_path):
    from qa_framework_generator.file_writer import write_files
    files = [
        make_file("pom.xml", "<project/>", "xml"),
        make_file("README.md", "# Hi", "markdown"),
        make_file("src/Foo.java", "class Foo {}", "java"),
    ]
    result = write_files(files, str(tmp_path))
    assert len(result.written) == 3
    assert len(result.skipped) == 0


# --- Overwrite safety ---

def test_non_generated_file_is_not_overwritten(tmp_path):
    from qa_framework_generator.file_writer import write_files
    target = tmp_path / "pom.xml"
    target.write_text("user content — hand-crafted")

    files = [make_file("pom.xml", "<generated/>", "xml")]
    result = write_files(files, str(tmp_path), force=False)

    assert target.read_text() == "user content — hand-crafted"
    assert len(result.skipped) == 1
    assert len(result.written) == 0


def test_force_overwrites_non_generated_file(tmp_path):
    from qa_framework_generator.file_writer import write_files
    target = tmp_path / "pom.xml"
    target.write_text("user content")

    files = [make_file("pom.xml", "<generated/>", "xml")]
    result = write_files(files, str(tmp_path), force=True)

    assert "<generated/>" in target.read_text()
    assert len(result.written) == 1


def test_previously_generated_file_is_overwritten_without_force(tmp_path):
    from qa_framework_generator.file_writer import write_files, GENERATED_MARKER
    target = tmp_path / "pom.xml"
    target.write_text(f"<!-- {GENERATED_MARKER} -->\n<old/>")

    files = [make_file("pom.xml", "<new/>", "xml")]
    result = write_files(files, str(tmp_path), force=False)

    assert "<new/>" in target.read_text()
    assert len(result.written) == 1
    assert len(result.skipped) == 0


# --- Generated header ---

def test_java_file_has_generated_header(tmp_path):
    from qa_framework_generator.file_writer import write_files, GENERATED_MARKER
    files = [make_file("Foo.java", "class Foo {}", "java")]
    write_files(files, str(tmp_path))
    content = (tmp_path / "Foo.java").read_text()
    assert GENERATED_MARKER in content


def test_xml_file_has_generated_header(tmp_path):
    from qa_framework_generator.file_writer import write_files, GENERATED_MARKER
    files = [make_file("config.xml", "<root/>", "xml")]
    write_files(files, str(tmp_path))
    content = (tmp_path / "config.xml").read_text()
    assert GENERATED_MARKER in content


def test_properties_file_has_generated_header(tmp_path):
    from qa_framework_generator.file_writer import write_files, GENERATED_MARKER
    files = [make_file("dev.properties", "base.url=http://dev", "properties")]
    write_files(files, str(tmp_path))
    content = (tmp_path / "dev.properties").read_text()
    assert GENERATED_MARKER in content


def test_yaml_file_has_generated_header(tmp_path):
    from qa_framework_generator.file_writer import write_files, GENERATED_MARKER
    files = [make_file("workflow.yml", "name: CI", "yaml")]
    write_files(files, str(tmp_path))
    content = (tmp_path / "workflow.yml").read_text()
    assert GENERATED_MARKER in content


def test_write_result_has_correct_paths(tmp_path):
    from qa_framework_generator.file_writer import write_files
    files = [make_file("a.java", "class A {}", "java"), make_file("b.java", "class B {}", "java")]
    result = write_files(files, str(tmp_path))
    written_names = {Path(p).name for p in result.written}
    assert "a.java" in written_names
    assert "b.java" in written_names


# --- Stale file cleanup ---

def test_stale_generated_file_is_deleted(tmp_path):
    from qa_framework_generator.file_writer import write_files, GENERATED_MARKER
    stale = tmp_path / "src" / "OldClass.java"
    stale.parent.mkdir(parents=True)
    stale.write_text(f"// {GENERATED_MARKER}\nclass OldClass {{}}")

    files = [make_file("pom.xml", "<project/>", "xml")]
    result = write_files(files, str(tmp_path))

    assert not stale.exists()
    assert "src/OldClass.java" in result.deleted


def test_non_generated_stale_file_is_not_deleted(tmp_path):
    from qa_framework_generator.file_writer import write_files
    user_file = tmp_path / "MyCustomClass.java"
    user_file.write_text("class MyCustomClass {} // hand-crafted")

    files = [make_file("pom.xml", "<project/>", "xml")]
    write_files(files, str(tmp_path))

    assert user_file.exists()


def test_stale_empty_directories_are_pruned(tmp_path):
    from qa_framework_generator.file_writer import write_files, GENERATED_MARKER
    stale_dir = tmp_path / "src" / "old" / "pkg"
    stale_dir.mkdir(parents=True)
    stale_file = stale_dir / "OldFile.java"
    stale_file.write_text(f"// {GENERATED_MARKER}\nclass OldFile {{}}")

    files = [make_file("pom.xml", "<project/>", "xml")]
    write_files(files, str(tmp_path))

    assert not stale_file.exists()
    assert not stale_dir.exists()


def test_new_files_are_not_deleted(tmp_path):
    from qa_framework_generator.file_writer import write_files
    files = [
        make_file("pom.xml", "<project/>", "xml"),
        make_file("src/Foo.java", "class Foo {}", "java"),
    ]
    result = write_files(files, str(tmp_path))

    assert (tmp_path / "pom.xml").exists()
    assert (tmp_path / "src/Foo.java").exists()
    assert len(result.deleted) == 0


def test_write_result_deleted_field_exists(tmp_path):
    from qa_framework_generator.file_writer import write_files
    files = [make_file("pom.xml", "<project/>", "xml")]
    result = write_files(files, str(tmp_path))
    assert hasattr(result, "deleted")

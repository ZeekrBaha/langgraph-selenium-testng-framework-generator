import pytest
from unittest.mock import patch, MagicMock


def make_proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


# --- compile ---

def test_compile_command_is_correct():
    from qa_framework_generator.validators import validate_maven_compile
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = make_proc(0)
        validate_maven_compile("/tmp/output")
        assert mock_run.call_args[0][0] == ["mvn", "-q", "-DskipTests", "compile"]


def test_compile_uses_output_dir_as_cwd():
    from qa_framework_generator.validators import validate_maven_compile
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = make_proc(0)
        validate_maven_compile("/tmp/output")
        assert mock_run.call_args[1]["cwd"] == "/tmp/output"


def test_compile_success_returns_passed():
    from qa_framework_generator.validators import validate_maven_compile
    with patch("subprocess.run", return_value=make_proc(0)):
        result = validate_maven_compile("/tmp/output")
    assert result.passed
    assert result.name == "maven_compile"


def test_compile_failure_returns_failed():
    from qa_framework_generator.validators import validate_maven_compile
    with patch("subprocess.run", return_value=make_proc(1, stderr="BUILD FAILURE")):
        result = validate_maven_compile("/tmp/output")
    assert not result.passed
    assert "BUILD FAILURE" in result.output


def test_compile_captures_stdout_and_stderr():
    from qa_framework_generator.validators import validate_maven_compile
    with patch("subprocess.run", return_value=make_proc(1, stdout="INFO compiling", stderr="ERROR: bad")):
        result = validate_maven_compile("/tmp/output")
    assert "INFO compiling" in result.output
    assert "ERROR: bad" in result.output


def test_compile_has_fix_hint_on_failure():
    from qa_framework_generator.validators import validate_maven_compile
    with patch("subprocess.run", return_value=make_proc(1, stderr="compile error")):
        result = validate_maven_compile("/tmp/output")
    assert result.fix_hint


# --- smoke ---

def test_smoke_command_is_correct():
    from qa_framework_generator.validators import validate_maven_smoke
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = make_proc(0)
        validate_maven_smoke("/tmp/output")
        assert mock_run.call_args[0][0] == ["mvn", "-q", "test", "-Dgroups=smoke", "-Dheadless=true"]


def test_smoke_uses_output_dir_as_cwd():
    from qa_framework_generator.validators import validate_maven_smoke
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = make_proc(0)
        validate_maven_smoke("/tmp/output")
        assert mock_run.call_args[1]["cwd"] == "/tmp/output"


def test_smoke_success_returns_passed():
    from qa_framework_generator.validators import validate_maven_smoke
    with patch("subprocess.run", return_value=make_proc(0)):
        result = validate_maven_smoke("/tmp/output")
    assert result.passed
    assert result.name == "maven_smoke"


def test_smoke_failure_returns_failed():
    from qa_framework_generator.validators import validate_maven_smoke
    with patch("subprocess.run", return_value=make_proc(1, stderr="Tests run: 1, Failures: 1")):
        result = validate_maven_smoke("/tmp/output")
    assert not result.passed
    assert "Failures" in result.output

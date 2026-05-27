import pytest


# --- Schema: PageObjectOutput ---

def test_page_object_output_valid():
    from qa_framework_generator.models import PageObjectOutput, LocatorDef
    out = PageObjectOutput(
        class_name="HomePage",
        package_name="com.example.qa",
        elements=[LocatorDef(name="searchInput", by="css", value="input[type='search']")],
    )
    assert out.class_name == "HomePage"
    assert len(out.elements) == 1
    assert out.elements[0].confidence == "high"


def test_page_object_output_missing_class_name_fails():
    from qa_framework_generator.models import PageObjectOutput
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PageObjectOutput(package_name="com.example.qa", elements=[])


def test_page_object_output_low_confidence_locator():
    from qa_framework_generator.models import LocatorDef
    loc = LocatorDef(name="el", by="xpath", value="//div[1]", confidence="low")
    assert loc.confidence == "low"


def test_page_object_has_placeholder_flag_on_low_confidence():
    from qa_framework_generator.models import PageObjectOutput, LocatorDef
    out = PageObjectOutput(
        class_name="Page",
        package_name="com.example.qa",
        elements=[LocatorDef(name="el", by="xpath", value="//div[1]", confidence="low")],
    )
    assert out.has_placeholder_locators()


def test_page_object_no_placeholder_when_all_high():
    from qa_framework_generator.models import PageObjectOutput, LocatorDef
    out = PageObjectOutput(
        class_name="Page",
        package_name="com.example.qa",
        elements=[LocatorDef(name="el", by="css", value="#btn", confidence="high")],
    )
    assert not out.has_placeholder_locators()


# --- Schema: TestCaseOutput ---

def test_test_case_output_valid():
    from qa_framework_generator.models import TestCaseOutput, TestStep
    out = TestCaseOutput(
        class_name="SmokeTest",
        package_name="com.example.qa",
        groups=["smoke"],
        steps=[TestStep(action="open", target="HomePage")],
        assertions=["Assert.assertTrue(driver.getTitle().length() > 0)"],
    )
    assert out.class_name == "SmokeTest"
    assert "smoke" in out.groups


def test_test_case_output_missing_class_name_fails():
    from qa_framework_generator.models import TestCaseOutput
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        TestCaseOutput(package_name="com.example.qa", groups=["smoke"],
                       steps=[], assertions=[])


def test_test_case_output_empty_groups_fails():
    from qa_framework_generator.models import TestCaseOutput
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        TestCaseOutput(class_name="T", package_name="com.example.qa",
                       groups=[], steps=[], assertions=[])


# --- Prompts ---

def test_build_page_object_prompt_returns_string():
    from qa_framework_generator.prompts import build_page_object_prompt
    from qa_framework_generator.config import PageDef, ElementDef
    page = PageDef(
        name="HomePage",
        path="/",
        elements=[ElementDef(name="searchInput", by="css", value="input[type='search']")],
    )
    prompt = build_page_object_prompt(page, "com.example.qa")
    assert isinstance(prompt, str) and len(prompt) > 50


def test_build_page_object_prompt_contains_page_name():
    from qa_framework_generator.prompts import build_page_object_prompt
    from qa_framework_generator.config import PageDef
    page = PageDef(name="CheckoutPage", path="/checkout")
    prompt = build_page_object_prompt(page, "com.example.qa")
    assert "CheckoutPage" in prompt


def test_build_test_case_prompt_returns_string():
    from qa_framework_generator.prompts import build_test_case_prompt
    from qa_framework_generator.config import FlowDef, PageDef
    flow = FlowDef(name="SmokeTest", groups=["smoke"], steps=[{"open": "HomePage"}])
    pages = [PageDef(name="HomePage", path="/")]
    prompt = build_test_case_prompt(flow, pages, "com.example.qa")
    assert isinstance(prompt, str) and len(prompt) > 50


def test_build_test_case_prompt_contains_flow_name():
    from qa_framework_generator.prompts import build_test_case_prompt
    from qa_framework_generator.config import FlowDef
    flow = FlowDef(name="CheckoutFlow", groups=["regression"])
    prompt = build_test_case_prompt(flow, [], "com.example.qa")
    assert "CheckoutFlow" in prompt


# --- LLM factory ---

def test_llm_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import importlib
    import qa_framework_generator.llm as llm_mod
    importlib.reload(llm_mod)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        llm_mod.get_openai_chat_model()


def test_llm_raises_with_empty_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    import importlib
    import qa_framework_generator.llm as llm_mod
    importlib.reload(llm_mod)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        llm_mod.get_openai_chat_model()

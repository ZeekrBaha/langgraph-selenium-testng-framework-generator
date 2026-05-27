# Prompt Contracts

All LLM nodes in the generator use structured output. The model must return JSON matching the schema below. Output is validated with Pydantic before rendering Java. If validation fails, the repair node retries with a targeted prompt.

---

## Page Object Prompt

**Module:** `qa_framework_generator/prompts.py` → `build_page_object_prompt(page, package_name)`

**System prompt:** `templates/prompts/page_object_system.md`

**Input context:**

```json
{
  "name": "HomePage",
  "path": "/",
  "package_name": "com.example.qa.pages",
  "elements": [
    {"name": "searchInput", "by": "css", "value": "input[type='search']"}
  ]
}
```

**Required output schema:**

```json
{
  "class_name": "HomePage",
  "package_name": "com.example.qa.pages",
  "elements": [
    {
      "name": "searchInput",
      "by": "css",
      "value": "input[type='search']",
      "confidence": "high"
    }
  ],
  "extra_methods": []
}
```

**Pydantic model:** `PageObjectOutput` in `qa_framework_generator/models.py`

**Hard rules enforced at output validation:**

- `class_name` is required.
- `confidence` must be `"high"`, `"medium"`, or `"low"`.
- If any element has `confidence = "low"`, `has_placeholder_locators()` returns `True`.
- If `allow_placeholder_locators = False` (default), static validator fails on `TODO_REPLACE_LOCATOR`.

---

## Test Case Prompt

**Module:** `qa_framework_generator/prompts.py` → `build_test_case_prompt(flow, pages, package_name)`

**System prompt:** `templates/prompts/test_case_system.md`

**Input context:**

```json
{
  "name": "SmokeTest",
  "package_name": "com.example.qa.tests",
  "groups": ["smoke"],
  "steps": [
    {"open": "HomePage"},
    {"assert_title_contains": "DemoShop"}
  ],
  "available_pages": ["HomePage", "SearchResultsPage"]
}
```

**Required output schema:**

```json
{
  "class_name": "SmokeTest",
  "package_name": "com.example.qa.tests",
  "groups": ["smoke"],
  "steps": [
    {"action": "open", "target": "HomePage", "value": null},
    {"action": "assert_title", "target": null, "value": "DemoShop"}
  ],
  "assertions": [
    "Assert.assertTrue(driver.getTitle().contains(\"DemoShop\"), \"Title should contain DemoShop\")"
  ]
}
```

**Pydantic model:** `TestCaseOutput` in `qa_framework_generator/models.py`

**Hard rules enforced at output validation:**

- `class_name` is required.
- `groups` must not be empty (`model_validator` raises `ValueError` on empty list).
- Generated Java must not contain `Thread.sleep` — static validator flags it, repair node removes it.

---

## LLM Factory

**Module:** `qa_framework_generator/llm.py` → `get_openai_chat_model()`

**Environment variables:**

| Variable | Required | Default |
|---|---|---|
| `OPENAI_API_KEY` | Yes | — (raises `RuntimeError` if missing or empty) |
| `OPENAI_MODEL` | No | `gpt-4.1` |
| `OPENAI_TEMPERATURE` | No | `0.1` |

**Key behaviors:**

- Calls `load_dotenv()` before reading env vars — supports `.env` file.
- Raises `RuntimeError("OPENAI_API_KEY is required...")` if key is missing or blank.
- Never logs or echoes the API key.
- The import of `langchain_openai` is deferred inside the function so the module can be imported without installing OpenAI dependencies (useful for unit tests that mock the factory).

---

## Repair Prompt (Milestone 2)

When static or Maven validation fails and a deterministic fix is not possible, the repair node sends the following to the LLM:

```
[system prompt: repair_system.md]

## Failed validation

Name: check_testng_groups_SmokeTest.java
Output: @Test annotation without groups in src/test/java/.../tests/SmokeTest.java
Fix hint: Add groups = {"smoke"} to @Test annotation

## Affected file

[full content of SmokeTest.java]
```

The model must return the corrected Java file content only — no markdown, no explanation.

System prompt location: `templates/prompts/repair_system.md` (Milestone 2).

---

## Future Prompts (Milestone 2)

| Prompt | Purpose | System prompt file |
|---|---|---|
| Requirements | Normalize raw input to structured requirements | `requirements_system.md` |
| Blueprint | Decide all generated file names and packages | `blueprint_system.md` |
| Review | Check generated framework against acceptance criteria | `review_system.md` |
| Repair | Fix failing files from validation output | `repair_system.md` |

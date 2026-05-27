# LangGraph Selenium TestNG Framework Generator Implementation Plan

**Goal:** Build a Python LangGraph application that generates a complete Java Selenium + TestNG UI automation framework, validates it, and reports exactly what was created and what failed.

**Architecture:** Python owns orchestration, prompts, project templates, checks, OpenAI model access, and repair loops. LangGraph runs a deterministic pipeline of agents/nodes: requirements intake, blueprint creation, file generation, static validation, Maven validation, self-review, repair, and final handoff. The generated output is a standalone Java Maven project with Selenium WebDriver, TestNG, Extent Reports, WebDriverManager, CI, environment configs, POM classes, listeners, retry logic, screenshots, and sample tests.

**Tech Stack:** Python 3.12, LangGraph, LangChain OpenAI integration, OpenAI API key via `OPENAI_API_KEY`, Pydantic, Jinja2, python-dotenv, pytest, Java 17, Maven, Selenium 4, TestNG, Extent Reports, WebDriverManager, SLF4J/Logback, GitHub Actions.

---

## Reference Project Baseline

Reference repository: production-style Java Selenium + TestNG project baseline

Observed baseline features to preserve:

- Java 17 + Maven framework.
- Selenium WebDriver + TestNG.
- Page Object Model.
- `BaseTest` and `DriverFactory`.
- Thread-safe WebDriver with `ThreadLocal`.
- Environment switching through runtime properties such as `mvn clean test -Denv=qa`.
- Retry mechanism for flaky tests.
- TestNG grouping for smoke/regression execution.
- Parallel execution support.
- Extent Reports.
- Failure screenshots.
- GitHub Actions CI with uploaded artifacts.
- Environment properties under `src/test/resources/env`.
- TestNG suite config under `src/test/resources/testng.xml`.

Improvements to add:

- Python generator with repeatable prompts and structured state.
- Configurable target site, package name, base URL environments, browser list, groups, and CI profile.
- Validation gates before handoff.
- Generated framework unit checks where possible.
- Maven compile/test verification.
- HTML report artifact validation.
- CI YAML syntax validation.
- Generated README with exact commands.
- Clear repair loop when generated code fails compilation.
- Optional generated sample pages/tests for ecommerce, login, search, cart, checkout, or generic web app flows.

## Product Shape

The project should be a generator, not only a static framework. The user runs a Python command, answers prompts or passes a config file, and receives a generated Java automation framework.

Example command:

```bash
uv run python -m qa_framework_generator generate \
  --config examples/ecommerce_demo.yaml \
  --output selenium-testng-framework-output
```

Required local environment:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Optional local `.env`:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1
OPENAI_TEMPERATURE=0.1
```

The API key must be read only from environment variables or `.env`. It must not be copied into generated Java files, generated reports, logs, screenshots, GitHub Actions YAML, or README examples.

Expected result:

```text
selenium-testng-framework-output/
  pom.xml
  README.md
  .github/workflows/ui-tests.yml
  src/main/java/com/acme/qa/
  src/test/java/com/acme/qa/tests/
  src/test/resources/
  target/ only after Maven is run
```

## Generated Java Framework Features

The generated framework must include:

- `pom.xml` with locked versions and Maven Surefire config.
- Java package generated from config, default `com.generated.qa`.
- `DriverFactory` with Chrome, Firefox, Edge, headless mode, window size, timeouts, and `ThreadLocal<WebDriver>`.
- `BaseTest` with setup/teardown, environment loading, browser selection, and listener registration.
- `ConfigLoader` and `EnvConfig` for `dev`, `qa`, and `prod`.
- `BasePage` with explicit waits, click/type/getText helpers, URL assertions, JS scroll, safe element lookup, and screenshot hooks.
- Page objects generated from requested pages.
- Test classes generated from requested flows.
- TestNG groups: `smoke`, `regression`, `critical`, and optional custom groups.
- Retry analyzer and annotation transformer.
- TestNG listeners for lifecycle logging, screenshots, and Extent Reports.
- Extent report manager with one report per run.
- Screenshot utility that writes deterministic paths.
- `testng.xml` with parallel class/method configuration.
- GitHub Actions workflow for Java 17, Chrome, Maven cache, headless execution, and artifact upload.
- `.gitignore` excluding `target`, reports, screenshots, IDE files, and generated temp files.
- Generated `README.md` with exact local and CI commands.

## Generator Repository Structure

Create this structure:

```text
langgraph-selenium-testng-framework-generator/
  pyproject.toml
  .env.example
  README.md
  qa_framework_generator/
    __init__.py
    __main__.py
    cli.py
    config.py
    state.py
    graph.py
    llm.py
    models.py
    prompts.py
    renderer.py
    validators.py
    repair.py
    file_writer.py
    templates/
      java/
        pom.xml.j2
        README.md.j2
        gitignore.j2
        github-actions.yml.j2
        BaseTest.java.j2
        DriverFactory.java.j2
        ConfigLoader.java.j2
        EnvConfig.java.j2
        BasePage.java.j2
        RetryAnalyzer.java.j2
        RetryTransformer.java.j2
        TestListener.java.j2
        ExtentReportListener.java.j2
        ExtentManager.java.j2
        ExtentTestManager.java.j2
        ScreenshotUtil.java.j2
        PageObject.java.j2
        TestClass.java.j2
        testng.xml.j2
        env.properties.j2
      prompts/
        requirements_system.md
        blueprint_system.md
        page_object_system.md
        test_case_system.md
        review_system.md
        repair_system.md
  tests/
    test_config.py
    test_graph_routes.py
    test_renderer.py
    test_validators.py
    fixtures/
      minimal_config.yaml
      minimal_config.yaml
  examples/
    minimal.yaml
    ecommerce_demo.yaml
  selenium-testng-framework-output/
    README.md
  docs/
    plans/
      2026-05-27-langgraph-selenium-testng-framework-generator.md
```

## OpenAI LLM Configuration

Create `qa_framework_generator/llm.py` to centralize model setup.

Requirements:

- Read `OPENAI_API_KEY` from the environment after loading `.env`.
- Read `OPENAI_MODEL`, defaulting to a configurable production model.
- Read `OPENAI_TEMPERATURE`, defaulting to `0.1`.
- Fail fast with a clear local error if `OPENAI_API_KEY` is missing and a graph node needs the LLM.
- Redact API keys in all exceptions, logs, and generated reports.
- Keep deterministic template rendering independent from the LLM so the MVP can still generate a skeleton without page/test intelligence.

Example shape:

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

def get_openai_chat_model() -> ChatOpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for LLM generation nodes.")

    return ChatOpenAI(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
    )
```

## LangGraph State

Use one typed state object for the whole graph.

```python
from typing import Literal
from pydantic import BaseModel, Field

class GeneratedFile(BaseModel):
    path: str
    content: str
    kind: Literal["java", "xml", "yaml", "markdown", "properties", "text"]

class ValidationResult(BaseModel):
    name: str
    passed: bool
    output: str = ""
    fix_hint: str = ""

class GeneratorState(BaseModel):
    config_path: str | None = None
    output_dir: str
    target_package: str = "com.generated.qa"
    project_name: str
    requirements: dict = Field(default_factory=dict)
    blueprint: dict = Field(default_factory=dict)
    generated_files: list[GeneratedFile] = Field(default_factory=list)
    validation_results: list[ValidationResult] = Field(default_factory=list)
    repair_attempts: int = 0
    max_repair_attempts: int = 3
    status: Literal["new", "generated", "validating", "repairing", "done", "failed"] = "new"
```

## LangGraph Nodes

The graph should run these nodes:

1. `load_config_node`
   - Reads YAML config or interactive answers.
   - Validates required fields with Pydantic.

2. `requirements_node`
   - Converts user input into normalized framework requirements.
   - Produces pages, flows, environments, browsers, groups, reporting preferences, and CI preferences.

3. `blueprint_node`
   - Creates a file-by-file blueprint for the Java framework.
   - Decides packages, class names, suite names, and generated commands.

4. `render_static_templates_node`
   - Renders deterministic files from Jinja templates: Maven, CI, config, base classes, listeners, reports, retry, utilities.

5. `generate_pages_and_tests_node`
   - Uses prompts to create page objects and TestNG tests from requested flows.
   - Output must be structured JSON first, then rendered to Java.

6. `write_files_node`
   - Writes the framework to `output_dir`.
   - Refuses to overwrite non-generated files unless `--force` is passed.

7. `static_validation_node`
   - Checks file presence, package declarations, imports, XML parseability, YAML parseability, no unresolved template markers, no hardcoded secrets, and no `target/` checked into the template output.

8. `maven_validation_node`
   - Runs `mvn -q -DskipTests compile`.
   - Runs `mvn -q test -Dgroups=smoke -Dheadless=true` when browser dependencies are available.

9. `review_node`
   - Reviews generated framework against acceptance criteria.
   - Produces pass/fail findings and repair hints.

10. `repair_node`
   - Applies bounded repairs from validation output.
   - Re-enters validation until green or `max_repair_attempts` is reached.

11. `final_report_node`
   - Writes `GENERATION_REPORT.md`.
   - Includes created files, commands, validation results, repair attempts, and next steps.

## Graph Routing

Routing rules:

```text
load_config_node -> requirements_node
requirements_node -> blueprint_node
blueprint_node -> render_static_templates_node
render_static_templates_node -> generate_pages_and_tests_node
generate_pages_and_tests_node -> write_files_node
write_files_node -> static_validation_node
static_validation_node -> maven_validation_node if passed else repair_node
maven_validation_node -> review_node if compile passed else repair_node
review_node -> final_report_node if passed else repair_node
repair_node -> static_validation_node if repair_attempts < max_repair_attempts
repair_node -> final_report_node if repair_attempts >= max_repair_attempts
```

## Prompt Contracts

All LLM outputs must be structured and validated. Do not ask the model to directly write files without schema checks.

### Requirements Prompt

Purpose: Convert raw user request into normalized framework requirements.

Output schema:

```json
{
  "project_name": "string",
  "package_name": "string",
  "environments": [{"name": "qa", "base_url": "https://example.com"}],
  "browsers": ["chrome"],
  "headless_default": true,
  "pages": [{"name": "HomePage", "url_path": "/", "elements": []}],
  "flows": [{"name": "SmokeTest", "groups": ["smoke"], "steps": []}],
  "ci": {"provider": "github_actions", "upload_artifacts": true},
  "reporting": {"extent": true, "screenshots_on_failure": true},
  "parallel": {"enabled": true, "thread_count": 3}
}
```

### Blueprint Prompt

Purpose: Decide every generated file and class responsibility.

Hard rules:

- Use Java 17 syntax.
- Use Selenium 4 APIs.
- Use TestNG annotations.
- Use explicit waits, not sleeps.
- No credentials in generated files.
- No generated `target/`, `bin/`, `.classpath`, or `.project`.
- Generated page objects extend `BasePage`.
- Generated tests extend `BaseTest`.

### Page Object Prompt

Purpose: Generate page objects from page definitions.

Hard rules:

- Use `By` locators, not Selenium PageFactory.
- Prefer stable locators from config.
- If locator confidence is low, add a visible `TODO_REPLACE_LOCATOR` marker and make validation fail unless `--allow-placeholder-locators` is passed.
- Keep assertions in tests, not page objects, except page-level identity checks.

### Test Case Prompt

Purpose: Generate TestNG classes from flow definitions.

Hard rules:

- Every test has `@Test(groups = {...})`.
- Tests use page methods, not raw WebDriver interactions.
- Tests include meaningful assertions.
- No `Thread.sleep`.
- No dependency on test order unless explicitly configured.

### Review Prompt

Purpose: Act as a strict framework reviewer.

Review checklist:

- Can Maven compile?
- Does TestNG suite point to real classes?
- Does CI run the same command as README?
- Are env URLs externalized?
- Are drivers thread-safe?
- Are screenshots and reports attached on final failure?
- Are retry attempts visible?
- Are generated commands documented?

## Example Config

Create `examples/ecommerce_demo.yaml`:

```yaml
project_name: ecommerce-demo-automation
package_name: com.generated.demoqa
output_dir: selenium-testng-framework-output
environments:
  dev:
    base_url: https://dev.example.com
  qa:
    base_url: https://qa.example.com
  prod:
    base_url: https://example.com
browsers:
  - chrome
  - firefox
headless_default: true
parallel:
  enabled: true
  thread_count: 3
pages:
  - name: HomePage
    path: /
    elements:
      - name: searchInput
        by: css
        value: input[type='search']
      - name: searchButton
        by: css
        value: button[type='submit']
flows:
  - name: SmokeTest
    groups: [smoke]
    steps:
      - open: HomePage
      - assert_title_contains: DemoShop
```

## Tasks

### Task 1: Bootstrap Python Project

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `qa_framework_generator/__init__.py`
- Create: `qa_framework_generator/__main__.py`
- Create: `qa_framework_generator/cli.py`
- Create: `tests/test_config.py`

**Step 1: Write failing CLI/config tests**

Create tests that assert:

- YAML config loads.
- Missing `project_name` fails.
- Default package is applied.
- CLI exposes `generate`.

**Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_config.py -q
```

Expected: fail because package does not exist.

**Step 3: Implement minimal config and CLI**

Implement Pydantic config models and Typer or argparse CLI.

Add dependencies:

- `langgraph`
- `langchain-openai`
- `pydantic`
- `pyyaml`
- `jinja2`
- `python-dotenv`
- `pytest`

Create `.env.example`:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1
OPENAI_TEMPERATURE=0.1
```

**Step 4: Run tests**

Run:

```bash
uv run pytest tests/test_config.py -q
```

Expected: pass.

### Task 2: Add Generator State and Graph Skeleton

**Files:**
- Create: `qa_framework_generator/state.py`
- Create: `qa_framework_generator/graph.py`
- Create: `tests/test_graph_routes.py`

**Step 1: Write graph routing tests**

Assert graph starts at config load and eventually reaches final report for a minimal config with mocked nodes.

**Step 2: Run failing tests**

```bash
uv run pytest tests/test_graph_routes.py -q
```

**Step 3: Implement state and graph**

Use LangGraph `StateGraph` with node functions and conditional edges.

**Step 4: Run tests**

```bash
uv run pytest tests/test_graph_routes.py -q
```

### Task 3: Build Static Template Renderer

**Files:**
- Create: `qa_framework_generator/renderer.py`
- Create: `qa_framework_generator/templates/java/pom.xml.j2`
- Create: `qa_framework_generator/templates/java/BaseTest.java.j2`
- Create: `qa_framework_generator/templates/java/DriverFactory.java.j2`
- Create: `qa_framework_generator/templates/java/testng.xml.j2`
- Create: `tests/test_renderer.py`

**Step 1: Write failing renderer tests**

Assert renderer creates `pom.xml`, `BaseTest.java`, `DriverFactory.java`, and `src/test/resources/testng.xml` with expected package names.

**Step 2: Run failing tests**

```bash
uv run pytest tests/test_renderer.py -q
```

**Step 3: Implement Jinja renderer**

Render templates into `GeneratedFile` objects. Do not write to disk yet.

**Step 4: Run tests**

```bash
uv run pytest tests/test_renderer.py -q
```

### Task 4: Generate Core Java Framework Templates

**Files:**
- Create: all Java templates listed in `Generator Repository Structure`
- Modify: `qa_framework_generator/renderer.py`
- Modify: `tests/test_renderer.py`

**Step 1: Expand renderer tests**

Assert all required generated files exist.

**Step 2: Run failing tests**

```bash
uv run pytest tests/test_renderer.py -q
```

**Step 3: Implement templates**

Include:

- Maven dependencies.
- Base test lifecycle.
- Driver creation.
- Environment config.
- Extent reporting.
- TestNG listeners.
- Retry analyzer.
- Screenshot utility.
- `.gitignore`.
- GitHub Actions workflow.

**Step 4: Run tests**

```bash
uv run pytest tests/test_renderer.py -q
```

### Task 5: Add Prompt-Based Page/Test Generation

**Files:**
- Create: `qa_framework_generator/llm.py`
- Create: `qa_framework_generator/prompts.py`
- Create: `qa_framework_generator/models.py`
- Create: `qa_framework_generator/templates/prompts/page_object_system.md`
- Create: `qa_framework_generator/templates/prompts/test_case_system.md`
- Modify: `qa_framework_generator/graph.py`
- Create: `tests/test_prompt_outputs.py`

**Step 1: Write schema tests**

Validate mock LLM JSON for page object and test case generation.

**Step 2: Run failing tests**

```bash
uv run pytest tests/test_prompt_outputs.py -q
```

**Step 3: Implement structured prompt contracts**

Use Pydantic models for LLM outputs before rendering Java. Load the OpenAI chat model only inside LLM-backed nodes through `qa_framework_generator/llm.py`, and keep tests mocked so unit tests do not call the real API.

**Step 4: Run tests**

```bash
uv run pytest tests/test_prompt_outputs.py -q
```

### Task 6: Add File Writer with Overwrite Safety

**Files:**
- Create: `qa_framework_generator/file_writer.py`
- Create: `tests/test_file_writer.py`

**Step 1: Write failing tests**

Assert:

- Files are written to output dir.
- Existing non-generated files are not overwritten.
- `--force` allows overwrite.

**Step 2: Run failing tests**

```bash
uv run pytest tests/test_file_writer.py -q
```

**Step 3: Implement writer**

Add generated file header comments where format allows it.

**Step 4: Run tests**

```bash
uv run pytest tests/test_file_writer.py -q
```

### Task 7: Add Validators

**Files:**
- Create: `qa_framework_generator/validators.py`
- Create: `tests/test_validators.py`

**Step 1: Write failing validation tests**

Assert validators catch:

- Missing `pom.xml`.
- Invalid XML.
- Unresolved Jinja markers.
- `Thread.sleep`.
- Missing TestNG groups.
- Placeholder locators when not allowed.
- Generated `target/` or `bin/` files.

**Step 2: Run failing tests**

```bash
uv run pytest tests/test_validators.py -q
```

**Step 3: Implement validators**

Use XML/YAML parsers where possible. Use narrow regex checks for Java anti-patterns.

**Step 4: Run tests**

```bash
uv run pytest tests/test_validators.py -q
```

### Task 8: Add Maven Validation

**Files:**
- Modify: `qa_framework_generator/validators.py`
- Create: `tests/test_maven_validator.py`

**Step 1: Write subprocess tests with mocks**

Assert compile command is:

```bash
mvn -q -DskipTests compile
```

Assert smoke command is:

```bash
mvn -q test -Dgroups=smoke -Dheadless=true
```

**Step 2: Run failing tests**

```bash
uv run pytest tests/test_maven_validator.py -q
```

**Step 3: Implement subprocess validator**

Capture stdout/stderr and return `ValidationResult`.

**Step 4: Run tests**

```bash
uv run pytest tests/test_maven_validator.py -q
```

### Task 9: Add Repair Loop

**Files:**
- Create: `qa_framework_generator/repair.py`
- Modify: `qa_framework_generator/graph.py`
- Create: `tests/test_repair.py`

**Step 1: Write repair routing tests**

Assert failed validation routes to repair and stops after `max_repair_attempts`.

**Step 2: Run failing tests**

```bash
uv run pytest tests/test_repair.py -q
```

**Step 3: Implement repair node**

For deterministic issues, fix directly. For code-generation issues, call repair prompt with validation output and affected file only.

**Step 4: Run tests**

```bash
uv run pytest tests/test_repair.py -q
```

### Task 10: Add End-to-End Generation Smoke Test

**Files:**
- Create: `examples/minimal.yaml`
- Create: `examples/ecommerce_demo.yaml`
- Create: `tests/test_e2e_generation.py`

**Step 1: Write e2e test**

Generate a minimal framework into a temp directory and assert:

- `pom.xml` exists.
- `src/main/java/.../DriverFactory.java` exists.
- `src/test/java/.../tests/SmokeTest.java` exists.
- `src/test/resources/testng.xml` exists.
- `README.md` includes Maven commands.

**Step 2: Run failing test**

```bash
uv run pytest tests/test_e2e_generation.py -q
```

**Step 3: Wire CLI to graph**

Make `generate` run the graph and write final report.

**Step 4: Run e2e test**

```bash
uv run pytest tests/test_e2e_generation.py -q
```

### Task 11: Validate Generated Java Project Locally

**Files:**
- Generated output directory: `selenium-testng-framework-output`

**Step 1: Generate project**

```bash
uv run python -m qa_framework_generator generate --config examples/minimal.yaml --output selenium-testng-framework-output --force
```

**Step 2: Compile generated project**

```bash
cd selenium-testng-framework-output
mvn -q -DskipTests compile
```

Expected: compile passes.

**Step 3: Run smoke tests headless**

```bash
mvn -q test -Dgroups=smoke -Dheadless=true
```

Expected: smoke test passes or fails only because target external site is unavailable. If unavailable, generated framework should still compile and report the runtime failure cleanly.

### Task 12: Documentation and Handoff

**Files:**
- Modify: `README.md`
- Create: `docs/generated-framework-contract.md`
- Create: `docs/prompt-contracts.md`

**Step 1: Document generator usage**

Include:

- Install command.
- `OPENAI_API_KEY` setup.
- Generate command.
- Config format.
- Validation gates.
- Repair loop behavior.
- Generated Java framework commands.

**Step 2: Run full Python tests**

```bash
uv run pytest -q
```

**Step 3: Run generation smoke**

```bash
uv run python -m qa_framework_generator generate --config examples/ecommerce_demo.yaml --output selenium-testng-framework-output --force
```

**Step 4: Compile generated framework**

```bash
cd selenium-testng-framework-output
mvn -q -DskipTests compile
```

## Acceptance Criteria

The project is complete when:

- LLM nodes use OpenAI through `OPENAI_API_KEY`.
- `.env.example` exists and real secrets are ignored.
- Running the Python generator creates a Java Selenium/TestNG Maven framework.
- The generated framework contains all baseline features from the reference project.
- The generated framework improves the reference with validation, repair, structured prompts, safer overwrite behavior, and documented generation reports.
- Python unit tests pass.
- Generated Java project compiles with Maven.
- Smoke test execution is documented and runnable.
- CI workflow is generated.
- `GENERATION_REPORT.md` clearly lists all files, validations, and repair attempts.

## Initial Milestone Recommendation

Build this in three milestones:

1. **MVP Generator:** config, static templates, file writer, validators, generated Java compile.
2. **LangGraph Intelligence:** prompt-based page/test generation, structured output, review node, repair loop.
3. **Framework Hardening:** richer Selenium utilities, CI artifact checks, report validation, ecommerce flow examples, documentation polish.

Start with the MVP generator before relying on LLM-generated Java. Deterministic templates should own the framework skeleton; LangGraph and prompts should customize pages, tests, and repair failures.

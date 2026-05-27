# LangGraph Selenium TestNG Framework Generator

A Python LangGraph application that generates production-grade Java Selenium + TestNG automation frameworks from a single YAML config file — with LLM-powered generation, DeepEval quality gates, self-repair loops, and CI scaffolding baked in.

You describe your target application (pages, flows, environments, browsers). The generator produces a standalone Maven project with Page Object Model, Selenium Grid support, parallel execution, Extent Reports, retry logic, screenshots, and GitHub Actions CI — validates it, scores it with DeepEval, repairs any failures, and reports exactly what it built.

---

## What It Generates

| Artifact | Description |
|---|---|
| `pom.xml` | Maven build with locked dependency versions and Surefire config |
| `DriverFactory.java` | Thread-safe `ThreadLocal<WebDriver>` for Chrome, Firefox, Edge, headless, and **Selenium Grid** |
| `BaseTest.java` | TestNG lifecycle: `@BeforeMethod(alwaysRun=true)` setup, `@AfterMethod(alwaysRun=true)` teardown, environment loading, listener registration, `getCurrentUrl()` / `getTitle()` helpers |
| `BasePage.java` | Explicit waits, hover, drag-drop, dropdown, typeAndSubmit, scrollToBottom, countElements |
| `ConfigLoader.java` | Environment switcher — `mvn test -Denv=qa` selects QA base URLs |
| `RetryAnalyzer.java` | Automatic retry for flaky tests with configurable attempt count |
| `TestListener.java` | TestNG listener: lifecycle logging + screenshots on failure |
| `ExtentReportListener.java` | One HTML report per run, attached to failing tests |
| Page objects | LLM-generated from your `pages:` config — By locators, interaction methods |
| Test classes | LLM-generated from your `flows:` config — TestNG groups, assertions, no raw WebDriver |
| `testng.xml` | Suite config with parallel class/method execution |
| `.github/workflows/ui-tests.yml` | GitHub Actions: Java 17, headless Chrome, Maven cache, artifact upload |
| `GENERATION_REPORT.md` | File list, validation results, DeepEval scores, repair attempts |

---

## Architecture

### LangGraph pipeline

```
YAML Config
    │
    ▼
┌─────────────────┐
│ load_config     │  Reads YAML, validates with Pydantic
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ requirements    │  LLM: normalises raw input into structured requirements
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ blueprint       │  LLM: decides every generated file, class name, package, command
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ render_static   │  Jinja2: pom.xml, BaseTest, DriverFactory, listeners, CI, README
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ generate_pages  │  LLM: structured JSON → Java page objects and TestNG test classes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ evaluate        │  DeepEval GEval: scores page objects and test classes
│                 │  PageObjectQuality + TestClassQuality metrics
│                 │  Routes to repair if score < threshold (default 0.7)
└────────┬────────┘
         │
    pass │ fail
         │    └──────────────────────┐
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│ write_files     │         │ repair          │  Bounded: max 3 attempts
└────────┬────────┘         │                 │  Deterministic: Thread.sleep fixer
         │                  │  LLM: targeted  │  LLM: repair with file + error
         ▼                  │  prompt         │
┌─────────────────┐         └────────┬────────┘
│ static_validate │  Jinja markers, XML/YAML parse,    │
│                 │  Thread.sleep, TestNG groups,       │
│                 │  placeholder locators, no target/,  │ loop
│                 │  cross-ref: pageVar.method() must   │
│                 │  exist on that page class            │
└────────┬────────┘                  │
    pass │ fail                      │
         │    └──────────────────────┘
         ▼
┌─────────────────┐
│ maven_validate  │  mvn -DskipTests test-compile
│                 │  (main + test sources; parses
│                 │  compiler errors for repair)
└────────┬────────┘
    pass │ fail ──────────────────▶ repair
         ▼
┌─────────────────┐
│ review          │  LLM checklist: Maven OK, thread-safe drivers,
│                 │  env URLs externalised, screenshots on failure
└────────┬────────┘
    pass │ fail ──────────────────▶ repair
         ▼
┌─────────────────┐
│ final_report    │  Writes GENERATION_REPORT.md; status "done"
│                 │  only if all validations passed —
│                 │  "failed" if failures remain after repair
└─────────────────┘
```

### Graph routing

```
load_config → requirements → blueprint → render_static → generate_pages
    → evaluate ──pass──▶ write_files → static_validate ──pass──▶ maven_validate ──pass──▶ review
         │                                   │                         │                       │
        fail                               fail                      fail                    fail
         └───────────────────────────────▶ repair ◀──────────────────────────────────────────┘
                                             │
                                attempts < max_attempts
                                             │
                                     → static_validate (loop)
                                             │
                                    attempts >= max_attempts
                                             │
                                     → final_report
```

### Generated Java framework structure

```
com.example.qa/
├── base/
│   ├── BaseTest.java          ← TestNG lifecycle, environment, listener registration
│   └── BasePage.java          ← Explicit waits, hover, dropdown, drag-drop, scroll helpers
├── driver/
│   └── DriverFactory.java     ← ThreadLocal<WebDriver>, local + Selenium Grid (-Dgrid.url)
├── config/
│   ├── ConfigLoader.java      ← Reads env.properties per -Denv flag
│   └── EnvConfig.java         ← Typed environment values (baseUrl, etc.)
├── listeners/
│   ├── TestListener.java      ← ITestListener: lifecycle log + screenshot on fail
│   ├── ExtentReportListener.java
│   ├── ExtentManager.java
│   └── ExtentTestManager.java
├── retry/
│   ├── RetryAnalyzer.java
│   └── RetryTransformer.java
├── utils/
│   └── ScreenshotUtil.java    ← Deterministic path: target/screenshots/{test}.png
├── pages/                     ← LLM-generated from pages: in YAML
│   └── HomePage.java
└── tests/                     ← LLM-generated from flows: in YAML
    └── SmokeTest.java
```

---

## Tech Stack

### Python generator

| Layer | Technology |
|---|---|
| Orchestration | LangGraph (StateGraph, conditional edges) |
| LLM generation | LangChain OpenAI (`ChatOpenAI` + `with_structured_output`) |
| LLM evaluation | DeepEval (`GEval` — PageObjectQuality + TestClassQuality) |
| Config validation | Pydantic v2 |
| Template rendering | Jinja2 |
| Config format | PyYAML |
| CLI | Typer |
| Environment | python-dotenv |
| Tests | pytest |
| Python | 3.12+ |

### Generated Java framework

| Layer | Technology |
|---|---|
| Build | Maven 3.x |
| Language | Java 17 |
| Browser automation | Selenium WebDriver 4 |
| Remote execution | Selenium Grid (via `-Dgrid.url`) |
| Test runner | TestNG 7 |
| Driver management | WebDriverManager |
| Reporting | Extent Reports 5 |
| Logging | SLF4J + Logback |
| CI | GitHub Actions |

---

## Project Structure

```
langgraph-selenium-testng-framework-generator/
├── pyproject.toml
├── .env.example
├── README.md
├── qa_framework_generator/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                     ← Typer CLI: generate command
│   ├── config.py                  ← Pydantic models + load_config()
│   ├── state.py                   ← GeneratorState (LangGraph typed state)
│   ├── graph.py                   ← StateGraph definition and routing
│   ├── llm.py                     ← ChatOpenAI factory, key validation
│   ├── models.py                  ← LLM output schemas (PageObjectOutput, TestCaseOutput, etc.)
│   ├── prompts.py                 ← Prompt builders for each LLM node
│   ├── renderer.py                ← Jinja2 renderer + render_page_object / render_test_class
│   ├── evaluator.py               ← DeepEval GEval scoring for generated Java
│   ├── validators.py              ← Static + Maven + YAML + Extent Report validation
│   ├── repair.py                  ← Deterministic fixer + LLM repair
│   ├── file_writer.py             ← Safe file writer with overwrite guard + stale cleanup
│   └── templates/
│       ├── java/
│       │   ├── pom.xml.j2
│       │   ├── BaseTest.java.j2
│       │   ├── BasePage.java.j2
│       │   ├── DriverFactory.java.j2
│       │   ├── ConfigLoader.java.j2
│       │   ├── EnvConfig.java.j2
│       │   ├── RetryAnalyzer.java.j2
│       │   ├── RetryTransformer.java.j2
│       │   ├── TestListener.java.j2
│       │   ├── ExtentReportListener.java.j2
│       │   ├── ExtentManager.java.j2
│       │   ├── ExtentTestManager.java.j2
│       │   ├── ScreenshotUtil.java.j2
│       │   ├── PageObject.java.j2
│       │   ├── TestClass.java.j2
│       │   ├── testng.xml.j2
│       │   ├── env.properties.j2
│       │   ├── README.md.j2
│       │   ├── gitignore.j2
│       │   └── github-actions.yml.j2
│       └── prompts/
│           ├── requirements_system.md
│           ├── blueprint_system.md
│           ├── page_object_system.md
│           ├── test_case_system.md
│           ├── review_system.md
│           └── repair_system.md
├── tests/
│   ├── test_config.py
│   ├── test_graph_routes.py
│   ├── test_renderer.py
│   ├── test_validators.py
│   ├── test_file_writer.py
│   ├── test_prompt_outputs.py
│   ├── test_maven_validator.py
│   ├── test_repair.py
│   ├── test_evaluator.py
│   ├── test_e2e_generation.py
│   └── fixtures/
│       └── minimal_config.yaml
├── examples/
│   ├── minimal.yaml
│   ├── ecommerce_demo.yaml
│   └── ecommerce_full.yaml        ← Login, search, cart, checkout flows
├── selenium-testng-framework-output/   ← Default generated Java project location
└── docs/
    ├── generated-framework-contract.md
    ├── prompt-contracts.md
    └── plans/
        └── 2026-05-27-langgraph-selenium-testng-framework-generator.md
```

---

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- `OPENAI_API_KEY` — required for LLM-backed nodes (requirements, blueprint, page/test generation, repair, review)
- Java 17 + Maven — required for `maven_validate` gate and running the generated framework

### Install

```bash
git clone <repo>
cd langgraph-selenium-testng-framework-generator

# Install all dependencies (includes deepeval)
uv sync
uv pip install -e ".[dev]"

# Configure API key
cp .env.example .env
# Edit .env — set OPENAI_API_KEY=sk-...
```

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key for LLM nodes and DeepEval scoring |
| `OPENAI_MODEL` | No | `gpt-4.1` | Model used for generation and evaluation |
| `OPENAI_TEMPERATURE` | No | `0.1` | Lower = more deterministic output |

> API keys are never written into generated Java files, generated reports, CI YAML, or README examples.

---

## Usage

### Generate a framework (full LangGraph pipeline)

```bash
uv run qa-framework-generator \
  --config examples/ecommerce_demo.yaml \
  --output selenium-testng-framework-output
```

### Generate without LLM (static templates only — no API key needed)

```bash
uv run qa-framework-generator \
  --config examples/ecommerce_demo.yaml \
  --output selenium-testng-framework-output \
  --skip-llm
```

### Adjust DeepEval quality threshold (default 0.7)

```bash
uv run qa-framework-generator \
  --config examples/ecommerce_full.yaml \
  --output selenium-testng-framework-output \
  --eval-threshold 0.8
```

### Run the generated Java framework

```bash
cd selenium-testng-framework-output

# Compile main + test sources (same as what the generator validates)
mvn -q -DskipTests test-compile

# Run smoke tests headless
mvn test -Dgroups=smoke -Dheadless=true

# Run against QA environment
mvn test -Denv=qa -Dgroups=regression -Dheadless=true

# Run with Firefox
mvn test -Dbrowser=firefox -Dgroups=smoke -Dheadless=true

# Run on Selenium Grid
mvn test -Dgrid.url=http://localhost:4444/wd/hub -Dgroups=smoke -Dheadless=true

# Retry flaky tests up to 2 times
mvn test -Dretry.count=2 -Dgroups=regression
```

### Run generator tests

```bash
uv run pytest -q
```

---

## Config Reference

```yaml
project_name: my-ui-automation          # Required. Used as Maven artifactId.
package_name: com.example.qa            # Java base package. Default: com.generated.qa
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
  - firefox                             # edge also supported

headless_default: true

parallel:
  enabled: true
  thread_count: 3

pages:
  - name: HomePage                      # Generates HomePage.java extending BasePage
    path: /
    elements:
      - name: searchInput               # Field name in the page object
        by: css                         # css | xpath | id | name | class
        value: input[type='search']

flows:
  - name: SmokeTest                     # Generates SmokeTest.java extending BaseTest
    groups: [smoke, regression]         # Maps to @Test(groups = {...})
    steps:
      - open: HomePage
      - type:
          element: searchInput
          value: laptop
      - assert_title_contains: DemoShop
```

---

## Validation Gates

### Static validation (before writing to disk)

The `static_validate` node runs these checks on every generated file:

| Check | What it catches |
|---|---|
| `check_pom_xml_exists` | Missing `pom.xml` |
| `check_xml_*` | Malformed XML in `pom.xml`, `testng.xml` |
| `check_yaml_*` | Malformed YAML in CI workflow |
| `check_jinja_markers_*` | Unresolved `{{ }}` / `{% %}` template tokens |
| `check_no_sleep_*` | `Thread.sleep` calls in Java test files |
| `check_testng_groups_*` | `@Test` without `groups = {...}` |
| `check_placeholder_locators_*` | `TODO_REPLACE_LOCATOR` left in page objects |
| `check_no_artifact_*` | `target/` or `bin/` paths in generated file list |
| `check_xref_*` | `pageVar.method()` calls in tests where `method` doesn't exist on that page class |

### Maven validation

Runs `mvn -q -DskipTests test-compile` — compiles both `src/main/java` and `src/test/java`. When it fails, the compiler's `[ERROR] File.java:[n,m]` output is parsed to target specific files for LLM repair.

---

## DeepEval Quality Gates

After LLM-generated page objects and test classes are produced, the `evaluate` node scores each file against two `GEval` metrics before writing to disk:

| Metric | Evaluated on | Criteria |
|---|---|---|
| `PageObjectQuality` | Every `pages/*.java` file | Correct class name, all locators present, extends BasePage, valid By methods, interaction methods exist |
| `TestClassQuality` | Every `tests/*.java` file | Correct class name, required TestNG groups, extends BaseTest, at least one Assert, no Thread.sleep, steps reflected |

Files that score below `--eval-threshold` (default `0.7`) are sent to the LLM repair loop before being written to disk. Scores are included in `GENERATION_REPORT.md`.

---

## Selenium Grid

The generated `DriverFactory.java` automatically routes to `RemoteWebDriver` when `-Dgrid.url` is provided:

```bash
# Start a local grid (Docker)
docker run -d -p 4444:4444 selenium/standalone-chrome

# Run tests against the grid
mvn test -Dgrid.url=http://localhost:4444/wd/hub -Dgroups=smoke -Dheadless=true
```

No code changes required — the same generated framework runs locally or on any Selenium Grid.

---

## Milestones

| Milestone | Status | Scope |
|---|---|---|
| 1 — MVP Generator | **Complete** | Config, static Jinja2 templates, file writer, validators, Maven compile |
| 2 — LangGraph Intelligence | **Complete** | LLM page/test generation, structured output, review node, repair loop, CLI wired to graph |
| 3 — Framework Hardening | **Complete** | Richer BasePage helpers, Selenium Grid, DeepEval quality gates, CI YAML validation, stale file cleanup, ecommerce examples |

### Milestone 1 acceptance
- [x] YAML config loads and validates with Pydantic
- [x] Jinja2 templates render static files (pom.xml, all Java infrastructure, CI, README, .gitignore, env properties)
- [x] File writer skips non-generated files; `--force` overwrites; stale file auto-cleanup
- [x] Static validator catches: missing pom.xml, invalid XML/YAML, unresolved Jinja markers, Thread.sleep, missing TestNG groups, placeholder locators, build artifacts
- [x] Maven validator mocks subprocess for `mvn test-compile` and `mvn test smoke`
- [x] Repair loop increments attempt count; deterministic Thread.sleep fixer
- [x] Generated Java project: `mvn -q -DskipTests test-compile` → **BUILD SUCCESS**
- [x] Python unit tests passing

### Milestone 2 acceptance
- [x] `requirements_node` — LLM normalises YAML config into structured requirements
- [x] `blueprint_node` — LLM decides file names, class names, packages, Maven commands
- [x] `generate_pages_node` — LLM generates `PageObjectOutput` and `TestCaseOutput` via structured output
- [x] Page objects rendered via `PageObject.java.j2` with correct By method mapping
- [x] Test classes rendered via `TestClass.java.j2` with page instantiation and assertions
- [x] `review_node` — LLM checks framework against quality checklist
- [x] `repair_node` — deterministic fixer + LLM repair with targeted prompt
- [x] CLI wired to `build_graph()` with `--skip-llm` fallback
- [x] `GENERATION_REPORT.md` written by `final_report_node`

### Milestone 3 acceptance
- [x] `BasePage` — hover, drag-drop, dropdown select, typeAndSubmit, waitForElement with timeout, countElements
- [x] `DriverFactory` — Selenium Grid via `-Dgrid.url`, clean local/remote split
- [x] `evaluate_node` — DeepEval `GEval` scoring, configurable threshold, routes to repair on failure
- [x] CI YAML validation in `validate_static`
- [x] Extent Report existence check after test run
- [x] Stale generated file auto-cleanup between runs
- [x] `examples/ecommerce_full.yaml` — login, search, cart, checkout flows (5 pages, 3 flows, verified end-to-end)
- [x] 163 Python unit tests passing

### Post-milestone fixes (batch 1)
- [x] **Method name casing** — `upper_first` Jinja2 filter preserves camelCase in generated method names (`clickResultItems()` not `clickResultitems()`)
- [x] **Eval repair routing** — `_resolve_failure_path` maps `eval_page_object_X` / `eval_test_class_X` failures to the correct Java file for LLM repair
- [x] **DeepEval unavailable warning** — when deepeval is not installed, a named `ValidationResult(passed=True)` is returned instead of a silent empty list; visible in report, doesn't block routing
- [x] **`with_structured_output` method** — all LLM nodes use `method="function_calling"` to avoid OpenAI strict schema rejection of `dict[str, Any]` fields
- [x] **Stale cleanup safety** — `cleanup=False` flag added to `write_files`; `final_report_node` no longer deletes all generated source files after Maven compiles them
- [x] **CLI entry point** — `[project.scripts]` added to `pyproject.toml` so `qa-framework-generator` installs as a proper CLI command
- [x] **DeepEval API** — migrated from deprecated `LLMTestCaseParams` to `SingleTurnParams` (deepeval 4.x)

### Post-milestone fixes (batch 2)
- [x] **Maven validates test sources** — `maven_validate` now runs `mvn -DskipTests test-compile` instead of `compile`; catches errors in `src/test/java` which is where all generated tests live
- [x] **Cross-reference validator** — `validate_cross_references()` extracts public methods from each generated page class and flags any `pageVar.method()` call in tests that doesn't exist on that page class; wired into `validate_static`
- [x] **Cross-page step routing** — `TestStep` gains a `page` field; renderer uses it per-step so `searchResultsPage.clickFirstResult()` is generated instead of `homePage.clickFirstResult()`; test case prompt updated to require `page` on every `click`/`type` step
- [x] **BaseTest driver helpers** — `getCurrentUrl()`, `getTitle()`, `getPageSource()` added to `BaseTest` so generated assertions like `getCurrentUrl().contains(...)` compile without raw `driver.` prefix
- [x] **`final_report_node` honest status** — returns `"failed"` when validation failures remain after repair exhaustion; previously always returned `"done"`
- [x] **Maven failure repair** — `_files_from_maven_error()` parses `[ERROR] /path/to/File.java:[n,m]` lines to find affected files; falls back to all test Java files; repair loop now actually fixes compilation errors
- [x] **`alwaysRun = true` on `@BeforeMethod` / `@AfterMethod`** — without this flag TestNG skips setup/teardown when running with `-Dgroups=smoke`, leaving `driver` null; adding `alwaysRun = true` guarantees lifecycle methods always execute regardless of group filter
- [x] **175 Python unit tests passing** (+12 new: cross-ref validator ×6, final-report status ×3, maven repair ×3)

---

## Reference

The generated framework follows production-style Java Selenium + TestNG patterns: ThreadLocal drivers, environment switching, retry logic, Extent Reports, and GitHub Actions CI. The generator adds LLM-powered generation, DeepEval quality scoring, structured prompts, overwrite safety, and repair loops on top of this foundation.

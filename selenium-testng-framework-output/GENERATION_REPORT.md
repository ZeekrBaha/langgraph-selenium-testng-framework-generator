# Generation Report — ecommerce-demo-automation

**Status:** done
**Output:** selenium-testng-framework-output
**Package:** com.generated.demoqa
**Repair attempts:** 0

## Files Generated

- `pom.xml`
- `.gitignore`
- `README.md`
- `.github/workflows/ui-tests.yml`
- `src/test/resources/testng.xml`
- `src/test/resources/env/dev.properties`
- `src/test/resources/env/qa.properties`
- `src/test/resources/env/prod.properties`
- `src/main/java/com/generated/demoqa/driver/DriverFactory.java`
- `src/main/java/com/generated/demoqa/base/BasePage.java`
- `src/main/java/com/generated/demoqa/config/ConfigLoader.java`
- `src/main/java/com/generated/demoqa/config/EnvConfig.java`
- `src/main/java/com/generated/demoqa/listeners/ExtentManager.java`
- `src/main/java/com/generated/demoqa/listeners/ExtentTestManager.java`
- `src/main/java/com/generated/demoqa/utils/ScreenshotUtil.java`
- `src/test/java/com/generated/demoqa/base/BaseTest.java`
- `src/test/java/com/generated/demoqa/listeners/TestListener.java`
- `src/test/java/com/generated/demoqa/listeners/ExtentReportListener.java`
- `src/test/java/com/generated/demoqa/retry/RetryAnalyzer.java`
- `src/test/java/com/generated/demoqa/retry/RetryTransformer.java`
- `src/test/java/com/generated/demoqa/pages/HomePage.java`
- `src/test/java/com/generated/demoqa/pages/SearchResultsPage.java`
- `src/test/java/com/generated/demoqa/tests/SmokeTest.java`
- `src/test/java/com/generated/demoqa/tests/SearchFlow.java`

## Validation — 5 passed / 0 failed

- ✅ `check_pom_xml_exists`
- ✅ `check_xml_pom.xml`
- ✅ `check_xml_testng.xml`
- ✅ `check_yaml_ui-tests.yml`
- ✅ `maven_compile`

## Blueprint

- Page classes: ['HomePage', 'SearchResultsPage']
- Test classes: ['SmokeTest', 'SearchFlow']
- Test groups: ['smoke', 'regression']

**Run commands:**
```bash
mvn test -Dgroups=smoke -Dheadless=true
```
```bash
mvn test -Dgroups=regression -Dheadless=true
```

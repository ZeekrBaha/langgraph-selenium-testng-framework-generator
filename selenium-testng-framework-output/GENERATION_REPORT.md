# Generation Report — ecommerce-full-automation

**Status:** done
**Output:** selenium-testng-framework-output
**Package:** com.generated.shopqa
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
- `src/main/java/com/generated/shopqa/driver/DriverFactory.java`
- `src/main/java/com/generated/shopqa/base/BasePage.java`
- `src/main/java/com/generated/shopqa/config/ConfigLoader.java`
- `src/main/java/com/generated/shopqa/config/EnvConfig.java`
- `src/main/java/com/generated/shopqa/listeners/ExtentManager.java`
- `src/main/java/com/generated/shopqa/listeners/ExtentTestManager.java`
- `src/main/java/com/generated/shopqa/utils/ScreenshotUtil.java`
- `src/test/java/com/generated/shopqa/base/BaseTest.java`
- `src/test/java/com/generated/shopqa/listeners/TestListener.java`
- `src/test/java/com/generated/shopqa/listeners/ExtentReportListener.java`
- `src/test/java/com/generated/shopqa/retry/RetryAnalyzer.java`
- `src/test/java/com/generated/shopqa/retry/RetryTransformer.java`
- `src/test/java/com/generated/shopqa/pages/LoginPage.java`
- `src/test/java/com/generated/shopqa/pages/HomePage.java`
- `src/test/java/com/generated/shopqa/pages/SearchResultsPage.java`
- `src/test/java/com/generated/shopqa/pages/ProductPage.java`
- `src/test/java/com/generated/shopqa/pages/CartPage.java`
- `src/test/java/com/generated/shopqa/tests/LoginSmokeTest.java`
- `src/test/java/com/generated/shopqa/tests/SearchAndAddToCartTest.java`
- `src/test/java/com/generated/shopqa/tests/CartCheckoutTest.java`

## Validation — 5 passed / 0 failed

- ✅ `check_pom_xml_exists`
- ✅ `check_xml_pom.xml`
- ✅ `check_xml_testng.xml`
- ✅ `check_yaml_ui-tests.yml`
- ✅ `maven_test_compile`

## Blueprint

- Page classes: ['LoginPage', 'HomePage', 'SearchResultsPage', 'ProductPage', 'CartPage']
- Test classes: ['LoginSmokeTest', 'SearchAndAddToCartTest', 'CartCheckoutTest']
- Test groups: ['smoke', 'regression']

**Run commands:**
```bash
mvn test -Dgroups=smoke -Dheadless=true
```
```bash
mvn test -Dgroups=regression -Dheadless=true
```

# ecommerce-demo-automation

Generated Java Selenium + TestNG automation framework.

## Quick Start

```bash
# Compile only
mvn -q -DskipTests compile

# Run smoke tests headless
mvn test -Dgroups=smoke -Dheadless=true

# Run against a specific environment
mvn test -Denv=qa -Dgroups=regression -Dheadless=true

# Run with a different browser
mvn test -Dbrowser=firefox -Dgroups=smoke -Dheadless=true

# Run with visible browser (debugging)
mvn test -Dgroups=smoke -Dheadless=false
```

## Environments


- **dev**: `https://dev.example.com`

- **qa**: `https://qa.example.com`

- **prod**: `https://example.com`


## Browsers


- `chrome`

- `firefox`


## Reports

After a test run, find the HTML report at:

```
target/extent-reports/report.html
```

Failure screenshots are saved to:

```
target/screenshots/
```

## CI

GitHub Actions runs headless smoke tests on every push. See `.github/workflows/ui-tests.yml`.

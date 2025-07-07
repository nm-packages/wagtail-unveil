# Testing Guide

This guide covers all aspects of testing the wagtail-unveil package.

## Quick Start

For most development work, use the convenient `runtests.py` script:

```bash
python runtests.py --verbose
```

## Test Structure

The tests are located in `src/wagtail_unveil/tests/` and include:

- `test_views.py`: Tests for all the unveil report views and API endpoints

### Test Classes

- `UnveilReportsIndexViewTest`: Tests all report index routes (collection, document, form, etc.)
- `UnveilReportsJSONAPITest`: Tests JSON API endpoints with authentication

## Running Tests

### Using runtests.py (Recommended)

The `runtests.py` script provides the most convenient way to run tests with proper configuration:

```bash
# Basic usage - run all tests
python runtests.py

# Verbose output with detailed test execution
python runtests.py --verbose
python runtests.py -v 2

# Run without Python warnings
python runtests.py --no-warnings

# Stop on first failure for quick debugging
python runtests.py --failfast

# Keep test database between runs (faster for repeated testing)
python runtests.py --keepdb

# Run with DEBUG=True for debugging templates/views
python runtests.py --debug-mode

# Run in non-interactive mode (useful for CI)
python runtests.py --no-interactive

# Run specific test module
python runtests.py test_views

# Get help
python runtests.py --help
```

### Using Django's Test Command

You can also use Django's standard test runner:

```bash
# Run all wagtail_unveil tests
python manage.py test src.wagtail_unveil.tests

# Run specific test class
python manage.py test src.wagtail_unveil.tests.test_views.UnveilReportsIndexViewTest

# Run specific test method
python manage.py test src.wagtail_unveil.tests.test_views.UnveilReportsIndexViewTest.test_collection_index_route

# Run with verbose output
python manage.py test src.wagtail_unveil.tests --verbosity=2

# Keep test database
python manage.py test src.wagtail_unveil.tests --keepdb
```

### Using uv (Alternative)

If you prefer using uv:

```bash
uv run python manage.py test src.wagtail_unveil.tests
```

## Test Configuration

### Settings Override

Tests use the development settings (`example_project.settings.dev`) which include:

- **Static Files**: Uses `StaticFilesStorage` instead of `ManifestStaticFilesStorage` to avoid manifest collection requirements
- **Database**: SQLite in-memory database for speed
- **Debug**: Can be enabled with `--debug-mode`

### Test Database

- Uses SQLite in-memory database by default: `'file:memorydb_default?mode=memory&cache=shared'`
- Can be kept between runs with `--keepdb` for faster subsequent test execution

### Warning Configuration

When using `runtests.py`:

- **Warnings enabled by default**: Shows Python deprecation warnings, Django warnings, etc.
- **Can be disabled**: Use `--no-warnings` to suppress warning output
- **Helps catch issues**: Useful for seeing deprecation warnings and potential problems

## Tox Testing

For comprehensive testing across multiple Python/Django/Wagtail versions:

### Setup

```bash
uv pip install tox tox-uv
```

### Running Tox

```bash
# Run all test environments
tox

# List available environments
tox list

# Run specific environment
tox -e py313-wt64-dj52

# Run specific environments matching a pattern
tox -e py312-wt63-dj51,py313-wt64-dj52
```

### Supported Test Matrix

The package is tested against:

- **Python**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Wagtail**: 5.2, 6.0, 6.1, 6.2, 6.3, 6.4
- **Django**: 4.2, 5.1, 5.2

See `tox.ini` for the complete compatibility matrix.

## Test Development

### Adding New Tests

1. **Location**: Add new tests to `src/wagtail_unveil/tests/`
2. **Naming**: Follow the pattern `test_*.py`
3. **Structure**: Use Django's `TestCase` class
4. **Setup**: Include proper test setup in `setUp()` method

### Test Best Practices

1. **Use descriptive names**: Test method names should clearly describe what they test
2. **Test one thing**: Each test method should test a single aspect
3. **Use assertions**: Use Django's assertion methods like `assertContains`, `assertEqual`
4. **Clean data**: Use test fixtures or factories for test data
5. **Test edge cases**: Include tests for error conditions and edge cases

### Example Test Structure

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class MyFeatureTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123"
        )
        self.client.login(username="admin", password="password123")

    def test_feature_works(self):
        url = reverse("my_feature_url")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Expected Content")
```

## Debugging Tests

### Using --debug-mode

```bash
python runtests.py --debug-mode test_views.UnveilReportsIndexViewTest.test_collection_index_route
```

This enables Django's DEBUG mode, which provides:

- Detailed error pages
- Template debugging information
- Better traceback information

### Using --failfast

```bash
python runtests.py --failfast
```

Stops execution on the first test failure, making it easier to focus on one issue at a time.

### Using --verbose

```bash
python runtests.py --verbose
```

Shows detailed output including:

- Individual test execution
- Database operations
- Migration details
- System check results

## Continuous Integration

For CI environments, use:

```bash
python runtests.py --no-interactive --no-warnings
```

This provides:

- Non-interactive execution
- Suppressed warnings (cleaner CI output)
- Proper exit codes for CI systems

## Troubleshooting

### Common Issues

1. **Static files manifest errors**: Fixed by using `StaticFilesStorage` in dev settings
2. **Database permission errors**: Use in-memory database or ensure proper permissions
3. **Import errors**: Ensure all dependencies are installed and virtual environment is activated

### Performance Tips

1. **Use --keepdb**: Keeps test database between runs for faster execution
2. **Use specific test selection**: Run only the tests you're working on
3. **Use --failfast**: Stop on first failure to save time during debugging

### Getting Help

1. **Check test output**: Use `--verbose` for detailed information
2. **Enable warnings**: Remove `--no-warnings` to see potential issues
3. **Run single test**: Isolate the problem by running one test at a time

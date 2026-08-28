---
name: Python Unit Test Guideline 2.0
description: Guidelines for Python unit testing
metadata:
  owner: Gaetan Semet <gaetan.semet@ampere.cars>
  keywords: [python, testing, unit-test, pytest, fixtures]
  guideline-id: 0b2bac4f-c5f2-4c24-a3cb-aecf5df02dbf
---

# Python Unit Test Guidelines

Use pytest, function-based tests, and pytest fixtures.

## Rules

1. Write standalone `def test_*():` functions, not test classes.
2. For multiple inputs with the same logic, use `@Parametrization` from the
   `pytest-parametrization` dev dependency, not `pytest.mark.parametrize`.
3. Use pytest fixtures instead of manual setup/teardown, including
   `tmp_path`, `monkeypatch`, `caplog`, and `mocker`.
4. Keep test code at most 120 characters wide. Preserve indentation in inline
   code and strings, using `textwrap.dedent()` when needed.
5. Put `test_<modulename>.py` in the `tests/` subdirectory parallel to its
   source module; for example, tests for `src/craftman/models.py` go in
   `src/craftman/tests/test_models.py`.

## Tools

- Framework: pytest.
- Parametrization: `pytest-parametrization`, not `pytest.mark.parametrize`.
- Fixtures: `tmp_path`, `monkeypatch`, `mocker`, and `caplog`.
- Set appropriate function, module, or session fixture scopes.

## Validation

Find the project's test gate, such as `just tests-coverage`, and run the full
test suite with coverage reporting.

## Positive example

```python
def test_file_operations(tmp_path):
   config_file = tmp_path / "config.yml"
   config_file.write_text("key: value")

   assert config_file.exists()
   assert "key:" in config_file.read_text()
```

Using pytest-parametrization:

```python
from parametrization import Parametrization

@Parametrization.autodetect_parameters()
@Parametrization.case(name="valid_input", input_val=1, expected=2)
@Parametrization.case("zero_input", input_val=0, expected=1)
@Parametrization.case("negative_input", input_val=-1, expected=0)
def test_increment_function(input_val, expected):
    assert increment(input_val) == expected
```

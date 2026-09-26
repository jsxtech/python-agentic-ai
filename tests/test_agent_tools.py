"""Offline unit tests for agent.py pure-logic tools (calculate, run_code).

No network/API calls are made; these exercise local computation only.
"""
import time

from agent import calculate, run_code

# --- calculate -------------------------------------------------------------

def test_calculate_basic_arithmetic():
    assert calculate("2 + 3 * 4") == "14"


def test_calculate_division():
    assert calculate("10 / 4") == "2.5"


def test_calculate_unary():
    assert calculate("-5 + 2") == "-3"


def test_calculate_power_within_limit():
    assert calculate("2 ** 10") == "1024"


def test_calculate_rejects_large_exponent():
    assert "Exponent too large" in calculate("2 ** 5000")


def test_calculate_rejects_expression_exponent():
    assert "Exponent must be a simple number" in calculate("2 ** (3 + 1)")


def test_calculate_division_by_zero():
    assert calculate("1 / 0") == "Error: Division by zero"


def test_calculate_rejects_names():
    # Attribute/name access must be rejected by the AST whitelist.
    assert calculate("__import__('os')").startswith("Error")


def test_calculate_invalid_syntax():
    assert calculate("2 +") == "Error: Invalid mathematical expression"


# --- run_code --------------------------------------------------------------

def test_run_code_normal_output():
    assert run_code("print(sum(range(5)))") == "10\n"


def test_run_code_no_output_message():
    assert run_code("x = 1 + 1") == "Code executed successfully (no output)"


def test_run_code_blocks_import():
    assert run_code("import os") == "Error: Imports are not allowed in sandboxed code"


def test_run_code_blocks_dunder():
    result = run_code("().__class__")
    assert "dunder" in result


def test_run_code_blocks_dangerous_builtin():
    result = run_code("open('x')")
    assert "not allowed" in result


def test_run_code_reports_runtime_error():
    assert "division by zero" in run_code("print(1/0)").lower()


def test_run_code_syntax_error():
    assert run_code("print(").startswith("Error: Invalid syntax")


def test_run_code_infinite_loop_is_killed():
    start = time.time()
    result = run_code("while True:\n    pass")
    elapsed = time.time() - start
    # Must terminate (CPU limit or wall-clock timeout) within a bounded window,
    # proving the runaway process is actually killed rather than leaked.
    assert elapsed < 15
    assert result.startswith("Error")

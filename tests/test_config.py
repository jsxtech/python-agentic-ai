"""Offline unit tests for pure-logic helpers in config.py.

These tests do not make any network/API calls.
"""
import os

import config
from config import (
    extract_json_array,
    extract_json_object,
    first_text,
    is_path_safe,
)


class _Block:
    """Minimal stand-in for an Anthropic content block."""

    def __init__(self, text=None):
        if text is not None:
            self.text = text


class _Resp:
    def __init__(self, content):
        self.content = content


# --- first_text -----------------------------------------------------------

def test_first_text_returns_first_text_block():
    resp = _Resp([_Block("hello"), _Block("world")])
    assert first_text(resp) == "hello"


def test_first_text_skips_non_text_blocks():
    resp = _Resp([_Block(), _Block("real")])  # first block has no .text
    assert first_text(resp) == "real"


def test_first_text_empty_content_returns_default():
    assert first_text(_Resp([])) == ""
    assert first_text(_Resp([]), default="fallback") == "fallback"


def test_first_text_none_content_returns_default():
    class NoContent:
        content = None

    assert first_text(NoContent(), default="x") == "x"


# --- extract_json_object ---------------------------------------------------

def test_extract_json_object_plain():
    assert extract_json_object('{"a": 1}') == {"a": 1}


def test_extract_json_object_embedded_in_text():
    text = 'Here you go: {"a": 1, "b": [2, 3]} -- done'
    assert extract_json_object(text) == {"a": 1, "b": [2, 3]}


def test_extract_json_object_ignores_braces_in_strings():
    text = 'prefix {"msg": "a } b { c"} suffix'
    assert extract_json_object(text) == {"msg": "a } b { c"}


def test_extract_json_object_nested():
    text = 'noise {"outer": {"inner": 1}} noise'
    assert extract_json_object(text) == {"outer": {"inner": 1}}


def test_extract_json_object_none_when_absent():
    assert extract_json_object("no json here") is None


# --- extract_json_array ----------------------------------------------------

def test_extract_json_array_plain():
    assert extract_json_array("[1, 2, 3]") == [1, 2, 3]


def test_extract_json_array_embedded():
    text = 'steps: [{"id": 1}, {"id": 2}] end'
    assert extract_json_array(text) == [{"id": 1}, {"id": 2}]


def test_extract_json_array_ignores_brackets_in_strings():
    text = '["a ] b", "c"]'
    assert extract_json_array(text) == ["a ] b", "c"]


def test_extract_json_array_none_when_absent():
    assert extract_json_array("nothing") is None


# --- is_path_safe ----------------------------------------------------------

def test_is_path_safe_relative_within_sandbox():
    assert is_path_safe("notes.txt") is True
    assert is_path_safe("sub/dir/notes.txt") is True


def test_is_path_safe_rejects_traversal():
    assert is_path_safe("../config.py") is False
    assert is_path_safe("../../etc/passwd") is False


def test_is_path_safe_rejects_absolute_outside():
    assert is_path_safe("/etc/passwd") is False


def test_is_path_safe_accepts_absolute_inside():
    inside = os.path.join(config.SANDBOX_DIR, "a.txt")
    assert is_path_safe(inside) is True


def test_is_path_safe_sandbox_root_itself():
    assert is_path_safe(config.SANDBOX_DIR) is True

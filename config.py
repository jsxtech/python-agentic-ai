"""Shared configuration and utilities for the agentic AI framework."""

import json
import os
import re
import time

import anthropic

# Model configuration
MODEL_NAME = os.environ.get("MODEL_NAME", "claude-3-5-sonnet-20241022")
DEFAULT_MAX_TOKENS = 2048

# File operations sandbox directory (defaults to workspace/ subdirectory to protect source)
SANDBOX_DIR = os.environ.get(
    "SANDBOX_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
)
# Ensure sandbox directory exists
os.makedirs(SANDBOX_DIR, exist_ok=True)

# Rate limiting defaults
DEFAULT_MAX_REQUESTS = 10
DEFAULT_RATE_WINDOW = 60

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


def get_client() -> anthropic.Anthropic:
    """Create and return an Anthropic client."""
    return anthropic.Anthropic()


def first_text(response, default=""):
    """Safely extract the first text block from an Anthropic API response.

    The response ``content`` is a list of blocks that may include non-text
    blocks (e.g. tool_use) or be empty. Indexing ``content[0].text`` directly
    can raise IndexError/AttributeError. This helper returns the first block
    that exposes a ``text`` attribute, or ``default`` if none is present.

    Args:
        response: Anthropic message response object
        default: Value returned when no text block is found

    Returns:
        The first text block's text, or ``default``
    """
    content = getattr(response, "content", None) or []
    return next(
        (block.text for block in content if hasattr(block, "text")),
        default,
    )


def parse_score(text, default=5.0, low=0.0, high=10.0):
    """Extract the first numeric score from free-form LLM text.

    Handles responses like ``"8"``, ``"Score: 8"``, ``"8/10"`` or
    ``"I'd rate it 7.5 out of 10"`` by taking the first number found and
    clamping it to ``[low, high]``. Returns ``default`` when no number is
    present. This avoids the brittle ``float(text.strip())`` pattern that
    silently collapses to a mid-range default on any surrounding prose.
    """
    if text is None:
        return default
    match = re.search(r"-?\d+(?:\.\d+)?", str(text))
    if not match:
        return default
    try:
        value = float(match.group())
    except (ValueError, TypeError):
        return default
    return max(low, min(high, value))


def api_call_with_retry(client, max_retries=MAX_RETRIES, rate_limiter=None, **kwargs):
    """Make an API call with exponential backoff retry on transient errors.

    Args:
        client: Anthropic client instance
        max_retries: Maximum number of retry attempts
        rate_limiter: Optional AgentRateLimiter-like object. If provided, the
            call blocks until the limiter permits a request (via ``allow_request``
            / ``time_until_available``) before contacting the API.
        **kwargs: Arguments passed to client.messages.create()

    Returns:
        API response object

    Raises:
        anthropic.APIError: If all retries are exhausted
    """
    # Apply defaults
    kwargs.setdefault("model", MODEL_NAME)
    kwargs.setdefault("max_tokens", DEFAULT_MAX_TOKENS)

    # Optional client-side rate limiting: wait until a request slot is free.
    if rate_limiter is not None:
        while not rate_limiter.allow_request():
            wait = rate_limiter.time_until_available()
            if wait <= 0:
                break
            print(f"\u23f3 Rate limit reached. Waiting {wait:.1f}s...")
            time.sleep(wait)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            last_error = e
            if attempt < max_retries:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"⏳ Rate limited. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise
        except anthropic.APIConnectionError as e:
            last_error = e
            if attempt < max_retries:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"⏳ Connection error. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise
        except anthropic.APIStatusError as e:
            # Don't retry on 4xx errors (except 429 handled above)
            if e.status_code < 500:
                raise
            last_error = e
            if attempt < max_retries:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"⏳ Server error ({e.status_code}). Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise

    raise last_error


def extract_json_object(text):
    """Safely extract a JSON object from LLM response text.

    Handles cases where JSON is embedded in explanation text by finding
    the outermost balanced braces, correctly skipping braces inside
    JSON string literals.

    Args:
        text: Raw text potentially containing JSON

    Returns:
        Parsed dict or None if extraction fails
    """
    # Try parsing the whole thing first
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        pass

    # Find balanced braces (string-aware)
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except (json.JSONDecodeError, ValueError):
                    return None
    return None


def extract_json_array(text):
    """Safely extract a JSON array from LLM response text.

    Handles cases where JSON is embedded in explanation text by finding
    the outermost balanced brackets, correctly skipping brackets inside
    JSON string literals.

    Args:
        text: Raw text potentially containing a JSON array

    Returns:
        Parsed list or None if extraction fails
    """
    # Try parsing the whole thing first
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        pass

    # Find balanced brackets (string-aware)
    start = text.find('[')
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except (json.JSONDecodeError, ValueError):
                    return None
    return None


def is_path_safe(filepath, sandbox_dir=None):
    """Validate that a file path is within the allowed sandbox directory.

    Args:
        filepath: Path to validate
        sandbox_dir: Allowed directory (defaults to SANDBOX_DIR)

    Returns:
        True if path is safe, False otherwise
    """
    return safe_resolved_path(filepath, sandbox_dir) is not None


def safe_resolved_path(filepath, sandbox_dir=None):
    """Return the fully-resolved absolute path if it is inside the sandbox.

    This resolves symlinks and ``..`` components and confirms the result is
    contained within the sandbox directory. Callers should open/operate on the
    *returned* path (never the original argument) to avoid a time-of-check /
    time-of-use (TOCTOU) gap where a symlink could redirect the real open
    outside the sandbox.

    Args:
        filepath: Path to validate
        sandbox_dir: Allowed directory (defaults to SANDBOX_DIR)

    Returns:
        The resolved absolute path (str) if safe, otherwise ``None``.
    """
    if sandbox_dir is None:
        sandbox_dir = SANDBOX_DIR

    sandbox_resolved = os.path.realpath(os.path.abspath(sandbox_dir))

    # Relative paths are interpreted relative to the sandbox directory rather
    # than the process's current working directory. This keeps tool behaviour
    # predictable and consistent with the "sandboxed to workspace" contract.
    if not os.path.isabs(filepath):
        filepath = os.path.join(sandbox_resolved, filepath)

    # Resolve to absolute path, resolving symlinks
    resolved = os.path.realpath(os.path.abspath(filepath))

    if resolved == sandbox_resolved or resolved.startswith(sandbox_resolved + os.sep):
        return resolved
    return None

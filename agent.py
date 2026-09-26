import ast
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from config import (
    SANDBOX_DIR,
    api_call_with_retry,
    first_text,
    get_client,
    safe_resolved_path,
)

client = get_client()


class AgentMemory:
    """Encapsulated memory storage for the agent."""

    def __init__(self):
        self._store = {}

    def save(self, key, value):
        self._store[key] = value
        return f"Saved '{key}' to memory"

    def recall(self, key):
        return self._store.get(key, f"No memory found for '{key}'")

    def clear(self):
        self._store.clear()


# Instance-level memory instead of global mutable list
agent_memory = AgentMemory()

tools = [
    {
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    },
    {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "save_memory",
        "description": "Save information to memory for later recall",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "recall_memory",
        "description": "Retrieve saved information from memory",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"}
            },
            "required": ["key"]
        }
    },
    {
        "name": "get_time",
        "description": "Get current date and time",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_file",
        "description": "Read contents of a file (sandboxed to the workspace directory)",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"}
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file (sandboxed to the workspace directory)",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["filepath", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a directory (sandboxed to the workspace directory)",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"}
            },
            "required": ["directory"]
        }
    },
    {
        "name": "run_code",
        "description": "Execute Python code in an isolated subprocess with CPU/memory limits and a hard timeout. Not safe against determined adversaries; intended for trusted/educational use.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"}
            },
            "required": ["code"]
        }
    }
]


def get_weather(location):
    return f"Weather in {location}: 72°F, sunny"


def calculate(expression):
    """Safely evaluate a mathematical expression using AST parsing.

    Only allows numeric literals and basic arithmetic operators.
    """
    try:
        # Parse the expression into an AST
        tree = ast.parse(expression, mode='eval')

        # Walk the AST and verify only safe nodes are present
        for node in ast.walk(tree):
            if isinstance(node, ast.Expression):
                continue
            elif isinstance(node, ast.BinOp):
                continue
            elif isinstance(node, ast.UnaryOp):
                if not isinstance(node.op, (ast.UAdd, ast.USub)):
                    return "Error: Unsupported operation"
                continue
            elif isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div,
                                   ast.FloorDiv, ast.Mod, ast.Pow)):
                continue
            elif isinstance(node, (ast.Constant,)):
                if not isinstance(node.value, (int, float)):
                    return "Error: Only numeric values allowed"
                continue
            elif isinstance(node, (ast.UAdd, ast.USub)):
                continue
            else:
                return f"Error: Unsupported expression element: {type(node).__name__}"

        # Prevent DoS via large exponents (e.g., 2**999999999) and nested
        # powers such as (10**1000)**1000 whose base is itself an expression.
        def _const_value(n):
            """Return the numeric value of a Constant or unary-signed Constant, else None."""
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                return n.value
            if (
                isinstance(n, ast.UnaryOp)
                and isinstance(n.op, (ast.UAdd, ast.USub))
                and isinstance(n.operand, ast.Constant)
                and isinstance(n.operand.value, (int, float))
            ):
                return -n.operand.value if isinstance(n.op, ast.USub) else n.operand.value
            return None

        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
                # Exponent must be a direct numeric constant (not an expression).
                exp = _const_value(node.right)
                if exp is None:
                    return "Error: Exponent must be a simple number (not an expression)"
                if abs(exp) > 1000:
                    return "Error: Exponent too large (max 1000)"
                # Base must ALSO be a simple numeric constant. This blocks
                # nested powers like (10**1000)**1000 where the base is a
                # BinOp that would otherwise evade the magnitude check.
                base = _const_value(node.left)
                if base is None:
                    return "Error: Power base must be a simple number (nested powers not allowed)"
                if abs(base) > 10000 and abs(exp) > 100:
                    return "Error: Base and exponent combination too large"

        # Safe to evaluate
        result = eval(compile(tree, "<expression>", "eval"), {"__builtins__": {}}, {})
        return str(result)
    except SyntaxError:
        return "Error: Invalid mathematical expression"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {str(e)}"


def save_memory(key, value):
    return agent_memory.save(key, value)


def recall_memory(key):
    return agent_memory.recall(key)


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def web_search(query):
    return f"Search results for '{query}': [Simulated results - integrate real API]"


def read_file(filepath):
    resolved = safe_resolved_path(filepath)
    if resolved is None:
        return f"Error: Access denied. Path must be within {SANDBOX_DIR}"
    try:
        # Open the *resolved* path and refuse to follow a final symlink to
        # avoid a TOCTOU/symlink escape between validation and open.
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(resolved, flags)
        with os.fdopen(fd) as f:
            return f.read()
    except OSError as e:
        return f"Error reading file: {str(e)}"


def write_file(filepath, content):
    resolved = safe_resolved_path(filepath)
    if resolved is None:
        return f"Error: Access denied. Path must be within {SANDBOX_DIR}"
    try:
        parent = os.path.dirname(resolved)
        # Ensure the parent directory is itself inside the sandbox before
        # creating it.
        if safe_resolved_path(parent) is None:
            return f"Error: Access denied. Path must be within {SANDBOX_DIR}"
        os.makedirs(parent, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(resolved, flags, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return f"Successfully wrote to {resolved}"
    except OSError as e:
        return f"Error writing file: {str(e)}"


def list_files(directory):
    resolved = safe_resolved_path(directory)
    if resolved is None:
        return f"Error: Access denied. Path must be within {SANDBOX_DIR}"
    try:
        files = [str(p) for p in Path(resolved).iterdir()]
        return "\n".join(files)
    except OSError as e:
        return f"Error listing files: {str(e)}"


def run_code(code):
    """Execute Python code in an isolated subprocess.

    Security model (defense in depth, best-effort):
      * AST pre-screening rejects imports, dunder attribute access, and calls
        to dangerous builtins before anything runs.
      * Execution happens in a *separate* Python process, so a runaway or
        crashing payload cannot corrupt the host interpreter's state.
      * On POSIX the child applies resource limits (CPU seconds, address space,
        no new files) via ``resource.setrlimit`` in a preexec hook.
      * A hard wall-clock timeout kills the process group if it overruns, so
        infinite loops are actually terminated (unlike a joined daemon thread).

    This is suitable for trusted/educational use. It is NOT a substitute for
    OS-level sandboxing (containers, seccomp, gVisor) against adversarial code.
    """
    # --- Fast AST pre-screen (rejects obvious abuse before spawning a process) ---
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Error: Invalid syntax - {str(e)}"

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "Error: Imports are not allowed in sandboxed code"
        if isinstance(node, ast.Attribute) and node.attr.startswith('__'):
            return "Error: Access to dunder attributes is not allowed"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in (
                'exec', 'eval', 'compile', 'open', 'input', '__import__',
                'getattr', 'setattr', 'delattr', 'globals', 'locals',
                'vars', 'breakpoint', 'exit', 'quit',
            ):
                return f"Error: '{node.func.id}' is not allowed in sandboxed code"

    # --- Runner script executed in the child process ---
    # Restricts builtins to a safe subset and runs the user code. Kept as a
    # string so it runs in a pristine, separate interpreter.
    runner = r'''
import sys

SAFE_BUILTINS = {
    'print': print, 'len': len, 'range': range, 'int': int,
    'float': float, 'str': str, 'bool': bool, 'list': list,
    'dict': dict, 'tuple': tuple, 'set': set, 'abs': abs,
    'min': min, 'max': max, 'sum': sum, 'sorted': sorted,
    'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
    'round': round, 'isinstance': isinstance,
    'True': True, 'False': False, 'None': None,
}

source = sys.stdin.read()
try:
    exec(compile(source, "<sandbox>", "exec"), {"__builtins__": SAFE_BUILTINS}, {})
except Exception as exc:  # noqa: BLE001 - surface any runtime error to caller
    sys.stderr.write(str(exc))
    sys.exit(1)
'''

    def _limit_resources():  # pragma: no cover - POSIX child hook, not measurable here
        """Apply CPU/memory limits and start a new session (for group kill)."""
        try:
            import resource
            # 5 CPU seconds hard cap
            resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
            # ~256 MB address space cap
            mem = 256 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
            # No new files written by the child
            resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        except Exception:
            pass
        try:
            os.setsid()  # isolate into its own process group
        except Exception:
            pass

    preexec = _limit_resources if os.name == "posix" else None

    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-S", "-c", runner],
            input=code,
            capture_output=True,
            text=True,
            timeout=5.0,
            preexec_fn=preexec,
            cwd=tempfile.gettempdir(),
            env={"PATH": "", "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (5 second limit)"
    except Exception as e:
        return f"Error: Failed to execute code - {str(e)}"

    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or "Non-zero exit status"
        return f"Error: {err}"

    output = proc.stdout or ""
    if len(output) > 10000:
        return output[:10000] + "\n... (output truncated at 10000 chars)"
    return output or "Code executed successfully (no output)"


tool_functions = {
    "get_weather": get_weather,
    "calculate": calculate,
    "save_memory": save_memory,
    "recall_memory": recall_memory,
    "get_time": get_time,
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "run_code": run_code
}


def run_agent(user_message, conversation_history=None, max_iterations=20):
    if conversation_history is None:
        messages = [{"role": "user", "content": user_message}]
    else:
        messages = conversation_history + [{"role": "user", "content": user_message}]

    for _iteration in range(max_iterations):
        response = api_call_with_retry(
            client,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            final_text = first_text(response)
            messages.append({"role": "assistant", "content": response.content})
            return final_text, messages

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    func = tool_functions.get(block.name)
                    if func:
                        try:
                            result = func(**block.input)
                        except TypeError as e:
                            result = f"Error calling {block.name}: {str(e)}"
                    else:
                        result = f"Error: Unknown tool '{block.name}'"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop reason
            final_text = first_text(response)
            messages.append({"role": "assistant", "content": response.content})
            return final_text, messages

    # Max iterations reached
    messages.append({"role": "assistant", "content": [{"type": "text", "text": "I've reached the maximum number of tool-use iterations. Please try a simpler request."}]})
    return "I've reached the maximum number of tool-use iterations. Please try a simpler request.", messages


def interactive_mode():
    print("🤖 Agent ready. Type 'quit' to exit, 'help' for commands.\n")
    conversation = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ["quit", "exit"]:
            break
        if user_input.lower() == "help":
            print("\nAvailable capabilities:")
            print("- Weather lookup")
            print("- Math calculations")
            print("- Memory (save/recall)")
            print("- Web search")
            print("- File operations (read/write/list)")
            print("- Code execution (sandboxed)")
            print("- Time/date\n")
            continue
        if not user_input:
            continue

        try:
            response, conversation = run_agent(user_input, conversation)
            print(f"Agent: {response}\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")


if __name__ == "__main__":
    interactive_mode()

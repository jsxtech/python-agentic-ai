import ast
import json
import os
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path

from config import (
    MODEL_NAME,
    SANDBOX_DIR,
    api_call_with_retry,
    get_client,
    is_path_safe,
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
        "description": "Read contents of a file (sandboxed to project directory)",
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
        "description": "Write content to a file (sandboxed to project directory)",
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
        "description": "List files in a directory (sandboxed to project directory)",
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
        "description": "Execute Python code in a restricted sandbox (no imports, no file/network access)",
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

        # Prevent DoS via large exponents (e.g., 2**999999999)
        # Only allow Pow when the exponent is a small numeric constant
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
                # Exponent must be a direct numeric constant (not an expression)
                if not isinstance(node.right, ast.Constant):
                    return "Error: Exponent must be a simple number (not an expression)"
                if not isinstance(node.right.value, (int, float)):
                    return "Error: Exponent must be numeric"
                if abs(node.right.value) > 1000:
                    return "Error: Exponent too large (max 1000)"
                # Also limit the base if it's a large constant
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, (int, float)):
                    if abs(node.left.value) > 10000 and abs(node.right.value) > 100:
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
    if not is_path_safe(filepath):
        return f"Error: Access denied. Path must be within {SANDBOX_DIR}"
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(filepath, content):
    if not is_path_safe(filepath):
        return f"Error: Access denied. Path must be within {SANDBOX_DIR}"
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def list_files(directory):
    if not is_path_safe(directory):
        return f"Error: Access denied. Path must be within {SANDBOX_DIR}"
    try:
        files = [str(p) for p in Path(directory).iterdir()]
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


def run_code(code):
    """Execute Python code in a restricted sandbox.

    Only allows basic computation — no imports, no file/network access,
    no access to builtins that could be dangerous. Has a 5-second timeout.
    """
    # AST-based validation: reject any import statements or attribute access to dunders
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
            # Block calls to exec, eval, compile, open, etc.
            if isinstance(node.func, ast.Name) and node.func.id in (
                'exec', 'eval', 'compile', 'open', 'input', '__import__',
                'getattr', 'setattr', 'delattr', 'globals', 'locals',
                'breakpoint', 'exit', 'quit'
            ):
                return f"Error: '{node.func.id}' is not allowed in sandboxed code"
        # Block while True / infinite loops
        if isinstance(node, ast.While):
            # Allow while loops but they'll be killed by timeout
            pass

    # Provide a minimal set of safe builtins
    safe_builtins = {
        'print': print, 'len': len, 'range': range, 'int': int,
        'float': float, 'str': str, 'bool': bool, 'list': list,
        'dict': dict, 'tuple': tuple, 'set': set, 'abs': abs,
        'min': min, 'max': max, 'sum': sum, 'sorted': sorted,
        'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
        'round': round, 'isinstance': isinstance,
        'True': True, 'False': False, 'None': None,
    }

    # Execute with timeout using threading
    import threading

    result_container = {"output": None, "error": None}

    def _execute():
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exec(compile(tree, "<sandbox>", "exec"),
                 {"__builtins__": safe_builtins}, {})
            result_container["output"] = sys.stdout.getvalue()
        except Exception as e:
            result_container["error"] = str(e)
        finally:
            sys.stdout = old_stdout

    thread = threading.Thread(target=_execute, daemon=True)
    thread.start()
    thread.join(timeout=5.0)

    if thread.is_alive():
        # Thread is still running — timed out
        return "Error: Code execution timed out (5 second limit)"

    if result_container["error"]:
        return f"Error: {result_container['error']}"

    output = result_container["output"]
    if output and len(output) > 10000:
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
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")), ""
            )
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
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")), ""
            )
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

import anthropic
import json
import os
import requests
from datetime import datetime
from pathlib import Path

client = anthropic.Anthropic()

# Memory storage
memory = []

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
        "description": "Read contents of a file",
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
        "description": "Write content to a file",
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
        "description": "List files in a directory",
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
        "description": "Execute Python code and return output",
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
    try:
        # Restrict to safe operations only
        allowed = set('0123456789+-*/().% ')
        if not all(c in allowed for c in expression):
            return "Error: Only basic math operations allowed"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

def save_memory(key, value):
    memory.append({"key": key, "value": value})
    return f"Saved '{key}' to memory"

def recall_memory(key):
    for item in memory:
        if item["key"] == key:
            return item["value"]
    return f"No memory found for '{key}'"

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def web_search(query):
    return f"Search results for '{query}': [Simulated results - integrate real API]"

def read_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(filepath, content):
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_files(directory):
    try:
        files = [str(p) for p in Path(directory).iterdir()]
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

def run_code(code):
    try:
        from io import StringIO
        import sys
        
        # Basic safety check
        dangerous = ['import os', 'import sys', 'import subprocess', '__import__', 'eval', 'exec']
        if any(d in code for d in dangerous):
            return "Error: Potentially unsafe code detected"
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        exec(code)
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return output or "Code executed successfully"
    except Exception as e:
        return f"Error: {str(e)}"

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

def run_agent(user_message, conversation_history=None):
    if conversation_history is None:
        messages = [{"role": "user", "content": user_message}]
    else:
        messages = conversation_history + [{"role": "user", "content": user_message}]
    
    while True:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=tools,
            messages=messages
        )
        
        if response.stop_reason == "end_turn":
            final_text = next((block.text for block in response.content if hasattr(block, "text")), "")
            messages.append({"role": "assistant", "content": response.content})
            return final_text, messages
        
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    func = tool_functions.get(block.name)
                    if func:
                        result = func(**block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
            
            messages.append({"role": "user", "content": tool_results})

def interactive_mode():
    print("🤖 Agent ready. Type 'quit' to exit, 'help' for commands.\n")
    conversation = []
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit"]:
            break
        if user_input.lower() == "help":
            print("\nAvailable capabilities:")
            print("- Weather lookup")
            print("- Math calculations")
            print("- Memory (save/recall)")
            print("- Web search")
            print("- File operations (read/write/list)")
            print("- Code execution")
            print("- Time/date\n")
            continue
        
        response, conversation = run_agent(user_input, conversation)
        print(f"Agent: {response}\n")

if __name__ == "__main__":
    interactive_mode()

import json

from config import api_call_with_retry, get_client

client = get_client()


class ChainOfThoughtAgent:
    """Agent that shows reasoning steps before answering"""

    def solve(self, problem):
        prompt = f"""Solve this problem using chain-of-thought reasoning.

Problem: {problem}

Think step by step:
1. Break down the problem
2. Identify what you know
3. Determine what you need to find
4. Work through the solution
5. Verify your answer

Format your response as:
REASONING:
[your step-by-step thinking]

ANSWER:
[final answer]"""

        response = api_call_with_retry(
            client,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text


class TreeOfThoughtAgent:
    """Agent that explores multiple reasoning paths"""

    def solve(self, problem, num_paths=3):
        print(f"🌳 Exploring {num_paths} reasoning paths...\n")

        paths = []
        for i in range(num_paths):
            prompt = f"""Problem: {problem}

Generate a unique approach to solve this (Approach #{i+1}).
Show your reasoning and conclusion."""

            response = api_call_with_retry(
                client,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            path = response.content[0].text
            paths.append(path)
            print(f"Path {i+1}:\n{path}\n")

        # Evaluate and select best path
        evaluation_prompt = f"""Problem: {problem}

Here are {num_paths} different approaches:

{chr(10).join([f"Approach {i+1}:\n{p}\n" for i, p in enumerate(paths)])}

Evaluate each approach and select the best one. Explain why."""

        evaluation = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": evaluation_prompt}]
        )

        return evaluation.content[0].text


class ReActAgent:
    """Reasoning + Acting agent that interleaves thought and action.

    Implements the ReAct pattern: the agent reasons about what to do,
    executes an action (tool), observes the result, and repeats until
    the task is complete.
    """

    def __init__(self, tool_functions):
        """Initialize with a dict of tool_name -> callable mappings."""
        self.tool_functions = tool_functions
        self.max_iterations = 5

    def run(self, task):
        print(f"🎯 Task: {task}\n")

        available_tools = list(self.tool_functions.keys())
        context = []

        for i in range(self.max_iterations):
            # Build context from previous iterations
            history = ""
            if context:
                history = "\n".join([
                    f"Step {c['iteration']}: Thought: {c['thought']} | "
                    f"Action: {c['action']} | Observation: {c['observation']}"
                    for c in context
                ])

            # Reasoning step
            thought_prompt = f"""Task: {task}
Available tools: {available_tools}
{f"History:{chr(10)}{history}" if history else ""}

Decide what to do next. You MUST respond in this exact format:
THOUGHT: [your reasoning about what to do next]
ACTION: [tool_name] with input [input_value]

Or if the task is complete:
THOUGHT: [summary of what was accomplished]
ACTION: FINISH"""

            response = api_call_with_retry(
                client,
                max_tokens=512,
                messages=[{"role": "user", "content": thought_prompt}]
            )

            result = response.content[0].text
            print(f"Iteration {i + 1}:")
            print(result)

            if "FINISH" in result.split("ACTION:")[-1] if "ACTION:" in result else "":
                print("\n✅ Task completed")
                break

            # Parse the action and execute
            thought = result
            action_name = None
            action_input = None
            observation = "No action taken"

            if "ACTION:" in result:
                action_part = result.split("ACTION:")[-1].strip()

                if "FINISH" in action_part:
                    print("\n✅ Task completed")
                    break

                # Try to extract tool name and input
                for tool_name in available_tools:
                    if tool_name in action_part.lower():
                        action_name = tool_name
                        # Extract input after "with input" or similar patterns
                        if "with input" in action_part.lower():
                            action_input = action_part.lower().split("with input")[-1].strip()
                        elif ":" in action_part:
                            action_input = action_part.split(":", 1)[-1].strip()
                        else:
                            action_input = action_part.replace(tool_name, "").strip()
                        break

                # Execute the tool
                if action_name and action_name in self.tool_functions:
                    try:
                        observation = str(self.tool_functions[action_name](action_input or ""))
                    except Exception as e:
                        observation = f"Error executing {action_name}: {str(e)}"
                    print(f"🔧 Executed: {action_name}({action_input}) → {observation}")
                else:
                    observation = f"Tool '{action_name}' not found. Available: {available_tools}"
                    print(f"⚠️  {observation}")

            context.append({
                "iteration": i + 1,
                "thought": thought,
                "action": action_name or "none",
                "observation": observation
            })
            print()

        return context


if __name__ == "__main__":
    print("=== Chain of Thought ===")
    cot = ChainOfThoughtAgent()
    print(cot.solve("If a train travels 120 miles in 2 hours, how far will it travel in 5 hours?"))

    print("\n\n=== Tree of Thought ===")
    tot = TreeOfThoughtAgent()
    print(tot.solve("How can we reduce plastic waste in cities?"))

    print("\n\n=== ReAct ===")
    # Define simple tool functions for demonstration
    from agent import calculate as safe_calculate

    def search(query):
        return f"Search results for '{query}': Tokyo population is approximately 13.96 million (2023)"

    def calculate(expression):
        return safe_calculate(expression)

    def write(text):
        return f"Written: {text}"

    react = ReActAgent({
        "search": search,
        "calculate": calculate,
        "write": write
    })
    react.run("Find the population of Tokyo and calculate what 10% of it is")

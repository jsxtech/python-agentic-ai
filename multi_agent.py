from agent import tool_functions, tools
from config import api_call_with_retry, first_text, get_client

client = get_client()


class Agent:
    def __init__(self, name, role, specialized_tools=None):
        self.name = name
        self.role = role
        self.tools = specialized_tools or tools
        self.memory = []

    def run(self, task, context="", max_iterations=20):
        """Run the agent with full multi-round tool use support."""
        messages = [{"role": "user", "content": f"Role: {self.role}\nContext: {context}\nTask: {task}"}]

        for _iteration in range(max_iterations):
            response = api_call_with_retry(
                client,
                tools=self.tools,
                messages=messages
            )

            if response.stop_reason == "end_turn":
                return first_text(response)

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
                # Unexpected stop reason — return whatever text is available
                return first_text(response)

        return "Max iterations reached. Could not complete the task."


class MultiAgentSystem:
    def __init__(self):
        self.agents = {
            "researcher": Agent("Researcher", "Research and gather information"),
            "coder": Agent("Coder", "Write and debug code"),
            "analyst": Agent("Analyst", "Analyze data and provide insights"),
            "planner": Agent("Planner", "Break down tasks and create plans")
        }

    def delegate(self, task):
        print(f"\n🎯 Task: {task}\n")

        # Planner breaks down the task
        plan = self.agents["planner"].run(f"Break down this task into steps: {task}")
        print(f"📋 Planner: {plan}\n")

        # Researcher gathers info
        research = self.agents["researcher"].run(f"Research: {task}", plan)
        print(f"🔍 Researcher: {research}\n")

        # Analyst provides insights
        analysis = self.agents["analyst"].run(
            f"Analyze: {task}", f"Plan: {plan}\nResearch: {research}"
        )
        print(f"📊 Analyst: {analysis}\n")

        # Coder implements if needed
        if "code" in task.lower() or "implement" in task.lower():
            code = self.agents["coder"].run(f"Implement: {task}", f"Analysis: {analysis}")
            print(f"💻 Coder: {code}\n")

        return "Task completed by multi-agent system"


if __name__ == "__main__":
    system = MultiAgentSystem()
    system.delegate("Create a simple web scraper")

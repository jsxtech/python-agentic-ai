import anthropic
from agent import tools, tool_functions

client = anthropic.Anthropic()

class Agent:
    def __init__(self, name, role, specialized_tools=None):
        self.name = name
        self.role = role
        self.tools = specialized_tools or tools
        self.memory = []
    
    def run(self, task, context=""):
        messages = [{"role": "user", "content": f"Role: {self.role}\nContext: {context}\nTask: {task}"}]
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=self.tools,
            messages=messages
        )
        
        if response.stop_reason == "end_turn":
            return next((block.text for block in response.content if hasattr(block, "text")), "")
        
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
            
            final_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=messages
            )
            return next((block.text for block in final_response.content if hasattr(block, "text")), "")

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
        analysis = self.agents["analyst"].run(f"Analyze: {task}", f"Plan: {plan}\nResearch: {research}")
        print(f"📊 Analyst: {analysis}\n")
        
        # Coder implements if needed
        if "code" in task.lower() or "implement" in task.lower():
            code = self.agents["coder"].run(f"Implement: {task}", f"Analysis: {analysis}")
            print(f"💻 Coder: {code}\n")
        
        return "Task completed by multi-agent system"

if __name__ == "__main__":
    system = MultiAgentSystem()
    system.delegate("Create a simple web scraper")

import anthropic
import json
from collections import deque

client = anthropic.Anthropic()

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
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
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
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
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
        
        evaluation = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": evaluation_prompt}]
        )
        
        return evaluation.content[0].text

class ReActAgent:
    """Reasoning + Acting agent that interleaves thought and action"""
    
    def __init__(self, tools):
        self.tools = tools
        self.max_iterations = 5
    
    def run(self, task):
        print(f"🎯 Task: {task}\n")
        
        context = []
        for i in range(self.max_iterations):
            # Reasoning step
            thought_prompt = f"""Task: {task}
Context so far: {json.dumps(context)}

Think: What should I do next? What tool should I use?
Respond with: THOUGHT: [your reasoning]
ACTION: [tool_name or FINISH]"""
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": thought_prompt}]
            )
            
            result = response.content[0].text
            print(f"Iteration {i+1}:")
            print(result)
            
            if "FINISH" in result:
                print("\n✅ Task completed")
                break
            
            # Simulate action
            context.append({"iteration": i+1, "thought": result})
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
    react = ReActAgent(["search", "calculate", "write"])
    react.run("Find the population of Tokyo and calculate what 10% of it is")

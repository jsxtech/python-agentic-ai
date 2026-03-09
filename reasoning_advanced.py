import anthropic
import json
from typing import List, Dict, Any

client = anthropic.Anthropic()

class TaskDecomposer:
    """Recursively decomposes complex tasks"""
    
    def decompose(self, task, max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return {"task": task, "subtasks": [], "atomic": True}
        
        prompt = f"""Task: {task}

Can this be broken into smaller subtasks? If yes, list 2-4 subtasks. If no, say "ATOMIC".

Format: {{"atomic": true/false, "subtasks": ["...", "..."]}}"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text
        
        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            data = json.loads(result[start:end])
            
            if data.get("atomic", False) or not data.get("subtasks"):
                return {"task": task, "subtasks": [], "atomic": True}
            
            subtasks = []
            for subtask in data["subtasks"]:
                subtasks.append(self.decompose(subtask, max_depth, current_depth + 1))
            
            return {"task": task, "subtasks": subtasks, "atomic": False}
        except:
            return {"task": task, "subtasks": [], "atomic": True}
    
    def visualize(self, tree, indent=0):
        print("  " * indent + f"- {tree['task']}")
        for subtask in tree.get("subtasks", []):
            self.visualize(subtask, indent + 1)

class ConstraintSolver:
    """Solves problems with constraints"""
    
    def solve(self, problem, constraints):
        print(f"🎯 Problem: {problem}")
        print(f"⚠️  Constraints: {constraints}\n")
        
        prompt = f"""Problem: {problem}

Constraints:
{chr(10).join([f"- {c}" for c in constraints])}

Find a solution that satisfies ALL constraints. Show your reasoning:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        solution = response.content[0].text
        
        # Verify constraints
        verify_prompt = f"""Problem: {problem}
Solution: {solution}
Constraints: {constraints}

Does this solution satisfy all constraints? Respond with JSON:
{{"satisfied": true/false, "violations": []}}"""
        
        verify_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": verify_prompt}]
        )
        
        print(f"Solution: {solution}")
        print(f"\nVerification: {verify_response.content[0].text}")
        
        return solution

class AnalogyAgent:
    """Solves problems using analogical reasoning"""
    
    def solve_by_analogy(self, problem, source_domain):
        print(f"🎯 Problem: {problem}")
        print(f"🔄 Using analogy from: {source_domain}\n")
        
        # Find analogy
        analogy_prompt = f"""Problem: {problem}
Source domain: {source_domain}

Find an analogous situation in {source_domain} that maps to this problem:"""
        
        analogy_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": analogy_prompt}]
        )
        
        analogy = analogy_response.content[0].text
        print(f"Analogy: {analogy}\n")
        
        # Transfer solution
        transfer_prompt = f"""Problem: {problem}
Analogy: {analogy}

Transfer the solution approach from the analogy to solve the original problem:"""
        
        solution_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": transfer_prompt}]
        )
        
        solution = solution_response.content[0].text
        print(f"Solution: {solution}")
        
        return solution

class CausalReasoningAgent:
    """Reasons about cause and effect"""
    
    def analyze_causality(self, observation):
        print(f"🔍 Observation: {observation}\n")
        
        # Identify causes
        cause_prompt = f"""Observation: {observation}

What are the likely causes? List 3-5 potential causes with confidence levels:"""
        
        cause_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": cause_prompt}]
        )
        
        causes = cause_response.content[0].text
        print(f"Potential causes:\n{causes}\n")
        
        # Predict effects
        effect_prompt = f"""Observation: {observation}
Causes: {causes}

What are the likely downstream effects? Consider short-term and long-term:"""
        
        effect_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": effect_prompt}]
        )
        
        effects = effect_response.content[0].text
        print(f"Predicted effects:\n{effects}\n")
        
        # Interventions
        intervention_prompt = f"""Observation: {observation}
Causes: {causes}
Effects: {effects}

What interventions could change the outcome?"""
        
        intervention_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": intervention_prompt}]
        )
        
        interventions = intervention_response.content[0].text
        print(f"Possible interventions:\n{interventions}")
        
        return {"causes": causes, "effects": effects, "interventions": interventions}

if __name__ == "__main__":
    print("=== Task Decomposer ===")
    decomposer = TaskDecomposer()
    tree = decomposer.decompose("Build a social media platform")
    decomposer.visualize(tree)
    
    print("\n\n=== Constraint Solver ===")
    solver = ConstraintSolver()
    solver.solve(
        "Schedule 5 meetings",
        ["All meetings must be between 9 AM - 5 PM", "Each meeting is 1 hour", "No overlaps", "Lunch break 12-1 PM"]
    )
    
    print("\n\n=== Analogy Agent ===")
    analogy = AnalogyAgent()
    analogy.solve_by_analogy("How to scale a startup?", "biology and organism growth")
    
    print("\n\n=== Causal Reasoning Agent ===")
    causal = CausalReasoningAgent()
    causal.analyze_causality("Website traffic dropped 40% last week")

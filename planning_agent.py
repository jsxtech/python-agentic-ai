import anthropic
import json

client = anthropic.Anthropic()

class PlanningAgent:
    def __init__(self):
        self.plans = []
    
    def create_plan(self, goal):
        """Break down a goal into actionable steps"""
        prompt = f"""Create a detailed step-by-step plan to achieve this goal: {goal}

Format your response as a JSON array of steps, where each step has:
- step_number
- description
- dependencies (array of step numbers that must complete first)
- estimated_time

Example format:
[
  {{"step_number": 1, "description": "...", "dependencies": [], "estimated_time": "5 min"}},
  {{"step_number": 2, "description": "...", "dependencies": [1], "estimated_time": "10 min"}}
]"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        plan_text = response.content[0].text
        
        # Extract JSON from response
        try:
            start = plan_text.find('[')
            end = plan_text.rfind(']') + 1
            plan = json.loads(plan_text[start:end])
            self.plans.append({"goal": goal, "steps": plan})
            return plan
        except:
            return [{"step_number": 1, "description": plan_text, "dependencies": [], "estimated_time": "unknown"}]
    
    def execute_step(self, plan, step_number):
        """Execute a specific step from the plan"""
        step = next((s for s in plan if s["step_number"] == step_number), None)
        if not step:
            return "Step not found"
        
        prompt = f"Execute this task: {step['description']}"
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def auto_execute(self, goal):
        """Create and execute a plan automatically"""
        print(f"🎯 Goal: {goal}\n")
        
        plan = self.create_plan(goal)
        print("📋 Plan created:\n")
        for step in plan:
            print(f"  {step['step_number']}. {step['description']} ({step['estimated_time']})")
        
        print("\n⚙️  Executing plan...\n")
        
        completed = []
        for step in plan:
            # Check dependencies
            if all(dep in completed for dep in step.get("dependencies", [])):
                print(f"▶️  Step {step['step_number']}: {step['description']}")
                result = self.execute_step(plan, step['step_number'])
                print(f"✅ Result: {result}\n")
                completed.append(step['step_number'])
        
        return "Plan execution complete"

if __name__ == "__main__":
    planner = PlanningAgent()
    planner.auto_execute("Build a REST API for a todo app")

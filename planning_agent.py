from config import api_call_with_retry, get_client, extract_json_array

client = get_client()


def _step_number(step):
    """Extract step number from a step dict, handling variant key names. Always returns a string for consistent comparison."""
    val = step.get("step_number", step.get("step", step.get("number", 0)))
    return str(val)


def _step_description(step):
    """Extract step description from a step dict, handling variant key names."""
    return step.get("description", step.get("task", step.get("desc", str(step))))


def _step_time(step):
    """Extract estimated time from a step dict, handling variant key names."""
    return step.get("estimated_time", step.get("time", step.get("duration", "unknown")))


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

        response = api_call_with_retry(
            client,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        plan_text = response.content[0].text

        # Extract JSON from response
        plan = extract_json_array(plan_text)
        if plan is None:
            plan = [{"step_number": 1, "description": plan_text, "dependencies": [], "estimated_time": "unknown"}]

        self.plans.append({"goal": goal, "steps": plan})
        return plan

    def execute_step(self, plan, step_number):
        """Execute a specific step from the plan"""
        step = next((s for s in plan if _step_number(s) == step_number), None)
        if not step:
            return "Step not found"

        prompt = f"Execute this task: {_step_description(step)}"

        response = api_call_with_retry(
            client,
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
            print(f"  {_step_number(step)}. {_step_description(step)} ({_step_time(step)})")

        print("\n⚙️  Executing plan...\n")

        completed = []
        remaining = list(plan)

        # Iterate until no more progress can be made
        while remaining:
            progress = False
            for step in remaining[:]:
                deps = step.get("dependencies", step.get("deps", []))
                # Normalize deps to strings for consistent comparison with step numbers
                deps_normalized = [str(d) for d in deps]
                if all(dep in completed for dep in deps_normalized):
                    step_num = _step_number(step)
                    print(f"▶️  Step {step_num}: {_step_description(step)}")
                    result = self.execute_step(plan, step_num)
                    print(f"✅ Result: {result}\n")
                    completed.append(step_num)
                    remaining.remove(step)
                    progress = True

            if not progress:
                skipped = [_step_number(s) for s in remaining]
                print(f"⚠️  Could not execute steps {skipped} (unmet dependencies)")
                break

        return "Plan execution complete"


if __name__ == "__main__":
    planner = PlanningAgent()
    planner.auto_execute("Build a REST API for a todo app")

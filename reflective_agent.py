import json
from datetime import datetime
from config import api_call_with_retry, get_client

client = get_client()

class ReflectiveAgent:
    """Agent that reflects on its actions and learns from mistakes"""
    
    def __init__(self):
        self.experience = []
        self.improvements = []
    
    def act(self, task):
        # Initial attempt
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": task}]
        )
        
        initial_result = response.content[0].text
        
        # Self-reflection
        reflection_prompt = f"""Task: {task}
Your response: {initial_result}

Reflect on your response:
1. What did you do well?
2. What could be improved?
3. What would you do differently?

Provide a JSON response with: {{strengths: [], weaknesses: [], improvements: []}}"""
        
        reflection = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": reflection_prompt}]
        )
        
        # Improved attempt based on reflection
        improve_prompt = f"""Task: {task}
Previous attempt: {initial_result}
Reflection: {reflection.content[0].text}

Now provide an improved response:"""
        
        improved = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": improve_prompt}]
        )
        
        self.experience.append({
            "task": task,
            "initial": initial_result,
            "reflection": reflection.content[0].text,
            "improved": improved.content[0].text,
            "timestamp": datetime.now().isoformat()
        })
        
        return improved.content[0].text
    
    def get_experience(self):
        return self.experience

if __name__ == "__main__":
    agent = ReflectiveAgent()
    result = agent.act("Explain quantum computing in simple terms")
    print(f"Final result:\n{result}")

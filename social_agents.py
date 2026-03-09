import anthropic
import json
from datetime import datetime
from typing import List, Dict, Any

client = anthropic.Anthropic()

class NegotiationAgent:
    """Agent that negotiates with other agents"""
    
    def negotiate(self, my_goal, other_goal, rounds=3):
        print(f"🤝 Negotiation")
        print(f"My goal: {my_goal}")
        print(f"Other's goal: {other_goal}\n")
        
        my_position = my_goal
        other_position = other_goal
        
        for i in range(rounds):
            print(f"--- Round {i+1} ---")
            
            # My proposal
            my_prompt = f"""Your goal: {my_goal}
Other party's goal: {other_goal}
Their last position: {other_position}

Make a proposal that moves toward agreement:"""
            
            my_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[{"role": "user", "content": my_prompt}]
            )
            
            my_position = my_response.content[0].text
            print(f"My proposal: {my_position}")
            
            # Other's counter
            other_prompt = f"""Your goal: {other_goal}
Other party's goal: {my_goal}
Their proposal: {my_position}

Counter-propose or accept:"""
            
            other_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[{"role": "user", "content": other_prompt}]
            )
            
            other_position = other_response.content[0].text
            print(f"Their response: {other_position}\n")
            
            if "accept" in other_position.lower():
                print("✅ Agreement reached!")
                return my_position
        
        return "No agreement reached"

class TeachingAgent:
    """Agent that teaches concepts to learners"""
    
    def assess_knowledge(self, learner_response, topic):
        """Assess learner's understanding"""
        prompt = f"""Topic: {topic}
Learner's response: {learner_response}

Assess understanding level (0-10) and identify gaps:
Return JSON: {{"score": 0-10, "gaps": [], "strengths": []}}"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def teach(self, topic, learner_level="beginner"):
        print(f"👨‍🏫 Teaching: {topic} (Level: {learner_level})\n")
        
        # Initial explanation
        explain_prompt = f"""Teach {topic} to a {learner_level}.
Use:
1. Simple explanation
2. Example
3. Practice question"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": explain_prompt}]
        )
        
        lesson = response.content[0].text
        print(f"Lesson:\n{lesson}\n")
        
        # Simulate learner response
        learner_prompt = f"You're a {learner_level} learning {topic}. Answer the practice question from the lesson."
        
        learner_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": learner_prompt}]
        )
        
        print(f"Learner answer: {learner_response.content[0].text}\n")
        
        # Assess and provide feedback
        assessment = self.assess_knowledge(learner_response.content[0].text, topic)
        print(f"Assessment: {assessment}")
        
        return lesson

class CoordinationAgent:
    """Agent that coordinates multiple agents"""
    
    def __init__(self):
        self.agents = {}
        self.tasks = []
    
    def register_agent(self, name, capabilities):
        self.agents[name] = {"capabilities": capabilities, "status": "idle"}
    
    def assign_tasks(self, tasks):
        print(f"📋 Coordinating {len(tasks)} tasks across {len(self.agents)} agents\n")
        
        assignments = []
        
        for task in tasks:
            # Find best agent for task
            assignment_prompt = f"""Task: {task}

Available agents:
{json.dumps(self.agents, indent=2)}

Which agent is best suited? Respond with agent name:"""
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                messages=[{"role": "user", "content": assignment_prompt}]
            )
            
            assigned_agent = response.content[0].text.strip()
            
            # Find matching agent
            for agent_name in self.agents:
                if agent_name.lower() in assigned_agent.lower():
                    assignments.append({"task": task, "agent": agent_name})
                    print(f"✓ {task} → {agent_name}")
                    break
        
        return assignments

class MonitoringAgent:
    """Agent that monitors system health and performance"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    def collect_metrics(self, metric_name, value):
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append({"value": value, "time": datetime.now().isoformat()})
    
    def analyze_health(self):
        print("🔍 System Health Analysis\n")
        
        prompt = f"""System metrics: {json.dumps(self.metrics)}

Analyze system health:
1. Identify anomalies
2. Predict potential issues
3. Recommend actions

Provide structured analysis:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis = response.content[0].text
        print(analysis)
        
        return analysis
    
    def detect_anomaly(self, metric_name):
        """Detect if metric is anomalous"""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < 3:
            return False
        
        values = [m["value"] for m in self.metrics[metric_name]]
        recent = values[-1]
        avg = sum(values[:-1]) / len(values[:-1])
        
        # Simple threshold-based detection
        if abs(recent - avg) > avg * 0.5:
            self.alerts.append(f"Anomaly detected in {metric_name}: {recent} vs avg {avg:.2f}")
            return True
        
        return False

if __name__ == "__main__":
    print("=== Negotiation Agent ===")
    negotiator = NegotiationAgent()
    negotiator.negotiate(
        "Get project done by Friday",
        "Need more time for quality assurance",
        rounds=2
    )
    
    print("\n\n=== Teaching Agent ===")
    teacher = TeachingAgent()
    teacher.teach("recursion in programming", "beginner")
    
    print("\n\n=== Coordination Agent ===")
    coordinator = CoordinationAgent()
    coordinator.register_agent("DataAgent", ["data processing", "analysis"])
    coordinator.register_agent("CodeAgent", ["programming", "debugging"])
    coordinator.register_agent("DesignAgent", ["UI/UX", "graphics"])
    
    coordinator.assign_tasks([
        "Analyze user behavior data",
        "Fix login bug",
        "Create landing page mockup"
    ])
    
    print("\n\n=== Monitoring Agent ===")
    monitor = MonitoringAgent()
    monitor.collect_metrics("cpu_usage", 45)
    monitor.collect_metrics("cpu_usage", 50)
    monitor.collect_metrics("cpu_usage", 85)
    monitor.detect_anomaly("cpu_usage")
    print(f"Alerts: {monitor.alerts}")

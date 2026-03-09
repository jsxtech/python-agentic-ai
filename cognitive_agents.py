import anthropic
import json
from datetime import datetime
from typing import List, Dict

client = anthropic.Anthropic()

class WorldModelAgent:
    """Agent that builds and maintains a world model"""
    
    def __init__(self):
        self.world_state = {}
        self.history = []
    
    def observe(self, observation):
        """Update world model based on observation"""
        prompt = f"""Current world state: {json.dumps(self.world_state)}
New observation: {observation}

Update the world state. Return JSON with updated state:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = response.content[0].text
            start = result.find('{')
            end = result.rfind('}') + 1
            self.world_state = json.loads(result[start:end])
        except:
            pass
        
        self.history.append({"time": datetime.now().isoformat(), "observation": observation})
        return self.world_state
    
    def predict(self, action):
        """Predict outcome of an action"""
        prompt = f"""World state: {json.dumps(self.world_state)}
Proposed action: {action}

Predict the outcome and new world state:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def plan_with_model(self, goal):
        """Plan actions using world model"""
        prompt = f"""World state: {json.dumps(self.world_state)}
Goal: {goal}

Create a plan considering the current world state:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text

class GoalOrientedAgent:
    """Agent with explicit goal management"""
    
    def __init__(self):
        self.goals = []
        self.completed = []
    
    def add_goal(self, goal, priority="medium"):
        self.goals.append({
            "goal": goal,
            "priority": priority,
            "status": "pending",
            "created": datetime.now().isoformat()
        })
    
    def prioritize_goals(self):
        """Determine which goal to pursue"""
        if not self.goals:
            return None
        
        prompt = f"""Goals: {json.dumps(self.goals)}

Which goal should be pursued next? Consider priority and dependencies.
Respond with the goal text:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        
        selected = response.content[0].text.strip()
        
        for goal in self.goals:
            if goal["goal"] in selected:
                return goal
        
        return self.goals[0]
    
    def pursue_goal(self, goal):
        """Work towards a goal"""
        print(f"🎯 Pursuing: {goal['goal']}")
        
        prompt = f"Create an action plan to achieve: {goal['goal']}"
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        plan = response.content[0].text
        print(f"Plan: {plan}")
        
        goal["status"] = "completed"
        self.completed.append(goal)
        self.goals.remove(goal)
        
        return plan

class EmotionalAgent:
    """Agent with emotional state modeling"""
    
    def __init__(self):
        self.emotional_state = {
            "valence": 0.5,  # 0 (negative) to 1 (positive)
            "arousal": 0.5,  # 0 (calm) to 1 (excited)
            "dominance": 0.5  # 0 (submissive) to 1 (dominant)
        }
    
    def process_event(self, event):
        """Update emotional state based on event"""
        prompt = f"""Current emotional state: {json.dumps(self.emotional_state)}
Event: {event}

How would this event affect emotional state? Return JSON with updated valence, arousal, dominance (0-1):"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = response.content[0].text
            start = result.find('{')
            end = result.rfind('}') + 1
            self.emotional_state = json.loads(result[start:end])
        except:
            pass
        
        return self.emotional_state
    
    def respond_with_emotion(self, situation):
        """Generate emotionally-aware response"""
        emotion_label = self.get_emotion_label()
        
        prompt = f"""Emotional state: {emotion_label}
Situation: {situation}

Respond in a way that reflects your emotional state:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def get_emotion_label(self):
        v, a = self.emotional_state["valence"], self.emotional_state["arousal"]
        if v > 0.6 and a > 0.6:
            return "excited/happy"
        elif v > 0.6 and a < 0.4:
            return "calm/content"
        elif v < 0.4 and a > 0.6:
            return "anxious/angry"
        else:
            return "sad/depressed"

class ExplainableAgent:
    """Agent that explains its reasoning"""
    
    def decide_with_explanation(self, situation, options):
        print(f"📊 Situation: {situation}")
        print(f"Options: {options}\n")
        
        # Make decision
        decision_prompt = f"""Situation: {situation}
Options: {options}

Choose the best option and explain your reasoning in detail:
1. What factors did you consider?
2. Why did you choose this option?
3. What are the trade-offs?

Format:
DECISION: [chosen option]
REASONING: [detailed explanation]"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": decision_prompt}]
        )
        
        result = response.content[0].text
        print(result)
        
        return result
    
    def counterfactual_explanation(self, decision, outcome):
        """Explain what would have happened with different decision"""
        prompt = f"""Decision made: {decision}
Actual outcome: {outcome}

Provide counterfactual explanations:
- What if a different decision was made?
- What factors were most critical?
- What could have changed the outcome?"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text

if __name__ == "__main__":
    print("=== World Model Agent ===")
    world_agent = WorldModelAgent()
    world_agent.observe("Temperature is 72°F")
    world_agent.observe("It's raining outside")
    print(f"World state: {world_agent.world_state}")
    print(f"Prediction: {world_agent.predict('Open window')}\n")
    
    print("\n=== Goal-Oriented Agent ===")
    goal_agent = GoalOrientedAgent()
    goal_agent.add_goal("Learn Python", "high")
    goal_agent.add_goal("Build a project", "medium")
    goal_agent.add_goal("Write documentation", "low")
    next_goal = goal_agent.prioritize_goals()
    goal_agent.pursue_goal(next_goal)
    
    print("\n\n=== Emotional Agent ===")
    emotional = EmotionalAgent()
    emotional.process_event("Received positive feedback on project")
    print(f"Emotional state: {emotional.get_emotion_label()}")
    response = emotional.respond_with_emotion("Someone asks for help")
    print(f"Response: {response}")
    
    print("\n\n=== Explainable Agent ===")
    explainable = ExplainableAgent()
    explainable.decide_with_explanation(
        "Need to choose a database for new project",
        ["PostgreSQL", "MongoDB", "Redis"]
    )

import anthropic
import json
from datetime import datetime

client = anthropic.Anthropic()

class AgentWithMemory:
    """Agent with episodic and semantic memory"""
    
    def __init__(self):
        self.episodic_memory = []  # Specific experiences
        self.semantic_memory = {}   # General knowledge
        self.working_memory = []    # Current context
    
    def remember_episode(self, event, context, outcome):
        """Store a specific experience"""
        self.episodic_memory.append({
            "event": event,
            "context": context,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        })
    
    def learn_fact(self, category, fact):
        """Store general knowledge"""
        if category not in self.semantic_memory:
            self.semantic_memory[category] = []
        self.semantic_memory[category].append(fact)
    
    def recall_similar(self, query):
        """Retrieve relevant memories"""
        relevant = []
        query_lower = query.lower()
        
        for episode in self.episodic_memory:
            if any(word in str(episode).lower() for word in query_lower.split()):
                relevant.append(episode)
        
        return relevant[-5:]  # Last 5 relevant memories
    
    def act_with_memory(self, task):
        """Perform task using memory"""
        # Recall relevant past experiences
        memories = self.recall_similar(task)
        
        memory_context = "\n".join([
            f"Past experience: {m['event']} -> {m['outcome']}"
            for m in memories
        ])
        
        prompt = f"""Task: {task}

Relevant past experiences:
{memory_context}

Semantic knowledge:
{json.dumps(self.semantic_memory, indent=2)}

Use your memory to inform your response:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text
        
        # Store this experience
        self.remember_episode(task, memory_context, result)
        
        return result

class MetaLearningAgent:
    """Agent that learns how to learn"""
    
    def __init__(self):
        self.strategies = []
        self.performance = {}
    
    def try_strategy(self, task, strategy_name, approach):
        """Try a learning strategy and track performance"""
        
        prompt = f"""Task: {task}
Strategy: {strategy_name}
Approach: {approach}

Execute this task using the specified approach:"""
        
        start = datetime.now()
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        duration = (datetime.now() - start).total_seconds()
        result = response.content[0].text
        
        # Evaluate result quality
        eval_prompt = f"""Rate this response on a scale of 1-10:
Task: {task}
Response: {result}

Provide just a number:"""
        
        eval_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": eval_prompt}]
        )
        
        try:
            score = float(eval_response.content[0].text.strip())
        except:
            score = 5.0
        
        # Track performance
        if strategy_name not in self.performance:
            self.performance[strategy_name] = []
        
        self.performance[strategy_name].append({
            "task": task,
            "score": score,
            "duration": duration
        })
        
        return result, score
    
    def learn_best_strategy(self, task_type):
        """Determine which strategy works best for a task type"""
        
        strategies = [
            ("analytical", "Break down into logical steps"),
            ("creative", "Think outside the box and explore novel approaches"),
            ("systematic", "Follow a structured methodology")
        ]
        
        print(f"🧪 Testing strategies for: {task_type}\n")
        
        for name, approach in strategies:
            result, score = self.try_strategy(task_type, name, approach)
            print(f"{name.capitalize()}: Score {score}/10")
        
        # Find best strategy
        best = max(self.performance.items(), 
                   key=lambda x: sum(p["score"] for p in x[1]) / len(x[1]))
        
        print(f"\n🏆 Best strategy: {best[0]}")
        return best[0]

if __name__ == "__main__":
    print("=== Agent with Memory ===")
    memory_agent = AgentWithMemory()
    
    # Learn some facts
    memory_agent.learn_fact("programming", "Python uses indentation for blocks")
    memory_agent.learn_fact("programming", "Functions are first-class objects")
    
    # Have experiences
    result1 = memory_agent.act_with_memory("Write a Python function")
    print(result1)
    
    print("\n\n=== Meta-Learning Agent ===")
    meta_agent = MetaLearningAgent()
    meta_agent.learn_best_strategy("Design a database schema for an e-commerce site")

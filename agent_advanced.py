import anthropic
import json
from typing import List, Dict
import asyncio

client = anthropic.Anthropic()

class AgentWorkflow:
    """Visual workflow builder for agents"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def add_node(self, node_id: str, agent_type: str, config: Dict):
        self.nodes.append({"id": node_id, "type": agent_type, "config": config})
    
    def add_edge(self, from_node: str, to_node: str, condition: str = None):
        self.edges.append({"from": from_node, "to": to_node, "condition": condition})
    
    def execute(self, input_data: str) -> Dict:
        """Execute workflow"""
        current = self.nodes[0]
        result = input_data
        path = []
        
        while current:
            path.append(current["id"])
            result = self._execute_node(current, result)
            
            # Find next node
            next_edge = next((e for e in self.edges if e["from"] == current["id"]), None)
            if not next_edge:
                break
            
            current = next((n for n in self.nodes if n["id"] == next_edge["to"]), None)
        
        return {"result": result, "path": path}
    
    def _execute_node(self, node: Dict, input_data: str) -> str:
        prompt = f"{node['config'].get('instruction', 'Process')}: {input_data}"
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text

class AgentPlugin:
    """Plugin system for extending agent capabilities"""
    
    def __init__(self):
        self.plugins = {}
    
    def register(self, name: str, func):
        self.plugins[name] = func
    
    def execute(self, name: str, *args, **kwargs):
        if name in self.plugins:
            return self.plugins[name](*args, **kwargs)
        return None
    
    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())

# Built-in plugins
def sentiment_analysis(text: str) -> Dict:
    """Analyze sentiment of text"""
    prompt = f"Analyze sentiment (positive/negative/neutral) and score 0-10:\n{text}\nReturn JSON."
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        text = response.content[0].text
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        return {"sentiment": "neutral", "score": 5}

def entity_extraction(text: str) -> List[Dict]:
    """Extract named entities"""
    prompt = f"Extract entities (person, org, location) from:\n{text}\nReturn JSON array."
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        text = response.content[0].text
        start = text.find('[')
        end = text.rfind(']') + 1
        return json.loads(text[start:end])
    except:
        return []

def intent_classification(text: str) -> Dict:
    """Classify user intent"""
    prompt = f"""Classify intent:
Text: {text}
Categories: question, command, statement, request
Return JSON: {{"intent": "...", "confidence": 0-1}}"""
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        text = response.content[0].text
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        return {"intent": "statement", "confidence": 0.5}

class AgentCache:
    """Cache agent responses for faster retrieval"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str):
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value):
        if len(self.cache) >= self.max_size:
            # Remove oldest
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value
    
    def stats(self) -> Dict:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self.cache)
        }

class AgentRateLimiter:
    """Rate limiting for API calls"""
    
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = []
    
    def allow_request(self) -> bool:
        import time
        now = time.time()
        
        # Remove old requests
        self.requests = [r for r in self.requests if now - r < self.window]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
    
    def time_until_available(self) -> float:
        if not self.requests:
            return 0
        import time
        oldest = min(self.requests)
        return max(0, self.window - (time.time() - oldest))

if __name__ == "__main__":
    # Test workflow
    print("=== Workflow ===")
    workflow = AgentWorkflow()
    workflow.add_node("analyze", "analyzer", {"instruction": "Analyze this"})
    workflow.add_node("summarize", "summarizer", {"instruction": "Summarize"})
    workflow.add_edge("analyze", "summarize")
    result = workflow.execute("AI is transforming industries")
    print(f"Result: {result['result'][:100]}...")
    print(f"Path: {result['path']}")
    
    # Test plugins
    print("\n=== Plugins ===")
    plugins = AgentPlugin()
    plugins.register("sentiment", sentiment_analysis)
    plugins.register("entities", entity_extraction)
    plugins.register("intent", intent_classification)
    
    sentiment = plugins.execute("sentiment", "I love this product!")
    print(f"Sentiment: {sentiment}")
    
    intent = plugins.execute("intent", "What is the weather today?")
    print(f"Intent: {intent}")
    
    # Test cache
    print("\n=== Cache ===")
    cache = AgentCache(max_size=5)
    cache.set("q1", "answer1")
    cache.set("q2", "answer2")
    print(f"Get q1: {cache.get('q1')}")
    print(f"Get q3: {cache.get('q3')}")
    print(f"Stats: {cache.stats()}")
    
    # Test rate limiter
    print("\n=== Rate Limiter ===")
    limiter = AgentRateLimiter(max_requests=3, window=10)
    for i in range(5):
        allowed = limiter.allow_request()
        print(f"Request {i+1}: {'✓' if allowed else '✗'}")
    print(f"Wait time: {limiter.time_until_available():.1f}s")

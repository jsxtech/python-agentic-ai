"""Agent Orchestrator — Auto-routing, validation, memory management, analytics, and chaining."""

from datetime import datetime
from typing import Dict, List, Optional

from config import api_call_with_retry, extract_json_object, first_text, get_client

client = get_client()


class AgentRouter:
    """Routes queries to the most appropriate agent based on content analysis."""

    def __init__(self):
        self.agents = {}
        self.routing_history = []

    def register_agent(self, name: str, description: str, handler):
        """Register an agent with its capability description."""
        self.agents[name] = {
            "description": description,
            "handler": handler
        }

    def route(self, query: str) -> Dict:
        """Analyze query and route to the best agent."""
        if not self.agents:
            return {"error": "No agents registered"}

        agent_descriptions = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.agents.items()
        ])

        prompt = f"""Given these available agents:
{agent_descriptions}

Query: {query}

Which agent is best suited for this query? Return JSON:
{{"agent": "agent_name", "confidence": 0.0-1.0, "reasoning": "..."}}"""

        response = api_call_with_retry(
            client,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        result = extract_json_object(first_text(response))
        if result is None:
            # Default to first agent
            agent_name = next(iter(self.agents))
            result = {"agent": agent_name, "confidence": 0.5, "reasoning": "fallback"}

        agent_name = result.get("agent", next(iter(self.agents)))
        if agent_name not in self.agents:
            agent_name = next(iter(self.agents))

        # Execute the selected agent
        handler = self.agents[agent_name]["handler"]
        agent_response = handler(query)

        self.routing_history.append({
            "query": query,
            "routed_to": agent_name,
            "confidence": result.get("confidence", 0),
            "timestamp": datetime.now().isoformat()
        })

        return {
            "agent": agent_name,
            "response": agent_response,
            "confidence": result.get("confidence", 0),
            "reasoning": result.get("reasoning", "")
        }


class ResponseValidator:
    """Validates agent responses against specified criteria."""

    def validate(self, response: str, criteria: List[str]) -> Dict:
        """Check if a response meets the given criteria."""
        criteria_text = "\n".join([f"- {c}" for c in criteria])

        prompt = f"""Response to validate:
{response}

Criteria:
{criteria_text}

Evaluate whether the response meets each criterion.
Return JSON: {{"passed": true/false, "scores": {{"criterion": true/false}}, "feedback": "..."}}"""

        result = api_call_with_retry(
            client,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        parsed = extract_json_object(first_text(result))
        if parsed is None:
            return {"passed": True, "scores": {}, "feedback": "Could not parse validation"}

        return parsed


class MemoryManager:
    """Semantic memory with keyword indexing for efficient retrieval.

    Growth is bounded by ``max_entries``: once the cap is reached, the oldest
    entry is evicted (FIFO) and its keyword-index references are pruned so the
    index does not grow without limit in long-running processes.
    """

    def __init__(self, max_entries: int = 1000):
        self.memories = []
        self.index = {}  # keyword -> list of memory ids
        self.max_entries = max_entries

    def _evict_oldest(self):
        """Remove the oldest memory and prune it from the keyword index."""
        oldest = self.memories.pop(0)
        oldest_id = oldest["id"]
        for kw in set(oldest["content"].lower().split()):
            ids = self.index.get(kw)
            if not ids:
                continue
            ids[:] = [i for i in ids if i != oldest_id]
            if not ids:
                del self.index[kw]

    def store(self, content: str, metadata: Optional[Dict] = None):
        """Store content with automatic keyword indexing."""
        entry = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "id": len(self.memories)
        }
        self.memories.append(entry)

        # Index by keywords
        keywords = set(content.lower().split())
        for kw in keywords:
            if len(kw) > 3:  # Skip short words
                if kw not in self.index:
                    self.index[kw] = []
                self.index[kw].append(entry["id"])

        # Enforce the bound after inserting.
        while len(self.memories) > self.max_entries:
            self._evict_oldest()

        return entry["id"]

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search memories by keyword relevance."""
        query_words = set(query.lower().split())
        scores = {}

        for word in query_words:
            if word in self.index:
                for mem_id in self.index[word]:
                    scores[mem_id] = scores.get(mem_id, 0) + 1

        # Sort by relevance score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        # ids may not equal list positions after eviction; look them up safely
        by_id = {m["id"]: m for m in self.memories}
        return [by_id[mem_id] for mem_id, _ in ranked if mem_id in by_id][:limit]

    def get_all(self) -> List[Dict]:
        """Return all stored memories."""
        return self.memories


class Analytics:
    """Performance tracking and reporting for agent operations."""

    def __init__(self):
        self.events = []
        self.metrics = {
            "total_queries": 0,
            "total_latency": 0.0,
            "errors": 0,
            "agent_usage": {}
        }

    def record_event(self, event_type: str, data: Dict):
        """Record an analytics event."""
        self.events.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        self.metrics["total_queries"] += 1
        if "latency" in data:
            self.metrics["total_latency"] += data["latency"]
        if "agent" in data:
            agent = data["agent"]
            self.metrics["agent_usage"][agent] = self.metrics["agent_usage"].get(agent, 0) + 1
        if data.get("error"):
            self.metrics["errors"] += 1

    def get_report(self) -> Dict:
        """Generate analytics report."""
        total = self.metrics["total_queries"]
        avg_latency = (
            self.metrics["total_latency"] / total if total > 0 else 0
        )
        error_rate = self.metrics["errors"] / total if total > 0 else 0

        return {
            "total_queries": total,
            "avg_latency": f"{avg_latency:.2f}s",
            "error_rate": f"{error_rate:.1%}",
            "agent_usage": self.metrics["agent_usage"],
            "recent_events": self.events[-10:]
        }


class AgentChain:
    """Sequential agent execution — output of one feeds into the next."""

    def __init__(self):
        self.steps = []

    def add_step(self, name: str, instruction: str):
        """Add a step to the chain."""
        self.steps.append({"name": name, "instruction": instruction})

    def execute(self, initial_input: str) -> Dict:
        """Run the chain, passing each output as input to the next step."""
        current_input = initial_input
        results = []

        for step in self.steps:
            prompt = f"""{step['instruction']}

Input: {current_input}"""

            response = api_call_with_retry(
                client,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            output = first_text(response)
            results.append({
                "step": step["name"],
                "output": output
            })
            current_input = output

        return {
            "final_output": current_input,
            "steps": results
        }


class AgentOrchestrator:
    """Top-level orchestrator combining routing, validation, memory, analytics, and chaining."""

    def __init__(self):
        self.router = AgentRouter()
        self.validator = ResponseValidator()
        self.memory = MemoryManager()
        self.analytics = Analytics()

    def register_agent(self, name: str, description: str, handler):
        """Register an agent for routing."""
        self.router.register_agent(name, description, handler)

    def query(self, user_query: str, validate_criteria: Optional[List[str]] = None) -> Dict:
        """Process a query through the full orchestration pipeline."""
        import time
        start = time.time()

        # Route to best agent
        result = self.router.route(user_query)
        latency = time.time() - start

        # Validate if criteria provided
        validation = None
        if validate_criteria:
            validation = self.validator.validate(result["response"], validate_criteria)

        # Store in memory
        self.memory.store(
            f"Q: {user_query}\nA: {result['response']}",
            metadata={"agent": result["agent"]}
        )

        # Record analytics
        self.analytics.record_event("query", {
            "agent": result["agent"],
            "latency": latency,
            "confidence": result["confidence"],
            "error": False
        })

        return {
            "response": result["response"],
            "agent": result["agent"],
            "confidence": result["confidence"],
            "validation": validation,
            "latency": f"{latency:.2f}s"
        }

    def search_memory(self, query: str) -> List[Dict]:
        """Search orchestrator memory."""
        return self.memory.search(query)

    def get_analytics(self) -> Dict:
        """Get analytics report."""
        return self.analytics.get_report()


if __name__ == "__main__":
    # Demo the orchestrator
    print("=== Agent Orchestrator Demo ===\n")

    # Create simple agent handlers
    def research_handler(query):
        response = api_call_with_retry(
            client,
            max_tokens=512,
            messages=[{"role": "user", "content": f"Research this topic briefly: {query}"}]
        )
        return first_text(response)

    def code_handler(query):
        response = api_call_with_retry(
            client,
            max_tokens=512,
            messages=[{"role": "user", "content": f"Write code for: {query}"}]
        )
        return first_text(response)

    def analysis_handler(query):
        response = api_call_with_retry(
            client,
            max_tokens=512,
            messages=[{"role": "user", "content": f"Analyze: {query}"}]
        )
        return first_text(response)

    # Set up orchestrator
    orchestrator = AgentOrchestrator()
    orchestrator.register_agent("researcher", "Research and gather information on topics", research_handler)
    orchestrator.register_agent("coder", "Write and debug code", code_handler)
    orchestrator.register_agent("analyst", "Analyze data and provide insights", analysis_handler)

    # Auto-route a query
    print("--- Auto-Routing ---")
    result = orchestrator.query("What are the benefits of microservices architecture?")
    print(f"Routed to: {result['agent']} (confidence: {result['confidence']})")
    print(f"Response: {result['response'][:200]}...\n")

    # Search memory
    print("--- Memory Search ---")
    memories = orchestrator.search_memory("microservices")
    print(f"Found {len(memories)} relevant memories\n")

    # Agent chaining
    print("--- Agent Chaining ---")
    chain = AgentChain()
    chain.add_step("research", "Research this topic and list key points")
    chain.add_step("summarize", "Summarize these points into 3 bullet points")
    chain.add_step("format", "Format this as a professional email snippet")

    chain_result = chain.execute("Benefits of test-driven development")
    print(f"Chain completed in {len(chain_result['steps'])} steps")
    print(f"Final output: {chain_result['final_output'][:200]}...\n")

    # Analytics
    print("--- Analytics ---")
    report = orchestrator.get_analytics()
    print(f"Total queries: {report['total_queries']}")
    print(f"Avg latency: {report['avg_latency']}")
    print(f"Agent usage: {report['agent_usage']}")

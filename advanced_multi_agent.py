import anthropic
import asyncio
import json

client = anthropic.Anthropic()

class HierarchicalAgent:
    """Multi-level agent system with managers and workers"""
    
    def __init__(self):
        self.manager = None
        self.workers = []
    
    def create_hierarchy(self, task):
        # Manager analyzes and delegates
        manager_prompt = f"""You are a manager agent. 
Task: {task}

Break this into 3-5 subtasks that can be delegated to worker agents.
Format as JSON: [{{"id": 1, "subtask": "...", "priority": "high/medium/low"}}]"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": manager_prompt}]
        )
        
        result = response.content[0].text
        
        try:
            start = result.find('[')
            end = result.rfind(']') + 1
            subtasks = json.loads(result[start:end])
        except:
            subtasks = [{"id": 1, "subtask": task, "priority": "high"}]
        
        print("👔 Manager: Task breakdown")
        for st in subtasks:
            print(f"  {st['id']}. [{st['priority']}] {st['subtask']}")
        
        return subtasks
    
    def execute_subtask(self, subtask):
        """Worker executes a subtask"""
        worker_prompt = f"You are a worker agent. Complete this subtask: {subtask['subtask']}"
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": worker_prompt}]
        )
        
        return response.content[0].text
    
    def run(self, task):
        print(f"🎯 Main task: {task}\n")
        
        # Manager creates plan
        subtasks = self.create_hierarchy(task)
        
        print("\n👷 Workers executing...\n")
        
        # Workers execute
        results = []
        for st in subtasks:
            result = self.execute_subtask(st)
            print(f"✅ Subtask {st['id']}: {result[:100]}...")
            results.append(result)
        
        # Manager synthesizes
        synthesis_prompt = f"""Task: {task}
Worker results:
{chr(10).join([f"{i+1}. {r}" for i, r in enumerate(results)])}

Synthesize these results into a final output:"""
        
        final = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        
        print(f"\n👔 Manager synthesis:\n{final.content[0].text}")
        return final.content[0].text

class SwarmAgent:
    """Swarm intelligence with multiple simple agents"""
    
    def __init__(self, num_agents=5):
        self.num_agents = num_agents
    
    def agent_vote(self, agent_id, problem):
        """Each agent proposes a solution"""
        prompt = f"Agent {agent_id}: Propose a solution to: {problem}"
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def consensus(self, problem):
        """Reach consensus through voting"""
        print(f"🐝 Swarm of {self.num_agents} agents solving: {problem}\n")
        
        proposals = []
        for i in range(self.num_agents):
            proposal = self.agent_vote(i+1, problem)
            proposals.append(proposal)
            print(f"Agent {i+1}: {proposal[:80]}...")
        
        # Consensus mechanism
        consensus_prompt = f"""Problem: {problem}

Agent proposals:
{chr(10).join([f"Agent {i+1}: {p}" for i, p in enumerate(proposals)])}

Synthesize the best elements from all proposals into one optimal solution:"""
        
        final = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": consensus_prompt}]
        )
        
        print(f"\n🎯 Swarm consensus:\n{final.content[0].text}")
        return final.content[0].text

if __name__ == "__main__":
    print("=== Hierarchical Agent ===")
    hierarchical = HierarchicalAgent()
    hierarchical.run("Create a marketing campaign for a new product")
    
    print("\n\n=== Swarm Agent ===")
    swarm = SwarmAgent(num_agents=4)
    swarm.consensus("How to improve team productivity?")

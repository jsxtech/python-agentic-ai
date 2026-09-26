from config import api_call_with_retry, extract_json_array, first_text, get_client

client = get_client()

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
        
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": manager_prompt}]
        )
        
        result = first_text(response)
        
        subtasks = extract_json_array(result)
        if subtasks is None:
            subtasks = [{"id": 1, "subtask": task, "priority": "high"}]
        
        print("👔 Manager: Task breakdown")
        for st in subtasks:
            st_id = st.get('id', st.get('task_id', '?'))
            priority = st.get('priority', st.get('importance', 'medium'))
            subtask_desc = st.get('subtask', st.get('task', st.get('description', str(st))))
            print(f"  {st_id}. [{priority}] {subtask_desc}")
        
        return subtasks
    
    def execute_subtask(self, subtask):
        """Worker executes a subtask"""
        subtask_desc = subtask.get('subtask', subtask.get('task', subtask.get('description', str(subtask))))
        worker_prompt = f"You are a worker agent. Complete this subtask: {subtask_desc}"
        
        response = api_call_with_retry(
            client,
            max_tokens=512,
            messages=[{"role": "user", "content": worker_prompt}]
        )
        
        return first_text(response)
    
    def run(self, task):
        print(f"🎯 Main task: {task}\n")
        
        # Manager creates plan
        subtasks = self.create_hierarchy(task)
        
        print("\n👷 Workers executing...\n")
        
        # Workers execute
        results = []
        for st in subtasks:
            st_id = st.get('id', st.get('task_id', '?'))
            result = self.execute_subtask(st)
            print(f"✅ Subtask {st_id}: {result[:100]}...")
            results.append(result)
        
        # Manager synthesizes
        synthesis_prompt = f"""Task: {task}
Worker results:
{chr(10).join([f"{i+1}. {r}" for i, r in enumerate(results)])}

Synthesize these results into a final output:"""
        
        final = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        
        print(f"\n👔 Manager synthesis:\n{first_text(final)}")
        return first_text(final)

class SwarmAgent:
    """Swarm intelligence with multiple simple agents"""
    
    def __init__(self, num_agents=5):
        self.num_agents = num_agents
    
    def agent_vote(self, agent_id, problem):
        """Each agent proposes a solution"""
        prompt = f"Agent {agent_id}: Propose a solution to: {problem}"
        
        response = api_call_with_retry(
            client,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return first_text(response)
    
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
        
        final = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": consensus_prompt}]
        )
        
        print(f"\n🎯 Swarm consensus:\n{first_text(final)}")
        return first_text(final)

if __name__ == "__main__":
    print("=== Hierarchical Agent ===")
    hierarchical = HierarchicalAgent()
    hierarchical.run("Create a marketing campaign for a new product")
    
    print("\n\n=== Swarm Agent ===")
    swarm = SwarmAgent(num_agents=4)
    swarm.consensus("How to improve team productivity?")

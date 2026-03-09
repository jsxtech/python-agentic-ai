import anthropic
import json
from typing import List, Dict

client = anthropic.Anthropic()

class CriticAgent:
    """Agent that critiques and validates outputs"""
    
    def critique(self, task, output):
        prompt = f"""Task: {task}
Output: {output}

Critique this output:
1. Correctness
2. Completeness
3. Quality
4. Improvements needed

Provide JSON: {{"score": 0-10, "issues": [], "suggestions": []}}"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text

class AgentWithCritic:
    """Agent that uses a critic for quality control"""
    
    def __init__(self):
        self.critic = CriticAgent()
        self.max_iterations = 3
    
    def solve_with_feedback(self, task):
        print(f"🎯 Task: {task}\n")
        
        current_output = None
        
        for i in range(self.max_iterations):
            # Generate solution
            if current_output is None:
                prompt = task
            else:
                prompt = f"{task}\n\nPrevious attempt: {current_output}\nCritique: {critique}\n\nImprove based on feedback:"
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            current_output = response.content[0].text
            print(f"Iteration {i+1}:\n{current_output[:200]}...\n")
            
            # Get critique
            critique = self.critic.critique(task, current_output)
            print(f"Critique: {critique[:150]}...\n")
            
            # Check if good enough
            if "score" in critique and any(str(x) in critique for x in range(8, 11)):
                print("✅ Quality threshold met")
                break
        
        return current_output

class DebateAgent:
    """Multiple agents debate to reach best solution"""
    
    def debate(self, topic, num_agents=3, rounds=2):
        print(f"🗣️  Debate: {topic}\n")
        
        positions = []
        
        # Initial positions
        for i in range(num_agents):
            prompt = f"Agent {i+1}: State your position on: {topic}"
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            
            position = response.content[0].text
            positions.append({"agent": i+1, "position": position})
            print(f"Agent {i+1}: {position[:100]}...\n")
        
        # Debate rounds
        for round_num in range(rounds):
            print(f"--- Round {round_num + 1} ---\n")
            
            new_positions = []
            for i, pos in enumerate(positions):
                other_positions = [p for j, p in enumerate(positions) if j != i]
                
                prompt = f"""Topic: {topic}
Your position: {pos['position']}

Other positions:
{chr(10).join([f"Agent {p['agent']}: {p['position']}" for p in other_positions])}

Respond to other positions and refine your argument:"""
                
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                new_position = response.content[0].text
                new_positions.append({"agent": pos['agent'], "position": new_position})
                print(f"Agent {pos['agent']}: {new_position[:100]}...\n")
            
            positions = new_positions
        
        # Synthesis
        synthesis_prompt = f"""Topic: {topic}

Final positions:
{chr(10).join([f"Agent {p['agent']}: {p['position']}" for p in positions])}

Synthesize the best insights from all positions:"""
        
        final = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        
        print(f"🎯 Synthesis:\n{final.content[0].text}")
        return final.content[0].text

class SocraticAgent:
    """Agent that learns through questioning"""
    
    def question(self, topic, depth=3):
        print(f"🤔 Socratic exploration: {topic}\n")
        
        current_understanding = topic
        
        for i in range(depth):
            # Ask probing question
            question_prompt = f"""Current understanding: {current_understanding}

Ask a deep, probing question that challenges assumptions or explores implications:"""
            
            q_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[{"role": "user", "content": question_prompt}]
            )
            
            question = q_response.content[0].text
            print(f"Q{i+1}: {question}")
            
            # Answer the question
            answer_prompt = f"""Question: {question}
Context: {current_understanding}

Provide a thoughtful answer:"""
            
            a_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": answer_prompt}]
            )
            
            answer = a_response.content[0].text
            print(f"A{i+1}: {answer}\n")
            
            current_understanding = f"{current_understanding}\n\nQ: {question}\nA: {answer}"
        
        return current_understanding

if __name__ == "__main__":
    print("=== Agent with Critic ===")
    critic_agent = AgentWithCritic()
    critic_agent.solve_with_feedback("Design a secure authentication system")
    
    print("\n\n=== Debate Agent ===")
    debate = DebateAgent()
    debate.debate("Should AI development be regulated?", num_agents=3, rounds=2)
    
    print("\n\n=== Socratic Agent ===")
    socratic = SocraticAgent()
    socratic.question("What is consciousness?", depth=3)

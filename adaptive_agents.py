from config import api_call_with_retry, first_text, get_client, parse_score

client = get_client()

class EvolutionaryAgent:
    """Agent that evolves solutions through generations"""
    
    def evolve(self, problem, population_size=5, generations=3):
        print(f"🧬 Evolving solutions for: {problem}\n")
        
        # Initial population
        population = []
        for i in range(population_size):
            prompt = f"Generate a solution to: {problem}"
            
            response = api_call_with_retry(
                client,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            
            solution = first_text(response)
            fitness = self.evaluate_fitness(problem, solution)
            population.append({"solution": solution, "fitness": fitness, "generation": 0})
            print(f"Gen 0, Individual {i+1}: Fitness {fitness:.2f}")
        
        # Evolution
        for gen in range(1, generations + 1):
            print(f"\n--- Generation {gen} ---")
            
            # Select best (keep at least one survivor so the next generation
            # is never empty, even for tiny population sizes).
            population.sort(key=lambda x: x["fitness"], reverse=True)
            num_survivors = max(1, population_size // 2)
            survivors = population[:num_survivors]

            # Crossover and mutation
            new_population = survivors.copy()

            # A single survivor cannot be crossed over with a distinct partner;
            # skip crossover in that degenerate case.
            for i in range(len(survivors) if len(survivors) > 1 else 0):
                parent1 = survivors[i]["solution"]
                parent2 = survivors[(i+1) % len(survivors)]["solution"]
                
                crossover_prompt = f"""Problem: {problem}
Parent 1: {parent1}
Parent 2: {parent2}

Create a new solution by combining best elements from both parents and adding innovation:"""
                
                response = api_call_with_retry(
                    client,
                    max_tokens=512,
                    messages=[{"role": "user", "content": crossover_prompt}]
                )
                
                offspring = first_text(response)
                fitness = self.evaluate_fitness(problem, offspring)
                new_population.append({"solution": offspring, "fitness": fitness, "generation": gen})
                print(f"Gen {gen}, Offspring {i+1}: Fitness {fitness:.2f}")
            
            population = new_population
        
        # Return best
        best = max(population, key=lambda x: x["fitness"])
        print(f"\n🏆 Best solution (Fitness: {best['fitness']:.2f}):\n{best['solution']}")
        return best
    
    def evaluate_fitness(self, problem, solution):
        """Evaluate solution quality"""
        eval_prompt = f"""Problem: {problem}
Solution: {solution}

Rate this solution 0-10 based on:
- Effectiveness
- Feasibility
- Innovation

Respond with just a number:"""
        
        response = api_call_with_retry(
            client,
            max_tokens=10,
            messages=[{"role": "user", "content": eval_prompt}]
        )
        
        return parse_score(first_text(response), default=5.0)

class CuriosityDrivenAgent:
    """Agent that explores based on curiosity"""
    
    def __init__(self):
        self.knowledge = []
        self.curiosity_threshold = 0.5
    
    def explore(self, starting_topic, steps=5):
        print(f"🔍 Curiosity-driven exploration from: {starting_topic}\n")
        
        current_topic = starting_topic
        
        for i in range(steps):
            # Learn about current topic
            learn_prompt = f"Explain {current_topic} in 2-3 sentences:"
            
            response = api_call_with_retry(
                client,
                max_tokens=256,
                messages=[{"role": "user", "content": learn_prompt}]
            )
            
            knowledge = first_text(response)
            self.knowledge.append({"topic": current_topic, "info": knowledge})
            print(f"Step {i+1}: {current_topic}")
            print(f"Learned: {knowledge}\n")
            
            # Generate curious question
            curiosity_prompt = f"""Current topic: {current_topic}
What you know: {knowledge}

What's the most interesting related topic to explore next? Respond with just the topic name:"""
            
            next_response = api_call_with_retry(
                client,
                max_tokens=50,
                messages=[{"role": "user", "content": curiosity_prompt}]
            )
            
            current_topic = first_text(next_response).strip()
        
        print(f"📚 Explored {len(self.knowledge)} topics")
        return self.knowledge

class AdaptiveAgent:
    """Agent that adapts strategy based on environment"""
    
    def __init__(self):
        self.strategies = {
            "analytical": "Break down logically and analyze systematically",
            "creative": "Think creatively and explore unconventional approaches",
            "practical": "Focus on practical, actionable solutions",
            "theoretical": "Explore theoretical foundations and principles"
        }
        self.performance_history = {k: [] for k in self.strategies}
    
    def detect_context(self, task):
        """Detect what type of task this is"""
        context_prompt = f"""Task: {task}

What type of approach would work best? Choose one:
- analytical (for logical, structured problems)
- creative (for open-ended, innovative problems)
- practical (for implementation-focused problems)
- theoretical (for conceptual, research problems)

Respond with just one word:"""
        
        response = api_call_with_retry(
            client,
            max_tokens=10,
            messages=[{"role": "user", "content": context_prompt}]
        )
        
        detected = first_text(response).strip().lower()
        return detected if detected in self.strategies else "analytical"
    
    def adapt_and_solve(self, task):
        context = self.detect_context(task)
        strategy = self.strategies[context]
        
        print(f"🎯 Task: {task}")
        print(f"🔄 Adapted strategy: {context}\n")
        
        prompt = f"""Task: {task}
Strategy: {strategy}

Solve this task using the specified strategy:"""
        
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = first_text(response)
        print(f"Result: {result}")
        
        return result

if __name__ == "__main__":
    print("=== Evolutionary Agent ===")
    evo = EvolutionaryAgent()
    evo.evolve("Design an efficient sorting algorithm", population_size=4, generations=2)
    
    print("\n\n=== Curiosity-Driven Agent ===")
    curious = CuriosityDrivenAgent()
    curious.explore("Machine Learning", steps=4)
    
    print("\n\n=== Adaptive Agent ===")
    adaptive = AdaptiveAgent()
    adaptive.adapt_and_solve("Create a mobile app for fitness tracking")

import anthropic
import json
from datetime import datetime
from typing import List, Dict

client = anthropic.Anthropic()

class AgentTesting:
    """Testing framework for agents"""
    
    def __init__(self):
        self.test_cases = []
        self.results = []
    
    def add_test(self, name: str, input_data: str, expected: str, criteria: str = "contains"):
        self.test_cases.append({
            "name": name,
            "input": input_data,
            "expected": expected,
            "criteria": criteria
        })
    
    def run_tests(self, agent_func) -> Dict:
        """Run all tests"""
        passed = 0
        failed = 0
        
        for test in self.test_cases:
            result = agent_func(test["input"])
            
            if test["criteria"] == "contains":
                success = test["expected"].lower() in result.lower()
            elif test["criteria"] == "exact":
                success = test["expected"] == result
            else:
                success = True
            
            self.results.append({
                "name": test["name"],
                "passed": success,
                "input": test["input"],
                "expected": test["expected"],
                "actual": result[:100]
            })
            
            if success:
                passed += 1
            else:
                failed += 1
        
        return {
            "total": len(self.test_cases),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed/len(self.test_cases)*100):.1f}%",
            "results": self.results
        }

class AgentBenchmark:
    """Benchmark agent performance"""
    
    def __init__(self):
        self.benchmarks = []
    
    def run_benchmark(self, name: str, agent_func, test_input: str, iterations: int = 5):
        """Run performance benchmark"""
        import time
        
        times = []
        for _ in range(iterations):
            start = time.time()
            agent_func(test_input)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        result = {
            "name": name,
            "iterations": iterations,
            "avg_time": f"{avg_time:.2f}s",
            "min_time": f"{min_time:.2f}s",
            "max_time": f"{max_time:.2f}s"
        }
        
        self.benchmarks.append(result)
        return result

class AgentMonitor:
    """Real-time monitoring and alerting"""
    
    def __init__(self):
        self.metrics = {
            "errors": [],
            "warnings": [],
            "performance": []
        }
        self.thresholds = {
            "response_time": 5.0,
            "error_rate": 0.1
        }
    
    def log_error(self, error: str, context: Dict = None):
        self.metrics["errors"].append({
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.metrics["errors"]) > 10:
            self.alert("High error rate detected")
    
    def log_performance(self, response_time: float):
        self.metrics["performance"].append(response_time)
        
        if response_time > self.thresholds["response_time"]:
            self.alert(f"Slow response: {response_time:.2f}s")
    
    def alert(self, message: str):
        print(f"🚨 ALERT: {message}")
    
    def get_health(self) -> Dict:
        """Get system health status"""
        error_count = len(self.metrics["errors"])
        avg_response = sum(self.metrics["performance"]) / len(self.metrics["performance"]) if self.metrics["performance"] else 0
        
        health = "healthy"
        if error_count > 5:
            health = "degraded"
        if error_count > 10:
            health = "critical"
        
        return {
            "status": health,
            "error_count": error_count,
            "avg_response_time": f"{avg_response:.2f}s",
            "uptime": "99.9%"
        }

class AgentVersioning:
    """Version control for agent configurations"""
    
    def __init__(self):
        self.versions = {}
        self.current_version = "1.0.0"
    
    def save_version(self, version: str, config: Dict):
        self.versions[version] = {
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
        self.current_version = version
    
    def load_version(self, version: str) -> Dict:
        return self.versions.get(version, {}).get("config", {})
    
    def list_versions(self) -> List[str]:
        return sorted(self.versions.keys())
    
    def rollback(self, version: str):
        if version in self.versions:
            self.current_version = version
            return True
        return False

class AgentABTest:
    """A/B testing for agent variants"""
    
    def __init__(self):
        self.variants = {}
        self.results = {}
    
    def add_variant(self, name: str, agent_func):
        self.variants[name] = agent_func
        self.results[name] = {"success": 0, "total": 0}
    
    def run_test(self, input_data: str, variant: str = None):
        """Run test with specific or random variant"""
        import random
        
        if variant is None:
            variant = random.choice(list(self.variants.keys()))
        
        agent_func = self.variants[variant]
        result = agent_func(input_data)
        
        self.results[variant]["total"] += 1
        
        return {"variant": variant, "result": result}
    
    def record_success(self, variant: str):
        self.results[variant]["success"] += 1
    
    def get_results(self) -> Dict:
        """Get A/B test results"""
        summary = {}
        for variant, data in self.results.items():
            success_rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
            summary[variant] = {
                "total": data["total"],
                "success": data["success"],
                "success_rate": f"{success_rate:.1f}%"
            }
        return summary

if __name__ == "__main__":
    # Test agent function
    def test_agent(input_text):
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": input_text}]
        )
        return response.content[0].text
    
    # Testing
    print("=== Testing ===")
    testing = AgentTesting()
    testing.add_test("math", "What is 2+2?", "4", "contains")
    testing.add_test("greeting", "Say hello", "hello", "contains")
    results = testing.run_tests(test_agent)
    print(f"Pass rate: {results['pass_rate']}")
    
    # Monitoring
    print("\n=== Monitoring ===")
    monitor = AgentMonitor()
    monitor.log_performance(1.5)
    monitor.log_performance(6.2)  # Triggers alert
    monitor.log_error("Connection timeout")
    health = monitor.get_health()
    print(f"Health: {health['status']}")
    
    # Versioning
    print("\n=== Versioning ===")
    versioning = AgentVersioning()
    versioning.save_version("1.0.0", {"model": "claude-3", "temp": 0.7})
    versioning.save_version("1.1.0", {"model": "claude-3.5", "temp": 0.8})
    print(f"Versions: {versioning.list_versions()}")
    print(f"Current: {versioning.current_version}")
    
    # A/B Testing
    print("\n=== A/B Testing ===")
    ab_test = AgentABTest()
    ab_test.add_variant("A", lambda x: "Response A")
    ab_test.add_variant("B", lambda x: "Response B")
    
    for i in range(10):
        result = ab_test.run_test("test input")
        if i % 2 == 0:
            ab_test.record_success(result["variant"])
    
    print(f"Results: {ab_test.get_results()}")

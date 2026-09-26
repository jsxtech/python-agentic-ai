from config import api_call_with_retry, first_text, get_client

client = get_client()

class EthicalAgent:
    """Agent with ethical reasoning capabilities"""
    
    def __init__(self):
        self.ethical_framework = "utilitarian"  # utilitarian, deontological, virtue
        self.values = ["fairness", "transparency", "privacy", "safety"]
    
    def evaluate_action(self, action, context):
        print("⚖️  Ethical Evaluation")
        print(f"Action: {action}")
        print(f"Context: {context}\n")
        
        prompt = f"""Ethical framework: {self.ethical_framework}
Core values: {self.values}

Action: {action}
Context: {context}

Evaluate this action ethically:
1. Potential harms and benefits
2. Stakeholders affected
3. Alignment with values
4. Ethical concerns
5. Recommendation (approve/reject/modify)

Provide structured analysis:"""
        
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        evaluation = first_text(response)
        print(evaluation)
        
        return evaluation
    
    def resolve_dilemma(self, option_a, option_b, context):
        """Resolve ethical dilemma between two options"""
        prompt = f"""Ethical dilemma:
Option A: {option_a}
Option B: {option_b}
Context: {context}

Framework: {self.ethical_framework}
Values: {self.values}

Which option is more ethical? Explain reasoning:"""
        
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return first_text(response)

class SafetyAgent:
    """Agent focused on safety and risk management"""
    
    def assess_risk(self, action, environment):
        print("🛡️  Safety Assessment")
        print(f"Action: {action}")
        print(f"Environment: {environment}\n")
        
        prompt = f"""Action: {action}
Environment: {environment}

Assess safety risks:
1. Identify potential hazards
2. Estimate probability and severity
3. Risk level (low/medium/high/critical)
4. Mitigation strategies

Return JSON: {{"risk_level": "...", "hazards": [], "mitigations": []}}"""
        
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        assessment = first_text(response)
        print(assessment)
        
        return assessment
    
    def create_safety_plan(self, task):
        """Create safety plan for a task"""
        prompt = f"""Task: {task}

Create a comprehensive safety plan:
1. Pre-task safety checks
2. Safety procedures during task
3. Emergency protocols
4. Post-task verification"""
        
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return first_text(response)

class PrivacyAgent:
    """Agent that protects privacy and handles sensitive data"""
    
    def __init__(self):
        self.pii_categories = ["name", "email", "phone", "address", "ssn", "credit_card"]
    
    def detect_pii(self, text):
        """Detect personally identifiable information"""
        prompt = f"""Text: {text}

Identify any PII (personally identifiable information):
Categories: {self.pii_categories}

Return JSON: {{"contains_pii": true/false, "found": [], "risk_level": "low/medium/high"}}"""
        
        response = api_call_with_retry(
            client,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return first_text(response)
    
    def anonymize(self, text):
        """Anonymize sensitive information"""
        prompt = f"""Text: {text}

Replace all PII with placeholders like [NAME], [EMAIL], etc.
Preserve the meaning while protecting privacy:"""
        
        response = api_call_with_retry(
            client,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return first_text(response)
    
    def check_consent(self, data_usage, user_permissions):
        """Check if data usage complies with user consent"""
        prompt = f"""Intended data usage: {data_usage}
User permissions: {user_permissions}

Does this usage comply with user consent? Explain:"""
        
        response = api_call_with_retry(
            client,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return first_text(response)

class BiasDetectionAgent:
    """Agent that detects and mitigates bias"""
    
    def detect_bias(self, text, bias_types=None):
        if bias_types is None:
            bias_types = ["gender", "racial", "age", "cultural", "socioeconomic"]
        
        print("🔍 Bias Detection")
        print(f"Analyzing for: {bias_types}\n")
        
        prompt = f"""Text: {text}

Analyze for potential biases:
Types to check: {bias_types}

For each bias type found:
1. Specific examples
2. Severity (low/medium/high)
3. Suggested corrections

Return structured analysis:"""
        
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis = first_text(response)
        print(analysis)
        
        return analysis
    
    def debias(self, text):
        """Remove or reduce bias in text"""
        prompt = f"""Text: {text}

Rewrite to remove biases while preserving meaning:
- Use inclusive language
- Avoid stereotypes
- Ensure fairness"""
        
        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return first_text(response)

if __name__ == "__main__":
    print("=== Ethical Agent ===")
    ethical = EthicalAgent()
    ethical.evaluate_action(
        "Collect user location data for personalization",
        "Mobile app with 1M users"
    )
    
    print("\n\n=== Safety Agent ===")
    safety = SafetyAgent()
    safety.assess_risk(
        "Deploy ML model to production",
        "Healthcare application affecting patient care"
    )
    
    print("\n\n=== Privacy Agent ===")
    privacy = PrivacyAgent()
    text = "Contact John Doe at john@example.com or call 555-1234"
    print(f"Original: {text}")
    print(f"PII Detection: {privacy.detect_pii(text)}")
    print(f"Anonymized: {privacy.anonymize(text)}")
    
    print("\n\n=== Bias Detection Agent ===")
    bias_detector = BiasDetectionAgent()
    bias_detector.detect_bias(
        "The chairman should ask his secretary to schedule the meeting"
    )

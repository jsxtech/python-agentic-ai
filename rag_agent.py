import anthropic
import json
from pathlib import Path

client = anthropic.Anthropic()

class RAGAgent:
    def __init__(self, knowledge_dir="knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(exist_ok=True)
        self.knowledge_base = []
        self.load_knowledge()
    
    def load_knowledge(self):
        """Load all text files from knowledge directory"""
        for file in self.knowledge_dir.glob("*.txt"):
            with open(file, 'r') as f:
                self.knowledge_base.append({
                    "source": file.name,
                    "content": f.read()
                })
    
    def search_knowledge(self, query):
        """Simple keyword search in knowledge base"""
        results = []
        query_lower = query.lower()
        
        for doc in self.knowledge_base:
            if any(word in doc["content"].lower() for word in query_lower.split()):
                results.append(doc)
        
        return results[:3]  # Top 3 results
    
    def query(self, question):
        # Retrieve relevant documents
        relevant_docs = self.search_knowledge(question)
        
        # Build context from retrieved documents
        context = "\n\n".join([f"Source: {doc['source']}\n{doc['content']}" for doc in relevant_docs])
        
        # Generate response with context
        prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {question}

Answer:"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def add_document(self, filename, content):
        """Add a new document to knowledge base"""
        filepath = self.knowledge_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
        self.knowledge_base.append({"source": filename, "content": content})
        return f"Added {filename} to knowledge base"

if __name__ == "__main__":
    rag = RAGAgent()
    
    # Add sample documents
    rag.add_document("python.txt", "Python is a high-level programming language known for simplicity and readability.")
    rag.add_document("ai.txt", "Artificial Intelligence involves creating systems that can perform tasks requiring human intelligence.")
    
    # Query the knowledge base
    answer = rag.query("What is Python?")
    print(f"Answer: {answer}")

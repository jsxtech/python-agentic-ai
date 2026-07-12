import json
import os
from pathlib import Path

from config import api_call_with_retry, get_client

client = get_client()

# Common English stopwords to exclude from keyword search
STOPWORDS = frozenset({
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'being', 'but', 'by',
    'can', 'could', 'did', 'do', 'does', 'done', 'for', 'from', 'had', 'has',
    'have', 'having', 'he', 'her', 'here', 'hers', 'him', 'his', 'how', 'i',
    'if', 'in', 'into', 'is', 'it', 'its', 'just', 'me', 'might', 'more',
    'most', 'must', 'my', 'no', 'nor', 'not', 'now', 'of', 'on', 'only',
    'or', 'other', 'our', 'out', 'own', 'same', 'shall', 'she', 'should',
    'so', 'some', 'such', 'than', 'that', 'the', 'their', 'them', 'then',
    'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under',
    'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where',
    'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'would', 'you',
    'your', 'about', 'also', 'any', 'because', 'between', 'both', 'each',
    'few', 'get', 'got', 'itself', 'let', 'like', 'make', 'many', 'much',
    'need', 'never', 'new', 'one', 'over', 'still', 'take', 'tell', 'thing',
    'think', 'use', 'want', 'way', 'well', 'yes',
})


class RAGAgent:
    def __init__(self, knowledge_dir="knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(exist_ok=True)
        self.knowledge_base = []
        self.load_knowledge()

    def load_knowledge(self):
        """Load all text files from knowledge directory."""
        self.knowledge_base = []
        for file in self.knowledge_dir.glob("*.txt"):
            try:
                with open(file, 'r') as f:
                    self.knowledge_base.append({
                        "source": file.name,
                        "content": f.read()
                    })
            except (IOError, OSError) as e:
                print(f"Warning: Could not load {file}: {e}")

    def search_knowledge(self, query):
        """Keyword search with stopword filtering and relevance scoring.

        Filters out common English stopwords and scores documents by
        the number of matching keywords.
        """
        # Extract meaningful keywords (filter stopwords, require min length)
        keywords = [
            word for word in query.lower().split()
            if word not in STOPWORDS and len(word) > 2
        ]

        if not keywords:
            # Fall back to all non-trivial words if everything was filtered
            keywords = [word for word in query.lower().split() if len(word) > 1]

        results = []
        for doc in self.knowledge_base:
            content_lower = doc["content"].lower()
            # Score by number of keywords found
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                results.append((score, doc))

        # Sort by relevance (highest score first)
        results.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in results[:3]]

    def query(self, question):
        """Answer a question using retrieved knowledge context."""
        # Retrieve relevant documents
        relevant_docs = self.search_knowledge(question)

        # Build context from retrieved documents
        if relevant_docs:
            context = "\n\n".join([
                f"Source: {doc['source']}\n{doc['content']}"
                for doc in relevant_docs
            ])
        else:
            context = "No relevant documents found in knowledge base."

        # Generate response with context
        prompt = f"""Based on the following context, answer the question.
If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {question}

Answer:"""

        response = api_call_with_retry(
            client,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def add_document(self, filename, content):
        """Add a new document to knowledge base."""
        # Validate filename to prevent path traversal
        if '/' in filename or '\\' in filename or '..' in filename:
            return "Error: Invalid filename (must not contain path separators or '..')"
        filepath = self.knowledge_dir / filename
        # Double-check resolved path is within knowledge_dir
        resolved = str(filepath.resolve())
        knowledge_resolved = str(self.knowledge_dir.resolve())
        if not resolved.startswith(knowledge_resolved + os.sep) and resolved != knowledge_resolved:
            return "Error: Invalid filename"
        with open(filepath, 'w') as f:
            f.write(content)
        self.knowledge_base.append({"source": filename, "content": content})
        return f"Added {filename} to knowledge base"


if __name__ == "__main__":
    rag = RAGAgent()

    # Add sample documents
    rag.add_document(
        "python.txt",
        "Python is a high-level programming language known for simplicity and readability. "
        "It supports multiple paradigms including object-oriented and functional programming."
    )
    rag.add_document(
        "ai.txt",
        "Artificial Intelligence involves creating systems that can perform tasks requiring "
        "human intelligence. Machine learning is a subset of AI focused on learning from data."
    )

    # Query the knowledge base
    answer = rag.query("What is Python?")
    print(f"Answer: {answer}")

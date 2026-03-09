# python-agentic-ai

Comprehensive Python agentic AI framework with 15+ agent architectures and 60+ advanced capabilities.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key
```

### Docker Setup

**Build and run with Docker:**
```bash
# Build image
docker build -t agentic-ai .

# Run basic agent
docker run -it --env ANTHROPIC_API_KEY=your_key agentic-ai

# Run with docker-compose
docker-compose up agent

# Run specific agents
docker-compose --profile multi up      # Multi-agent
docker-compose --profile reasoning up  # Reasoning agent
docker-compose --profile rag up        # RAG agent
docker-compose --profile planning up   # Planning agent
```

**Environment variables:**
Create a `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Quick Start

**Interactive CLI**
```bash
python agent.py
# Type: "What's 25 * 47?"
# Type: "Save my name as John"
# Type: "help" for all capabilities
```

**Run Specific Agents**
```bash
python multi_agent.py          # Multi-agent collaboration
python reasoning_agents.py     # CoT, ToT, ReAct
python rag_agent.py            # RAG with knowledge base
python planning_agent.py       # Autonomous planning
```

## Agent Architectures

### 🎯 Core Agents

**Basic Agent** (`agent.py`) - Interactive agent with tool use
- Tools: weather, calculator, memory, file operations, code execution, web search
- Interactive chat mode with conversation history
- Help command for capabilities

**Multi-Agent System** (`multi_agent.py`) - Specialized agents working together
- Researcher: Information gathering
- Coder: Code generation and debugging
- Analyst: Data analysis and insights
- Planner: Task breakdown and coordination

**RAG Agent** (`rag_agent.py`) - Retrieval-augmented generation
- Knowledge base management
- Document retrieval and indexing
- Context-aware responses

**Planning Agent** (`planning_agent.py`) - Autonomous goal decomposition
- Step-by-step planning
- Dependency tracking
- Auto-execution with progress tracking

### 🧠 Reasoning Agents

**Basic Reasoning** (`reasoning_agents.py`)
- **Chain-of-Thought (CoT)**: Step-by-step reasoning with explicit thinking
- **Tree-of-Thought (ToT)**: Explores multiple reasoning paths
- **ReAct**: Reasoning + Acting interleaved for tool use

**Advanced Reasoning** (`reasoning_advanced.py`)
- **Task Decomposer**: Recursive problem breakdown into subtasks
- **Constraint Solver**: Multi-constraint satisfaction problems
- **Analogy Agent**: Cross-domain reasoning via analogies
- **Causal Reasoning**: Cause-effect analysis and interventions

### 🎓 Learning Agents

**Learning Systems** (`learning_agents.py`)
- **Episodic Memory**: Stores specific experiences with context
- **Semantic Memory**: General knowledge organization
- **Meta-Learning**: Learning how to learn, strategy optimization
- **Performance Tracking**: Monitors and improves over time

**Reflective Agent** (`reflective_agent.py`)
- Self-reflection on outputs
- Iterative improvement loops
- Experience tracking and learning from mistakes

### 🤝 Collaborative Agents

**Collaboration** (`collaborative_agents.py`)
- **Critic Agent**: Quality control with feedback loops
- **Debate Agents**: Multi-round argumentation for best solutions
- **Socratic Agent**: Learning through questioning

**Advanced Multi-Agent** (`advanced_multi_agent.py`)
- **Hierarchical**: Manager delegates to workers, synthesizes results
- **Swarm**: Consensus-based decision making with voting

### 🔄 Adaptive Agents

**Adaptation Systems** (`adaptive_agents.py`)
- **Evolutionary Agent**: Genetic algorithm approach with crossover/mutation
- **Curiosity-Driven**: Autonomous exploration based on novelty
- **Adaptive Agent**: Context-aware strategy selection

### 🧩 Cognitive Agents

**Cognitive Systems** (`cognitive_agents.py`)
- **World Model**: Internal state representation and prediction
- **Goal-Oriented**: Explicit goal management and prioritization
- **Emotional Agent**: Emotional state modeling (valence, arousal, dominance)
- **Explainable Agent**: Reasoning transparency and counterfactuals

### 👥 Social Agents

**Social Interaction** (`social_agents.py`)
- **Negotiation**: Multi-round bargaining and compromise
- **Teaching**: Adaptive instruction with knowledge assessment
- **Coordination**: Task assignment across multiple agents
- **Monitoring**: System health tracking and anomaly detection

### ⚖️ Responsible AI Agents

**Ethics & Safety** (`responsible_agents.py`)
- **Ethical Agent**: Moral reasoning and dilemma resolution
- **Safety Agent**: Risk assessment and mitigation strategies
- **Privacy Agent**: PII detection, anonymization, consent checking
- **Bias Detection**: Identifies and mitigates biases in outputs

### 🔧 Advanced Infrastructure

**Agent Orchestrator** (`agent_orchestrator.py`)
- **Auto-Routing**: Intelligently routes queries to best agent
- **Validation**: Validates responses against criteria
- **Memory Manager**: Semantic memory with keyword indexing
- **Analytics**: Performance tracking and reporting
- **Agent Chaining**: Sequential agent execution

**Advanced Features** (`agent_advanced.py`)
- **Workflow Builder**: Visual workflow with nodes and edges
- **Plugin System**: Extensible with custom plugins
  - Sentiment analysis
  - Entity extraction
  - Intent classification
- **Response Cache**: Caching with hit rate tracking
- **Rate Limiter**: API rate limiting and throttling

**Testing & QA** (`agent_testing.py`)
- **Testing Framework**: Unit tests for agents
- **Benchmarking**: Performance benchmarking
- **Monitoring**: Real-time monitoring and alerting
- **Versioning**: Configuration version control
- **A/B Testing**: Test agent variants

## Complete Feature List (60+)

### 🛠️ Core Capabilities
- ✅ Tool use and function calling
- ✅ Interactive chat mode
- ✅ Conversation history
- ✅ Memory systems (episodic, semantic, working)
- ✅ File operations (read, write, list)
- ✅ Code execution (with safety checks)
- ✅ Web search integration
- ✅ Mathematical calculations

### 🧠 Reasoning & Problem Solving
- ✅ Chain-of-Thought (CoT)
- ✅ Tree-of-Thought (ToT)
- ✅ ReAct (Reasoning + Acting)
- ✅ Task decomposition
- ✅ Constraint satisfaction
- ✅ Analogical reasoning
- ✅ Causal reasoning
- ✅ Counterfactual analysis

### 🎓 Learning & Adaptation
- ✅ Episodic memory
- ✅ Semantic memory
- ✅ Meta-learning
- ✅ Strategy optimization
- ✅ Self-reflection
- ✅ Iterative improvement
- ✅ Experience tracking
- ✅ Evolutionary algorithms
- ✅ Curiosity-driven exploration
- ✅ Adaptive strategy selection

### 🤖 Multi-Agent Systems
- ✅ Hierarchical structures
- ✅ Swarm intelligence
- ✅ Agent coordination
- ✅ Task delegation
- ✅ Consensus mechanisms
- ✅ Debate and argumentation
- ✅ Critic feedback loops
- ✅ Socratic dialogue

### 🧩 Advanced Cognition
- ✅ World modeling
- ✅ State prediction
- ✅ Goal management
- ✅ Goal prioritization
- ✅ Emotional intelligence
- ✅ Emotional state modeling
- ✅ Explainable AI
- ✅ Reasoning transparency

### 👥 Social Intelligence
- ✅ Negotiation
- ✅ Teaching and instruction
- ✅ Knowledge assessment
- ✅ Agent coordination
- ✅ System monitoring
- ✅ Anomaly detection

### ⚖️ Responsible AI
- ✅ Ethical reasoning
- ✅ Moral dilemma resolution
- ✅ Safety assessment
- ✅ Risk management
- ✅ Privacy protection
- ✅ PII detection and anonymization
- ✅ Bias detection
- ✅ Bias mitigation
- ✅ Fairness analysis

### 📚 Knowledge Management
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ Knowledge base management
- ✅ Document retrieval
- ✅ Context-aware responses

### 📋 Planning & Execution
- ✅ Autonomous planning
- ✅ Goal decomposition
- ✅ Dependency tracking
- ✅ Step-by-step execution
- ✅ Plan synthesis

### 🔧 Advanced Infrastructure
- ✅ Agent orchestration and routing
- ✅ Semantic memory management
- ✅ Performance analytics
- ✅ Agent chaining
- ✅ Visual workflow builder
- ✅ Plugin system
- ✅ Response caching
- ✅ Rate limiting
- ✅ Testing framework
- ✅ Benchmarking tools
- ✅ Real-time monitoring
- ✅ Version control
- ✅ A/B testing
- ✅ Sentiment analysis
- ✅ Entity extraction
- ✅ Intent classification

## Architecture Overview

```
python-agentic-ai/
├── agent.py                    # Core interactive agent
├── multi_agent.py              # Multi-agent collaboration
├── rag_agent.py                # RAG with knowledge base
├── planning_agent.py           # Autonomous planning
├── reasoning_agents.py         # CoT, ToT, ReAct
├── reasoning_advanced.py       # Task decomposition, constraints, analogy, causality
├── learning_agents.py          # Memory & meta-learning
├── reflective_agent.py         # Self-improvement
├── collaborative_agents.py     # Critic, Debate, Socratic
├── advanced_multi_agent.py     # Hierarchical, Swarm
├── adaptive_agents.py          # Evolution, Curiosity, Adaptation
├── cognitive_agents.py         # World models, Goals, Emotions, Explainability
├── social_agents.py            # Negotiation, Teaching, Coordination, Monitoring
├── responsible_agents.py       # Ethics, Safety, Privacy, Bias
├── agent_orchestrator.py       # Routing, Memory, Analytics, Chaining
├── agent_advanced.py           # Workflows, Plugins, Cache, Rate Limiting
└── agent_testing.py            # Testing, Benchmarking, Monitoring, A/B Testing
```

## Usage Examples

### Basic Agent
```bash
python agent.py
> What's 25 * 47?
Agent: 1175

> Save my name as Alice
Agent: Saved 'name' to memory

> What's my name?
Agent: Your name is Alice
```

### Multi-Agent System
```bash
python multi_agent.py
# Automatically delegates to Researcher, Coder, Analyst, Planner
```

### Reasoning Agents
```bash
python reasoning_agents.py
# Demonstrates CoT, ToT, and ReAct reasoning patterns
```

### Advanced Reasoning
```bash
python reasoning_advanced.py
# Task decomposition, constraint solving, analogical reasoning
```

### Orchestrator
```bash
python agent_orchestrator.py
# Auto-routing, memory search, analytics, chaining
```

### Testing & Benchmarking
```bash
python agent_testing.py
# Run tests, benchmarks, monitoring, A/B tests
```

## Use Cases

- 🔬 **Research Assistants**: Information gathering and synthesis
- 💻 **Code Generation**: Automated coding and debugging
- 📊 **Data Analysis**: Insights and visualization
- 📝 **Content Creation**: Writing and editing
- 🎓 **Educational Tutoring**: Adaptive learning
- 🤝 **Negotiation**: Multi-party bargaining
- 🔍 **Information Retrieval**: RAG-based search
- 📋 **Task Planning**: Complex project management
- ⚖️ **Ethical Decision Making**: Moral reasoning
- 🛡️ **Safety Assessment**: Risk analysis

## Technologies

- **LLM**: Claude 3.5 Sonnet (Anthropic)
- **Framework**: Custom agentic architecture
- **Language**: Python 3.8+
- **Patterns**: Tool use, multi-agent, RAG, planning, reasoning, learning

## Key Features

✨ **15+ Agent Architectures** - From basic to advanced cognitive systems
🧠 **Advanced Reasoning** - CoT, ToT, ReAct, analogical, causal
🎓 **Learning Systems** - Memory, meta-learning, reflection
🤝 **Multi-Agent** - Hierarchical, swarm, collaborative
⚖️ **Responsible AI** - Ethics, safety, privacy, bias detection
🔧 **Production-Ready** - Testing, monitoring, caching, rate limiting
📦 **Extensible** - Plugin system, workflows, chaining

## Contributing

This is a comprehensive framework demonstrating state-of-the-art agentic AI patterns. Each agent type is self-contained and can be extended or combined for specific use cases.

## License

MIT

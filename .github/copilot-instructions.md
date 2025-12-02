# AI Coding Agent Instructions for LangChain/LangGraph Project

## Project Overview

This is a **Python-based LangChain + LangGraph experimentation workspace** focused on building agentic AI applications using OpenAI's LLMs. The project contains:
- **`sample.ipynb`**: Jupyter notebook for testing OpenAI API integration and basic LangChain usage
- **`langgraph/`**: A structured LangGraph application package with state-based graph architecture

## Architecture & Key Components

### Core Pattern: StateGraph-Based Agents

The project uses **LangGraph's StateGraph** pattern (see `langgraph/src/app.py`):
1. Define a **state schema** (dict-like state structure)
2. Create **nodes** (functions that process state)
3. Connect nodes with **edges** (workflow routing)
4. **Compile** to create an executable graph

Example: The chatbot node receives messages from state, invokes gpt-4o-mini, appends AI response, and returns updated state.

### Dependency Structure

- **langchain**: Core framework for LLM interactions and chains
- **langchain-openai**: OpenAI integration (ChatOpenAI, embeddings)
- **langgraph**: State machine & multi-step agent orchestration
- **openai**: Direct OpenAI API client (used alongside LangChain)
- **python-dotenv**: Environment variable management

## Developer Workflows

### Environment Setup
```bash
# Virtual environment is at .venv/
# Dependencies listed in requirements.txt (root) and setup.py (langgraph/)
# API keys stored in plaintext files: openai_key.txt, langchain_key.txt
```

### Running Code

- **Jupyter Notebook** (`sample.ipynb`):
  - Cells test OpenAI API, LangChain ChatOpenAI, and summarization tasks
  - Loads API keys from `openai_key.txt` and `langchain_key.txt` 
  
- **LangGraph App** (`langgraph/src/app.py`):
  - Defined in `langgraph.json` as entrypoint
  - Execute via: `python -m langgraph.cli run langgraph/langgraph.json`
  - Can be deployed/invoked via LangGraph's deployment mechanisms

## Project-Specific Conventions

1. **API Key Management**: Keys are read from `.txt` files in notebooks/scripts, not from `.env` by default
   - `.env.example` exists but appears unused; production should migrate to environment variables

2. **Model Choice**: Consistently uses **gpt-4o-mini** (fast, cost-efficient) for inference
   - Rationale: Speed and cost for experimentation (see notebook comments)

3. **State Pattern**: Always structure agent data as state dicts with "messages" key
   - Enables LangGraph to handle multi-turn conversations naturally

4. **Graph Compilation**: StateGraph must be `.compile()` before execution (app = graph.compile())

## Integration Points

- **OpenAI API**: Direct client (`OpenAI()`) + LangChain wrapper (`ChatOpenAI`)
- **LangChain Tracing**: `langchain_key.txt` enables LangSmith integration (rarely active in samples)
- **Deployment**: `langgraph.json` defines graphs for LangGraph Cloud/server deployment

## Critical Files

- `langgraph/langgraph.json` — Deployment configuration; changes here affect how graphs are exposed
- `langgraph/src/app.py` — Main graph definition; all agentic logic flows through this
- `sample.ipynb` — Reference for API usage patterns; good template for prototyping

## Common Patterns to Follow

1. **Always use state-first**: Pass data through state, not function arguments
2. **Node returns must update state**: Every node must return the modified state dict
3. **Use ChatOpenAI over raw OpenAI client** in LangGraph contexts (more integrations)
4. **Chain responses properly**: Use `invoke()` for single calls, `stream()` for iterative workflows

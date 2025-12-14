# ArtificialHackMan

Collection of AI-powered projects and experiments.

## Task 9: World Happiness Dashboard Generator

A fully dynamic LangGraph agent that creates interactive dashboards from natural language requirements using GPT-4.

### Features
- **Zero Hardcoded Prompts**: All prompts generated dynamically from brief.md
- **GPT-4 Powered**: Uses GPT-4 for both prompt generation and code creation
- **Interactive Dashboard**: World map with happiness score gradients and linked charts
- **Data-Driven**: Processes real World Happiness Report data

### Quick Start
```bash
cd task_9
pip install -r requirements.txt
echo "OPENAI_API_KEY=your_key_here" > .env
python main.py
```

See `task_9/README.md` for detailed documentation.
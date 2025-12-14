# Audit Finding Extraction Agent

High-accuracy AI agent for extracting structured audit findings from PDF reports using DeepSeek-OCR and LangGraph.

## Features

- **DeepSeek-OCR** via Replicate API for advanced document understanding
- **LangGraph** workflow with validation loops
- **Claude-3.5-Sonnet** for structured extraction (or GPT-4)
- **Human-in-the-loop** for low-confidence results
- **Async processing** for performance
- **Pydantic validation** for data integrity

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
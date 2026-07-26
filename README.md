# SHL Assessment Recommender

A conversational AI agent that takes a hiring manager from a vague need to a grounded shortlist of SHL **Individual Test Solutions**.

## Quickstart

**1. Setup Environment**
Ensure you have Python installed, then install dependencies:
```bash
pip install -r requirements.txt
```

**2. Configure API Keys**
Copy the `.env.example` to `.env` (or just edit your existing `.env` file) and add your chosen LLM provider key:
```env
LLM_PROVIDER=groq  # or gemini, anthropic
GROQ_API_KEY=your_key_here
```

**3. Run the Temporary UI (Recommended for testing)**
To test the agent with a modern chat interface:
```bash
python run_with_ui.py
```
Then open your browser to **http://127.0.0.1:8000/ui**.

**4. Run the API directly (Headless)**
If you just want to run the FastAPI endpoints (`/health` and `/chat`):
```bash
uvicorn app.main:app --reload
```
Then you can send POST requests to `http://127.0.0.1:8000/chat`.

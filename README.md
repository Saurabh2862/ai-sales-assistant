# AI Sales & Document Chatbot

A deterministic AI analytics assistant built using:
- FastAPI
- Streamlit
- Pandas
- LLM (for query understanding only)

## Features
- Natural language sales queries
- Salesman, customer, channel, brand filters
- No hallucinations (backend-only calculations)
- Chat-style UI

## Run locally

### Backend
```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000

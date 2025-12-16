# Horizon Finance - Agentic AI Loan Assistant

## Overview
A consulting-grade Proof of Concept demonstrating Agentic AI orchestration for a BFSI personal loan sales journey. Built for EY Techathon 6.0 - Problem Statement 2 (BFSI).

## Tech Stack
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **AI**: OpenAI GPT-5 (for Master Agent and Sales Agent only)
- **PDF Generation**: ReportLab

## Architecture

### Agent System (Controller-Worker Pattern)
1. **Master Agent (Orchestrator)**: Manages conversation flow, routes to worker agents, maintains session state. Uses LLM for natural conversation only - NEVER makes credit decisions.

2. **Sales Agent (LLM-Assisted)**: Mimics human loan sales executive, gathers requirements, returns strict JSON output.

3. **Verification Agent (Deterministic Logic)**: Mock KYC verification using Python dictionary database. Zero AI involvement.

4. **Underwriting Agent (Pure Python Logic)**: 
   - Credit score < 700 → REJECT
   - Loan ≤ pre-approved limit → APPROVE
   - Loan ≤ 2x pre-approved limit → Requires salary verification (EMI ≤ 50% salary)
   - Loan > 2x pre-approved limit → REJECT

5. **Sanction Agent**: Generates professional PDF sanction letters using ReportLab.

## Project Structure
```
/backend
  main.py                    # FastAPI application
  agents/
    master_agent.py          # Orchestrator
    sales_agent.py           # LLM-assisted sales
    verification_agent.py    # Deterministic KYC
    underwriting_agent.py    # Pure logic credit rules
    sanction_agent.py        # PDF generation
  utils/
    pdf_generator.py         # ReportLab PDF creation
    loan_calculator.py       # EMI and DTI calculations
    state_manager.py         # Session state management

/frontend
  index.html                 # Chat interface
  styles.css                 # Premium BFSI styling
  app.js                     # API communication
```

## Running the Application
```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints
- `POST /api/start` - Initialize new chat session
- `POST /api/chat` - Send message and receive response
- `GET /api/session/{session_id}` - Get session state
- `GET /api/download/{session_id}` - Download sanction letter PDF
- `GET /` - Serve frontend

## Key Design Decisions
1. Underwriting is 100% deterministic Python logic - no AI involvement
2. LLM used only for natural language generation, not decision-making
3. Single session state object tracks entire loan journey
4. Professional PDF generation with NBFC branding

## User Preferences
- Premium, trustworthy UI design
- Indian market focused (Rs., lakhs)
- Clean, responsive interface
- No aggressive sales tactics

## Recent Changes
- Initial project setup: December 2024
- Implemented complete agentic AI orchestration
- Created BFSI-grade premium UI
- Added deterministic underwriting rules
- Integrated PDF sanction letter generation

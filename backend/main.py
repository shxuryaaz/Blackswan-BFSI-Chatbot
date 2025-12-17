import os
import sys
import logging
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional

from backend.utils.state_manager import StateManager
from backend.agents.master_agent import MasterAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Horizon Finance - AI Loan Assistant",
    description="Agentic AI Personal Loan Sales Journey",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state_manager = StateManager()
master_agent = MasterAgent(state_manager)

os.makedirs("generated_letters", exist_ok=True)


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    message: str
    stage: str
    download_available: bool = False
    download_path: Optional[str] = None


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Horizon Finance AI Assistant"}


@app.post("/api/start")
async def start_session():
    logger.info("🚀 Starting new session...")
    result = master_agent.start_session()
    logger.info(f"✅ Session started: {result['session_id']}")
    logger.info(f"Initial message: {result['message'][:100]}...")
    return ChatResponse(
        session_id=result["session_id"],
        message=result["message"],
        stage=result["stage"],
        download_available=False,
        download_path=None
    )


@app.post("/api/chat")
async def chat(request: ChatRequest):
    logger.info("=" * 80)
    logger.info(f"📨 INCOMING REQUEST - {datetime.now().strftime('%H:%M:%S')}")
    logger.info(f"Session ID: {request.session_id or 'NEW SESSION'}")
    logger.info(f"User Message: {request.message}")
    logger.info("-" * 80)
    
    if not request.message.strip():
        logger.warning("❌ Empty message received")
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    session_id = request.session_id
    
    if not session_id:
        logger.info("🆕 Creating new session...")
        start_result = master_agent.start_session()
        session_id = start_result["session_id"]
        logger.info(f"✅ New session created: {session_id}")
    
    logger.info(f"🔄 Processing message with Master Agent...")
    result = master_agent.process_message(session_id, request.message)
    
    logger.info("📤 OUTGOING RESPONSE")
    logger.info(f"Session ID: {result['session_id']}")
    logger.info(f"Stage: {result['stage']}")
    logger.info(f"Response Message: {result['message'][:200]}{'...' if len(result['message']) > 200 else ''}")
    logger.info(f"Download Available: {result.get('download_available', False)}")
    logger.info("=" * 80)
    
    return ChatResponse(
        session_id=result["session_id"],
        message=result["message"],
        stage=result["stage"],
        download_available=result.get("download_available", False),
        download_path=result.get("download_path")
    )


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    state = state_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "state": state.get_state_summary(),
        "stage": state.conversation_stage.value,
        "history": state.conversation_history
    }


@app.get("/api/download/{session_id}")
async def download_sanction_letter(session_id: str):
    state = state_manager.get_session(session_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not state.sanction_letter_path:
        raise HTTPException(status_code=404, detail="Sanction letter not generated")
    
    if not os.path.exists(state.sanction_letter_path):
        raise HTTPException(status_code=404, detail="Sanction letter file not found")
    
    return FileResponse(
        path=state.sanction_letter_path,
        media_type="application/pdf",
        filename=f"sanction_letter_{session_id[:8]}.pdf",
        headers={
            "Content-Disposition": f"attachment; filename=sanction_letter_{session_id[:8]}.pdf"
        }
    )


app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("frontend/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

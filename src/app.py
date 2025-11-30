import os
import shutil
import asyncio
from typing import List
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.agent import create_pipeline
from src.schemas import PipelineState
from utils.logger import get_logger

logger = get_logger()

app = FastAPI(title="Kripaa Exam Generator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure directories exist
(STATIC_DIR / "pyqs").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "syllabus").mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

@app.post("/api/upload")
async def upload_files(
    pyqs: List[UploadFile] = File(...),
    syllabus: UploadFile = File(...)
):
    """
    Uploads PYQs and Syllabus files.
    Clears existing files in static directories first.
    """
    try:
        # Clear existing files
        pyq_dir = STATIC_DIR / "pyqs"
        syllabus_dir = STATIC_DIR / "syllabus"
        
        for f in pyq_dir.glob("*"):
            if f.is_file(): f.unlink()
        for f in syllabus_dir.glob("*"):
            if f.is_file(): f.unlink()
            
        # Save PYQs
        for file in pyqs:
            file_path = pyq_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
        # Save Syllabus
        syllabus_path = syllabus_dir / syllabus.filename
        with open(syllabus_path, "wb") as buffer:
            shutil.copyfileobj(syllabus.file, buffer)
            
        return JSONResponse({"message": "Files uploaded successfully", "pyq_count": len(pyqs)})
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Initialize Pipeline
        pipeline = create_pipeline()
        
        initial_state: PipelineState = {
            "target_year": 2025,
            "pyq_directory": str(STATIC_DIR / "pyqs"),
            "syllabus_directory": str(STATIC_DIR / "syllabus"),
            "snapshot_id": None,
            "paper_markdown": None,
            "current_step": "Initializing",
            "errors": [],
            "completed": False
        }
        
        # Run Pipeline and Stream Updates
        async for event in pipeline.astream(initial_state):
            # event is a dict where key is node name and value is the state update
            # We want to extract the current state
            
            current_state = None
            for node_name, state_update in event.items():
                current_state = state_update
                break # Just take the first one
            
            if current_state:
                # Send update to client
                await websocket.send_json({
                    "step": current_state.get("current_step", "Processing..."),
                    "completed": current_state.get("completed", False),
                    "errors": current_state.get("errors", [])
                })
                
                if current_state.get("completed"):
                    # Send final success message with file links
                    await websocket.send_json({
                        "step": "Completed",
                        "completed": True,
                        "errors": [],
                        "output": {
                            "paper": "/output/generated_paper.pdf",
                            "report": "/output/comprehensive_report.pdf"
                        }
                    })
                    break
                    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})

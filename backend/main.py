import os
import uuid
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import time

# --- Setup and Config ---
load_dotenv()

# --- Database Connection ---
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = None
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    print("❌ DATABASE_URL not found. Please set it in your environment.")
    exit(1)


def check_db_connection():
    for i in range(5):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print(f"✅ Database connection successful on attempt {i+1}.")
            return True
        except Exception as e:
            print(f"Database connection attempt {i+1} failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    return False

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    prompt: str
class CommandRequest(BaseModel):
    command: str
    agent_id: str
class TaskResult(BaseModel):
    result: str

# --- FastAPI App Setup ---
app = FastAPI(title="AI Server Management Backend")

origins = ["http://localhost:3000", "https://ai-server-management-platform.vercel.app"] # Add your Vercel URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    if not check_db_connection():
        print("❌ Could not connect to the database after several retries. The application will start, but database operations will fail.")

# --- In-memory storage ---
active_agents: Dict[str, List[Dict[str, Any]]] = {}
task_results: Dict[str, str] = {}

# --- API Endpoints ---

@app.get("/")
def read_root():
    # This is the updated, simpler version. It no longer talks to the database.
    # This acts as a simple, reliable health check.
    return {"status": "ok", "message": "Backend is running."}

@app.post("/api/chat")
def handle_chat(chat_request: ChatRequest):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction="You are a helpful DevOps assistant.")
        response = model.generate_content(chat_request.prompt)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with AI model: {str(e)}")

@app.post("/api/agent/register")
def register_agent():
    agent_id = str(uuid.uuid4())
    active_agents[agent_id] = []
    print(f"✅ Agent {agent_id} has registered.")
    return {"agent_id": agent_id}

@app.get("/api/agents/active")
def get_active_agents():
    return {"active_agent_ids": list(active_agents.keys())}

@app.get("/api/agent/task/{agent_id}")
def get_agent_task(agent_id: str):
    if agent_id in active_agents and active_agents[agent_id]:
        return active_agents[agent_id].pop(0)
    return {}

@app.post("/api/agent/task/{task_id}/result")
def post_agent_result(task_id: str, result: TaskResult):
    task_results[task_id] = result.result
    return {"status": "ok"}

@app.post("/api/command")
def queue_command(command_request: CommandRequest):
    agent_id = command_request.agent_id
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")
    task_id = str(uuid.uuid4())
    active_agents[agent_id].append({"task_id": task_id, "command": command_request.command})
    return {"task_id": task_id}

@app.get("/api/command/result/{task_id}")
def get_command_result(task_id: str):
    if task_id in task_results:
        return {"status": "complete", "result": task_results.pop(task_id)}
    return {"status": "pending"}

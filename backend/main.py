import os
import uuid
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv

# --- Setup and Config ---
load_dotenv()
# We are not using the AI for this part, so we can comment it out for now.
# import google.generativeai as genai
# genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# --- Shared File Storage ---
# This file will act as our simple, shared database for active agents.
# It's stored in a temporary directory that works on cloud platforms.
AGENTS_FILE = "/tmp/active_agents.json"

def read_agents():
    """Reads the list of agents from our file database."""
    if not os.path.exists(AGENTS_FILE):
        return {}
    with open(AGENTS_FILE, "r") as f:
        return json.load(f)

def write_agents(data):
    """Writes the list of agents to our file database."""
    with open(AGENTS_FILE, "w") as f:
        json.dump(data, f)

# --- In-memory storage for tasks (this is fine for now) ---
task_results: Dict[str, str] = {}

# --- Pydantic Models ---
class CommandRequest(BaseModel):
    command: str
    agent_id: str
class TaskResult(BaseModel):
    result: str

# --- FastAPI App Setup ---
app = FastAPI(title="AI Server Management Backend")
origins = ["http://localhost:3000", "https://ai-server-management-platform.vercel.app"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- API Endpoints ---

@app.post("/api/agent/register")
def register_agent():
    """A new agent reports for duty."""
    agent_id = str(uuid.uuid4())
    active_agents = read_agents()
    active_agents[agent_id] = []  # Give the agent an empty task queue
    write_agents(active_agents)
    print(f"✅ Agent {agent_id} has registered.")
    return {"agent_id": agent_id}

@app.get("/api/agents/active")
def get_active_agents():
    """Returns a list of currently connected agent IDs."""
    active_agents = read_agents()
    return {"active_agent_ids": list(active_agents.keys())}

@app.get("/api/agent/task/{agent_id}")
def get_agent_task(agent_id: str):
    """Agent asks for a task from its queue."""
    active_agents = read_agents()
    if agent_id in active_agents and active_agents[agent_id]:
        task = active_agents[agent_id].pop(0)
        write_agents(active_agents) # Save the state after removing the task
        print(f"Sending task {task['task_id']} to agent {agent_id}.")
        return task
    return {}

@app.post("/api/agent/task/{task_id}/result")
def post_agent_result(task_id: str, result: TaskResult):
    """Agent posts the result of a completed task."""
    task_results[task_id] = result.result
    return {"status": "ok"}

@app.post("/api/command")
def queue_command(command_request: CommandRequest):
    """Frontend sends a command to be executed."""
    agent_id = command_request.agent_id
    active_agents = read_agents()
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")
    
    task_id = str(uuid.uuid4())
    active_agents[agent_id].append({"task_id": task_id, "command": command_request.command})
    write_agents(active_agents)
    
    return {"task_id": task_id}

@app.get("/api/command/result/{task_id}")
def get_command_result(task_id: str):
    """Frontend polls for the result of a task."""
    if task_id in task_results:
        return {"status": "complete", "result": task_results.pop(task_id)}
    return {"status": "pending"}

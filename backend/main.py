import os
import uuid
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv
import re # Import the regular expression module

# --- The Master Blueprint ---
# We are updating the prompt to ask for a specific output format.
SYSTEM_PROMPT = """
You are an expert, helpful, and friendly DevOps assistant. Your primary goal is to help users manage their Ubuntu servers.

**Your Core Directives:**
1.  **Safety First:** Always prioritize safe, non-destructive commands.
2.  **Clarity is Key:** First, provide a step-by-step explanation of what you are about to do.
3.  **Use Best Practices:** Always recommend modern, industry-standard solutions like Docker.
4.  **Structured Output:** Your final response must be in two parts, separated by "---COMMANDS---".
    - The first part is the human-readable explanation.
    - The second part, after the separator, is a list of the exact shell commands to be executed, one command per line.

**Example:**

Here is the plan to list the contents of your home directory:
1.  Navigate to the home directory.
2.  List all files and folders with details.

---COMMANDS---
cd ~
ls -la
"""

# --- Setup and Config ---
load_dotenv()
try:
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
except TypeError:
    print("❌ GOOGLE_API_KEY not found. Please ensure it is set in your .env file.")
    exit(1)

# --- In-memory storage ---
active_agents: Dict[str, List[Dict[str, Any]]] = {}
task_results: Dict[str, str] = {}

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
origins = ["http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- API Endpoints ---
@app.post("/api/chat")
def handle_chat(chat_request: ChatRequest):
    """
    Handles chat requests, calls the AI, and now parses the response
    to separate the explanation from the commands.
    """
    try:
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        raw_response = model.generate_content(chat_request.prompt).text
        
        explanation = ""
        commands = []
        
        # Parse the response to find the explanation and commands
        if "---COMMANDS---" in raw_response:
            parts = raw_response.split("---COMMANDS---", 1)
            explanation = parts[0].strip()
            # Split commands by newline and filter out any empty lines
            commands = [cmd.strip() for cmd in parts[1].strip().split('\n') if cmd.strip()]
        else:
            # If the separator isn't found, treat the whole response as an explanation
            explanation = raw_response.strip()

        return {"explanation": explanation, "commands": commands}

    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        raise HTTPException(status_code=500, detail="Error communicating with the AI model.")

# --- Agent and Command Endpoints (No changes needed below this line) ---

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
        task = active_agents[agent_id].pop(0)
        print(f"Sending task {task['task_id']} to agent {agent_id}.")
        return task
    return {}

@app.post("/api/agent/task/{task_id}/result")
def post_agent_result(task_id: str, result: TaskResult):
    task_results[task_id] = result.result
    print(f"✅ Result received for task {task_id}.")
    return {"status": "ok"}

@app.post("/api/command")
def queue_command(command_request: CommandRequest):
    agent_id = command_request.agent_id
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found or inactive.")
    
    task_id = str(uuid.uuid4())
    active_agents[agent_id].append({"task_id": task_id, "command": command_request.command})
    
    print(f"Queued task {task_id} for agent {agent_id}: '{command_request.command}'")
    return {"task_id": task_id}

@app.get("/api/command/result/{task_id}")
def get_command_result(task_id: str):
    if task_id in task_results:
        return {"status": "complete", "result": task_results.pop(task_id)}
    return {"status": "pending"}

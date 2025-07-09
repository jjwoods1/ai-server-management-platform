import time
import subprocess
import json
import traceback

# --- Configuration ---
LOG_FILE = "/tmp/ai_agent.log"
BASE_URL = "https://ai-server-management-platform-production.up.railway.app/api/agent"
agent_id = None

# --- Custom Logger ---
def log_message(message):
    """Writes a message to our custom log file with a timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message) # Also print to standard output

# --- Agent Functions ---
def register_agent():
    """Announce the agent to the backend using curl."""
    global agent_id
    log_message("Attempting to register agent via curl...")
    
    command = f"curl -sS -X POST -k {BASE_URL}/register"
    
    try:
        log_message(f"Executing command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        
        log_message(f"Curl command finished. STDOUT: {result.stdout}")
        response_data = json.loads(result.stdout)
        
        agent_id = response_data.get("agent_id")
        if agent_id:
            log_message(f"✅ Agent registered successfully with ID: {agent_id}")
            return True
        else:
            log_message("❌ Registration failed: 'agent_id' not found in response.")
            return False

    except subprocess.CalledProcessError as e:
        log_message(f"❌ Curl command failed with a non-zero exit code.")
        log_message(f"❌ STDERR: {e.stderr}")
    except json.JSONDecodeError:
        log_message(f"❌ Failed to decode JSON response from backend.")
        log_message(f"Raw response was: {result.stdout}")
    except Exception:
        # Catch any other exception and write the full traceback to the log
        log_message("❌ An unexpected error occurred during registration.")
        with open(LOG_FILE, "a") as f:
            traceback.print_exc(file=f)
            
    return False

# --- Main Execution Block ---
if __name__ == "__main__":
    log_message("Agent script started.")
    
    # We will only try to register once and then exit so we can inspect the log.
    if register_agent():
        log_message("✅ REGISTRATION SUCCESSFUL.")
    else:
        log_message("❌ REGISTRATION FAILED. See logs for details.")


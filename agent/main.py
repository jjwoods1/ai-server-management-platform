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
    
    # We add a --max-time flag to curl to prevent it from hanging indefinitely
    command = f"curl --max-time 15 -sS -X POST -k {BASE_URL}/register"
    
    try:
        log_message(f"Executing command: {command}")
        # We add a timeout to the subprocess call as a fallback
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, timeout=20)
        
        log_message(f"Curl command finished. STDOUT: {result.stdout}")
        response_data = json.loads(result.stdout)
        
        agent_id = response_data.get("agent_id")
        if agent_id:
            log_message(f"✅ Agent registered successfully with ID: {agent_id}")
            return True
        else:
            log_message(f"❌ Registration failed: 'agent_id' not found in response. Raw response: {result.stdout}")
            return False

    except subprocess.TimeoutExpired:
        log_message("❌ Curl command timed out after 20 seconds.")
    except subprocess.CalledProcessError as e:
        log_message(f"❌ Curl command failed with a non-zero exit code.")
        log_message(f"❌ STDERR: {e.stderr}")
    except json.JSONDecodeError:
        log_message(f"❌ Failed to decode JSON response from backend.")
        log_message(f"Raw response was: {result.stdout}")
    except Exception:
        log_message("❌ An unexpected error occurred during registration.")
        with open(LOG_FILE, "a") as f:
            traceback.print_exc(file=f)
            
    return False

def get_task():
    """Fetches a command from the backend."""
    try:
        command = f"curl --max-time 10 -sS -k {BASE_URL}/task/{agent_id}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, timeout=15)
        response_data = json.loads(result.stdout)
        if response_data:
            return response_data
    except Exception:
        pass # It's normal for this to fail if there are no tasks
    return None

def run_command(command_to_run):
    """Runs a shell command."""
    try:
        result = subprocess.run(command_to_run, shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully with no output."
        else:
            return f"Error executing command:\n{result.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def post_result(task_id, result_text):
    """Posts the result back to the backend."""
    try:
        escaped_result = json.dumps(result_text)
        payload = f'{{"result": {escaped_result}}}'
        command = f"curl --max-time 15 -sS -X POST -k -H 'Content-Type: application/json' -d '{payload}' {BASE_URL}/task/{task_id}/result"
        subprocess.run(command, shell=True, check=True, timeout=20)
    except Exception as e:
        log_message(f"Failed to post result for task {task_id}: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    log_message("Agent script started.")
    
    while not agent_id:
        if register_agent():
            break
        log_message("Registration failed. Retrying in 10 seconds...")
        time.sleep(10)

    log_message("Agent is online and waiting for tasks.")
    while True:
        task = get_task()
        if task:
            task_id = task.get("task_id")
            command = task.get("command")
            log_message(f"Received task {task_id}: Running command '{command}'")
            result = run_command(command)
            post_result(task_id, result)
            log_message(f"Finished task {task_id}. Waiting for next task.")
        
        time.sleep(5)
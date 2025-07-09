import time
import subprocess
import json

# We still define the URL here
BASE_URL = "https://ai-server-management-platform-production.up.railway.app/api/agent"
agent_id = None 

def register_agent():
    """
    Announce the agent to the backend using the system's curl command.
    This is the most reliable method and bypasses Python's SSL/requests stack.
    """
    global agent_id
    
    command = f"curl -sS -X POST -k {BASE_URL}/register"
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        response_data = json.loads(result.stdout)
        
        agent_id = response_data.get("agent_id")
        if agent_id:
            print(f"✅ Agent registered successfully using curl with ID: {agent_id}")
            return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Curl command failed. STDERR: {e.stderr}")
    except json.JSONDecodeError:
        print(f"❌ Failed to decode JSON response from backend.")
    except Exception as e:
        print(f"❌ An unexpected error occurred during registration: {e}")
        
    return False

def get_task():
    """Fetches a command from the backend."""
    try:
        command = f"curl -sS -k {BASE_URL}/task/{agent_id}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
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
        # We need to properly escape the result text for the JSON payload
        escaped_result = json.dumps(result_text)
        payload = f'{{"result": {escaped_result}}}'
        command = f"curl -sS -X POST -k -H 'Content-Type: application/json' -d '{payload}' {BASE_URL}/task/{task_id}/result"
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(f"Failed to post result for task {task_id}: {e}")

# This is the main execution block. All indentation has been corrected.
if __name__ == "__main__":
    print("Agent starting...")
    
    while not agent_id:
        print("Attempting to register agent...")
        if register_agent():
            break
        time.sleep(5)

    print("Agent is online and waiting for tasks.")
    while True:
        task = get_task()
        if task:
            task_id = task.get("task_id")
            command = task.get("command")
            print(f"Received task {task_id}: Running command '{command}'")
            result = run_command(command)
            post_result(task_id, result)
            print(f"Finished task {task_id}. Waiting for next task.")
        
        time.sleep(5)

import requests
import time
import subprocess

# THIS IS THE UPDATED LINE:
# Replace the placeholder with your actual Railway URL
BASE_URL = "https://ai-server-management-platform-production.up.railway.app/api/agent"
agent_id = None 

def register_agent():
    """Announce the agent to the backend and get an ID."""
    global agent_id
    try:
        response = requests.post(f"{BASE_URL}/register", timeout=10)
        if response.status_code == 200:
            agent_id = response.json().get("agent_id")
            print(f"✅ Agent registered successfully with ID: {agent_id}")
            return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not register with backend: {e}")
    return False

def get_task():
    """Fetches a command from the backend."""
    try:
        response = requests.get(f"{BASE_URL}/task/{agent_id}", timeout=10)
        if response.status_code == 200 and response.json():
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None

def run_command(command):
    """Runs a shell command."""
    try:
        # Using shell=True for simplicity, but be cautious in production
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully with no output."
        else:
            return f"Error executing command:\n{result.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def post_result(task_id, result):
    """Posts the result back to the backend."""
    try:
        payload = {"result": result}
        requests.post(f"{BASE_URL}/task/{task_id}/result", json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Failed to post result for task {task_id}: {e}")

if __name__ == "__main__":
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

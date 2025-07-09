import requests
import time
import subprocess

BASE_URL = "https://ai-server-management-platform-production.up.railway.app/api/agent"
agent_id = None 

def register_agent():
    """Announce the agent to the backend and get an ID."""
    global agent_id
    try:
        # THIS IS THE FIX: We are adding verify=False to bypass SSL certificate checks.
        response = requests.post(f"{BASE_URL}/register", timeout=15, verify=False)
        
        if response.status_code == 200:
            agent_id = response.json().get("agent_id")
            print(f"✅ Agent registered successfully with ID: {agent_id}")
            return True
        else:
            print(f"❌ Backend returned an error. Status Code: {response.status_code}")
            print(f"❌ Response Body: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Could not register with backend due to a connection error: {e}")
    return False

def get_task():
    try:
        # We add verify=False here as well for consistency.
        response = requests.get(f"{BASE_URL}/task/{agent_id}", timeout=10, verify=False)
        if response.status_code == 200 and response.json():
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully with no output."
        else:
            return f"Error executing command:\n{result.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def post_result(task_id, result):
    try:
        payload = {"result": result}
        # And here.
        requests.post(f"{BASE_URL}/task/{task_id}/result", json=payload, timeout=10, verify=False)
    except requests.exceptions.RequestException as e:
        print(f"Failed to post result for task {task_id}: {e}")

if __name__ == "__main__":
    print("Agent starting...")
    # Add a small delay to allow network to be ready on server boot
    time.sleep(5) 
    
    while not agent_id:
        print("Attempting to register agent...")
        if register_agent():
            break
        time.sleep(5)

    if agent_id:
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

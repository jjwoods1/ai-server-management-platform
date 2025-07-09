import requests
    import time
    import subprocess

    # THIS IS THE FINAL FIX: We are using the direct IP address to bypass any DNS issues.
    # We also need to tell the server which domain we are trying to reach.
    IP_ADDRESS = "35.233.197.6" # This is the public IP for Railway's US-West proxy
    DOMAIN = "ai-server-management-platform-production.up.railway.app"
    BASE_URL = f"https://{IP_ADDRESS}/api/agent"
    HEADERS = {'Host': DOMAIN}

    agent_id = None 

    def register_agent():
        """Announce the agent to the backend and get an ID."""
        global agent_id
        try:
            # We add the Host header to the request
            response = requests.post(f"{BASE_URL}/register", headers=HEADERS, timeout=15, verify=False)
            
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
            response = requests.get(f"{BASE_URL}/task/{agent_id}", headers=HEADERS, timeout=10, verify=False)
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
            requests.post(f"{BASE_URL}/task/{task_id}/result", json=payload, headers=HEADERS, timeout=10, verify=False)
        except requests.exceptions.RequestException as e:
            print(f"Failed to post result for task {task_id}: {e}")

    if __name__ == "__main__":
        print("Agent starting...")
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
    
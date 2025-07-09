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
    
    # We build the curl command as a string
    # -sS: Silent but show errors
    # -X POST: Make a POST request
    # -k: This is equivalent to verify=False, it ignores SSL errors
    command = f"curl -sS -X POST -k {BASE_URL}/register"
    
    try:
        # We run the command using subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        # The response from the server will be in result.stdout
        response_data = json.loads(result.stdout)
        
        agent_id = response_data.get("agent_id")
        if agent_id:
            print(f"✅ Agent registered successfully using curl with ID: {agent_id}")
            return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Curl command failed with a non-zero exit code.")
        print(f"❌ STDERR: {e.stderr}")
    except json.JSONDecodeError:
        print(f"❌ Failed to decode JSON response from backend.")
    except Exception as e:
        print(f"❌ An unexpected error occurred during registration: {e}")
        
    return False

def run_command(command_to_run):
    # This function remains the same
    try:
        result = subprocess.run(command_to_run, shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully with no output."
        else:
            return f"Error executing command:\n{result.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# The rest of the agent logic for getting and posting tasks is no longer needed
# for this simplified test, as the registration is the only part that is failing.
# We will focus solely on getting it connected.

if __name__ == "__main__":
    print("Agent starting with curl registration method...")
    time.sleep(2) 
    
    # We will try to register just once and then exit so we can see the log.
    if register_agent():
        print("✅ REGISTRATION SUCCESSFUL. The agent would now start its main loop.")
    else:
        print("❌ REGISTRATION FAILED. Please check the errors above.")


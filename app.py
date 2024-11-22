import requests
import subprocess
import threading
import os
from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

# Base URL for raw content of scripts in the GitHub repository (main branch)
GITHUB_REPO = "https://raw.githubusercontent.com/Gedco45/ArcBridge.github.io/main/"

# Directory where scripts will be temporarily stored
TEMP_SCRIPT_DIR = "Scripts"

# Ensure the Scripts directory exists locally (temporary storage for scripts fetched from GitHub)
os.makedirs(TEMP_SCRIPT_DIR, exist_ok=True)

# Function to fetch and save a script from GitHub
def fetch_script_from_github(script_name):
    url = f"{GITHUB_REPO}{script_name}"
    local_script_path = f"{TEMP_SCRIPT_DIR}/{script_name}"

    # Download the script from GitHub if not already present or if we want the latest version
    response = requests.get(url)

    # Check if request is successful
    if response.status_code == 200:
        with open(local_script_path, 'wb') as f:
            f.write(response.content)
        print(f"{script_name} downloaded successfully from GitHub.")
        return local_script_path
    else:
        print(f"Failed to download {script_name} from GitHub.")
        return None

# Function to run the script (generic function for all scripts)
def run_script(script_name):
    script_path = fetch_script_from_github(script_name)
    if script_path:
        # Run the script in a new thread to not block the Flask server
        threading.Thread(target=lambda: subprocess.run(["python", script_path])).start()

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to start the first script (API to GDB)
@app.route('/run_script1')
def run_script1():
    run_script("API_to_GDB.py")
    return redirect(url_for('home'))

# Route to start the second script (GDB to AGOL)
@app.route('/run_script2')
def run_script2():
    run_script("GDB_to_AGOL.py")
    return redirect(url_for('home'))

# Route to start the third script (Raster Tool)
@app.route('/run_script3')
def run_script3():
    run_script("Rastertool.py")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

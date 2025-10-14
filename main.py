from flask import Flask, request, render_template_string, jsonify
import requests
import threading
import time
import os
import queue

app = Flask(__name__)

# Global state variables
stop_flag = False
task_thread = None
message_queue = queue.Queue() # Queue for passing logs from thread to Flask
# IMPORTANT: Update this API URL if the Facebook Graph API version changes
FB_API_URL = "https://graph.facebook.com/v20.0/me/messages"
# ---------------- Stylish HTML (SANJU BABA TERMINAL Theme - Red/White) ---------------- #
html_page = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>⚡ 𝐒𝟑𝐑𝐕𝟑𝐑 𝐁𝐘 𝐒𝟒𝐍𝐉𝐔 𝐁𝟒𝐁𝟒 ⚡</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Share+Tech+Mono&display=swap');
    
    /* Variable for the main glow color */
    :root {
        --cyber-blue: #00ffff;
        --dark-bg: #0d1a2b;
        --light-bg: #1c2e4a;
        --success-green: #39ff14;
        --error-red: #ff3333;
    }

    body {
      font-family: 'Share Tech Mono', monospace; /* Tech Monospace Font */
      background-color: var(--dark-bg); 
      color: var(--cyber-blue); 
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      padding: 10px;
    }
    .main-container {
        width: 100%;
        max-width: 900px;
        display: flex;
        flex-direction: column;
        gap: 30px;
        align-items: center;
    }
    .box {
      background: var(--dark-bg); 
      border-radius: 3px;
      padding: 40px;
      width: 90%;
      box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
      border: 1px solid var(--cyber-electric greens);
      text-align: center;
    }
    h2 {
      margin-bottom: 25px;
      color: #fff; /* White title for contrast */
      text-shadow: 0 0 10px var(--cyber-electric greens), 0 0 20px var(--cyber-electric greens);
      font-family: 'Audiowide', cursive;
      font-size: 2rem;
      text-transform: uppercase;
    }
    input, select, .file-input-label {
      width: 90%;
      padding: 10px;
      margin: 10px 0;
      border-radius: 2px;
      border: 1px solid #444;
      outline: none;
      font-size: 15px;
      background: #000;
      color: var(--cyber-blue);
      transition: border-color 0.3s, box-shadow 0.3s;
    }
    input::placeholder { color: #555; }
    input:focus, select:focus {
      border-color: var(--cyber-bright blue);
      box-shadow: 0 0 8px var(--cyber-bright blue);
    }
    
    /* Custom file input style */
    input[type="file"] {
      display: none;
    }
    .file-input-label {
      display: inline-block;
      cursor: pointer;
      text-align: left;
      border: 1px dashed var(--cyber-blue);
      padding: 10px 14px;
      font-size: 14px;
      margin-top: 10px;
    }

    button {
      padding: 12px 24px;
      margin: 20px 10px 5px;
      border: none;
      border-radius: 3px;
      font-weight: 700;
      cursor: pointer;
      transition: 0.3s all ease-in-out;
      text-transform: uppercase;
      font-family: 'Audiowide', cursive;
      width: 45%;
      box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
    }
    .start {
      background: var(--cyber-blue); 
      color: var(--dark-bg);
    }
    .start:hover {
      background: #fff; 
      box-shadow: 0 0 15px var(--cyber-blue);
      transform: translateY(-2px);
    }
    .stop {
      background: var(--error-red); 
      color: #fff;
    }
    .stop:hover {
      background: #ff0000;
      box-shadow: 0 0 15px var(--error-red);
      transform: translateY(-2px);
    }
    #status {
      margin-top: 20px;
      font-size: 16px;
      color: var(--success-green);
      font-weight: 700;
    }
    .hidden { display: none; }
    label.form-label { font-size: 14px; color: #fff; margin-top: 8px; display: block; text-align: left; width: 90%; margin-left: auto; margin-right: auto;}
    p.file-name-display { font-size:12px; color:var(--cyber-blue); margin-top:5px; text-align:center;}

    /* MSSGE SEND HONE KA PROOF */
    .log-box {
        background: #000;
        border: 1px solid var(--cyber-blue);
        border-radius: 5px;
        height: 300px;
        overflow-y: scroll;
        padding: 10px;
        text-align: left;
        color: #ddd;
        font-size: 13px;
        margin-top: 20px;
        font-family: 'Share Tech Mono', monospace;
        line-height: 1.5;
    }
    .log-box::-webkit-scrollbar { display: none; } /* Hide scrollbar for style */
    .log-entry { margin-bottom: 2px; padding-left: 5px; border-left: 2px solid transparent;}
    .log-entry.success { color: var(--success-green); border-left-color: var(--success-green); }
    .log-entry.fail { color: var(--error-red); border-left-color: var(--error-red); }
  </style>
</head>
<body>
  <div class="main-container">
    <div class="box form-box">
        <h2>:: DATA INJECTION INTERFACE ::</h2>
        <form id="sendForm" enctype="multipart/form-data">
            <label for="mode" class="form-label">Select Authentication Mode:</label>
            <select name="mode" id="mode" onchange="toggleMode()" required>
                <option value="single">🔑 Single Token Injection</option>
                <option value="multi">🔑 Multi-Token File Upload</option>
            </select>

            <div id="singleBox">
                <input type="text" name="single_token" placeholder="Enter Single Access Token [KEY-1]">
            </div>
            <div id="multiBox" class="hidden">
                <label for="multi_file" class="file-input-label">🔑 Select Token List (.txt)</label>
                <input type="file" name="multi_file" id="multi_file" accept=".txt" onchange="updateFileName('multi_file', 'multi-file-name')">
                <p id="multi-file-name" class="file-name-display">No file selected.</p>
            </div>

            <input type="text" name="recipient_id" placeholder="Target Recipient/Group ID (UID)" required><br>
            <input type="text" name="hettar" placeholder="Alias Name (Optional Sender Tag)"><br>
            <input type="number" name="delay" placeholder="Delay (seconds) - Min 1" required min="1" value="5"><br>
            
            <label for="message_file" class="file-input-label">📝 Select Message Payload (.txt)</label>
            <input type="file" name="file" id="message_file" accept=".txt" required onchange="updateFileName('message_file', 'message-file-name')">
            <p id="message-file-name" class="file-name-display">No file selected.</p>

            <button type="button" class="start" onclick="startTask()">⚡ EXECUTE INJECTION ⚡</button>
            <button type="button" class="stop" onclick="stopTask()">🛑 DISTRUCTION PROCESS</button>
        </form>
        <p id="status">Status: 💤 IDLE / Awaiting Command</p>
    </div>
    
    <!-- Proof System / Live Log -->
    <div class="box log-container">
        <h2>:: TRANSMISSION PROOF LOG ::</h2>
        <div id="logArea" class="log-box">
            <!-- Log messages will appear here -->
            <p class="log-entry success">[00:00:00] SYSTEM ONLINE. Awaiting command...</p>
        </div>
    </div>
  </div>

<script>
let logInterval;

function updateFileName(inputId, nameId) {
    const input = document.getElementById(inputId);
    const nameDisplay = document.getElementById(nameId);
    if (input.files.length > 0) {
        nameDisplay.innerText = "File Selected: " + input.files[0].name;
    } else {
        nameDisplay.innerText = "No file selected.";
    }
}

function toggleMode() {
  let mode = document.getElementById("mode").value;
  document.getElementById("singleBox").classList.toggle("hidden", mode !== "single");
  document.getElementById("multiBox").classList.toggle("hidden", mode !== "multi");
}

function fetchLogs() {
    fetch('/logs')
        .then(r => r.json())
        .then(data => {
            const logArea = document.getElementById('logArea');
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => {
                    const p = document.createElement('p');
                    p.classList.add('log-entry');
                    p.classList.add(log.status); // 'success' or 'fail'
                    p.innerText = log.message;
                    logArea.appendChild(p);
                });
                // Auto scroll to the bottom
                logArea.scrollTop = logArea.scrollHeight;
            }
        })
        .catch(error => console.error('Error fetching logs:', error));
}

function startTask() {
  let form = document.getElementById("sendForm");
  let formData = new FormData(form);
  document.getElementById("status").innerText = "Status: ⏱️ Initializing Injection...";
  document.getElementById('logArea').innerHTML = '<p class="log-entry success">[00:00:00] Initializing Process...</p>';

  fetch("/start", { method: "POST", body: formData })
    .then(r => r.json())
    .then(d => {
        if (d.status === "started") {
            document.getElementById("status").innerText = "Status: 🟢 INJECTING DATA (Running)";
            // Start fetching logs every 1 second
            if (!logInterval) {
                logInterval = setInterval(fetchLogs, 1000);
            }
        } else {
            document.getElementById("status").innerText = "Status: ❌ ERROR: " + d.message;
        }
    })
    .catch(error => {
        document.getElementById("status").innerText = "Status: ❌ NETWORK ERROR! Failed to initialize.";
        console.error('Error starting task:', error);
    });
}

function stopTask() {
  document.getElementById("status").innerText = "Status: 🛑 TERMINATING PROCESS...";
  
  // Clear the log fetching interval
  if (logInterval) {
    clearInterval(logInterval);
    logInterval = null;
  }
  
  fetch("/stop", { method: "POST" })
    .then(r => r.json())
    .then(d => {
        document.getElementById("status").innerText = "Status: ✅ PROCESS TERMINATED (Stopped)";
        const logArea = document.getElementById('logArea');
        const p = document.createElement('p');
        p.classList.add('log-entry', 'fail');
        p.innerText = `[${new Date().toLocaleTimeString()}] Process successfully terminated.`;
        logArea.appendChild(p);
        logArea.scrollTop = logArea.scrollHeight;
    })
    .catch(error => {
        document.getElementById("status").innerText = "Status: ❌ ERROR! Could not stop task.";
        console.error('Error stopping task:', error);
    });
}
// Initialize mode display on load
document.addEventListener('DOMContentLoaded', toggleMode);
</script>
</body>
</html>
"""

# ---------------- Background Task (Worker Thread) ---------------- #
def send_loop(tokens, recipient_id, hettar, delay, messages, log_queue):
    global stop_flag
    token_index = 0
    
    # Use requests.Session for efficient connection reuse
    with requests.Session() as s:
        while not stop_flag:
            for msg in messages:
                if stop_flag:
                    break
                
                # Add a timestamp to the message for uniqueness and proof
                current_time = time.strftime("%H:%M:%S", time.localtime())
                # Format the message content
                final_msg = f"[{current_time}] {hettar}: {msg}" if hettar else f"[{current_time}] {msg}"
                
                # Cycle through tokens
                access_token = tokens[token_index % len(tokens)]
                current_token_idx = (token_index % len(tokens)) + 1
                token_index += 1

                payload = {
                    "recipient": {"id": recipient_id},
                    "message": {"text": final_msg}
                }
                params = {"access_token": access_token}
                
                log_entry = {
                    "message": "",
                    "status": "fail"
                }
                
                try:
                    # Attempt the request with a timeout
                    res = s.post(FB_API_URL, params=params, json=payload, timeout=10) 
                    
                    if res.status_code == 200:
                        log_entry["status"] = "success"
                        log_entry["message"] = f"[{current_time}] Token #{current_token_idx} | SUCCESS | Payload: {final_msg[:40]}..."
                    else:
                        error_msg = res.json().get('error', {}).get('message', 'Unknown Error')
                        log_entry["status"] = "fail"
                        log_entry["message"] = f"[{current_time}] Token #{current_token_idx} | FAILED ({res.status_code}) | Error: {error_msg}"
                
                except requests.exceptions.RequestException as e:
                    log_entry["status"] = "fail"
                    log_entry["message"] = f"[{current_time}] Token #{current_token_idx} | FAILED | Network Error: {str(e)[:50]}..."
                except Exception as e:
                    log_entry["status"] = "fail"
                    log_entry["message"] = f"[{current_time}] Token #{current_token_idx} | FAILED | Unexpected Error: {str(e)[:50]}..."
                
                # Push the log entry to the queue for the main thread to pick up
                log_queue.put(log_entry)
                
                time.sleep(delay)

# ---------------- Routes ---------------- #
@app.route("/")
def index():
    return render_template_string(html_page)

# New endpoint for the Proof System (Live Logs)
@app.route("/logs")
def get_logs():
    logs = []
    # Retrieve all items currently in the queue
    while not message_queue.empty():
        logs.append(message_queue.get())
    return jsonify({"logs": logs})

@app.route("/start", methods=["POST"])
def start():
    global stop_flag, task_thread, message_queue
    
    if task_thread and task_thread.is_alive():
        return jsonify({"status": "already running", "message": "The task is already active."})

    stop_flag = False
    
    # Clear the log queue before starting
    while not message_queue.empty():
        try: message_queue.get(False)
        except queue.Empty: break
    
    try:
        mode = request.form["mode"]

        tokens = []
        if mode == "single":
            token = request.form.get("single_token", "").strip()
            if not token:
                 return jsonify({"status": "error", "message": "Please enter a Single Token."}), 400
            tokens = [token]
        elif mode == "multi":
            if "multi_file" not in request.files or not request.files["multi_file"].filename:
                return jsonify({"status": "error", "message": "Please select a Token file."}), 400
            
            file = request.files["multi_file"]
            # Filter out empty lines
            tokens = [t.strip() for t in file.read().decode("utf-8").splitlines() if t.strip()]
            
            if not tokens:
                return jsonify({"status": "error", "message": "No tokens found in the file."}), 400

        recipient_id = request.form.get("recipient_id", "").strip()
        if not recipient_id:
             return jsonify({"status": "error", "message": "Please enter a Target UID."}), 400
             
        hettar = request.form.get("hettar", "").strip()
        
        delay_str = request.form.get("delay", "5")
        try:
            delay = int(delay_str)
            if delay < 1: delay = 1 # Enforce minimum 1 second delay
        except ValueError:
            return jsonify({"status": "error", "message": "Delay must be a valid number."}), 400
        
        if "file" not in request.files or not request.files["file"].filename:
             return jsonify({"status": "error", "message": "Please select a Message file."}), 400

        msg_file = request.files["file"]
        messages = [m.strip() for m in msg_file.read().decode("utf-8").splitlines() if m.strip()]
        if not messages:
            return jsonify({"status": "error", "message": "No messages found in the file."}), 400

        print(f"Operation START: Tokens={len(tokens)}, Delay={delay}s, Messages={len(messages)}")

        # Start the background task, passing the message_queue
        task_thread = threading.Thread(target=send_loop, args=(tokens, recipient_id, hettar, delay, messages, message_queue))
        task_thread.daemon = True 
        task_thread.start()
        
        return jsonify({"status": "started"})
    
    except Exception as e:
        print(f"Error during start process: {e}")
        return jsonify({"status": "error", "message": f"Server Error: {str(e)}"})


@app.route("/stop", methods=["POST"])
def stop():
    global stop_flag, task_thread
    stop_flag = True
    
    if task_thread and task_thread.is_alive():
        # Give a small timeout for the thread to recognize the flag and exit cleanly
        task_thread.join(timeout=2) 
    
    task_thread = None 
    return jsonify({"status": "stopped"})

if __name__ == "__main__":
    # Get port from environment variables or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
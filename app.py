from flask import Flask, render_template, request, Response, jsonify, send_file, send_from_directory
import subprocess
import threading
import time
import queue
import psutil
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------------------
#  QUEUES
# ---------------------------
log_queue = queue.Queue()
stats_queue = queue.Queue()

# ---------------------------
#  BACKGROUND TASKS
# ---------------------------
def system_stats():
    while True:
        stats = {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        stats_queue.put(stats)
        time.sleep(1)

def dummy_logs():
    i = 1
    while True:
        log_queue.put(f"[INFO] Service running... Tick {i} | CPU: {psutil.cpu_percent()}%")
        i += 1
        time.sleep(2)

threading.Thread(target=dummy_logs, daemon=True).start()
threading.Thread(target=system_stats, daemon=True).start()

# ---------------------------
#  SSE GENERATORS
# ---------------------------
def log_generator():
    while True:
        msg = log_queue.get()
        yield f"data: {json.dumps({'type': 'log', 'msg': msg})}\n\n"

def stats_generator():
    while True:
        stats = stats_queue.get()
        yield f"data: {json.dumps({'type': 'stats', **stats})}\n\n"

# ---------------------------
#  ROUTES
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/logs")
def stream_logs():
    return Response(log_generator(), mimetype="text/event-stream")

@app.route("/stats")
def stream_stats():
    return Response(stats_generator(), mimetype="text/event-stream")

@app.route("/run", methods=["POST"])
def run_command():
    data = request.json
    cmd = data.get("cmd", "").strip()
    safe_mode = data.get("safe_mode", True)

    allowed_cmds = ["echo", "ls", "pwd", "whoami", "python", "wget", "curl", "pip", "cat", "head", "tail", "grep", "ps", "df", "free"]
    dangerous_cmds = ["rm", "sudo", "mv", "kill"]

    start_time = time.time()

    if not cmd:
        return jsonify({"output": "Empty command.", "time": 0})

    if safe_mode and any(cmd.startswith(dc) for dc in dangerous_cmds):
        return jsonify({"output": "❌ Dangerous command blocked in safe mode.", "time": 0})

    if not safe_mode:
        allowed_cmds.extend(dangerous_cmds)

    if not any(cmd.split()[0] == ac for ac in allowed_cmds):
        return jsonify({"output": "❌ Command not allowed.", "time": 0})

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        if result.returncode != 0:
            output = f"❌ Error:\n{output}"
    except Exception as e:
        output = f"⚠️ Exception: {str(e)}"

    elapsed = round(time.time() - start_time, 3)
    return jsonify({"output": output or "✅ Success (no output)", "time": elapsed})

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "msg": "No file"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "msg": "No selected file"})
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    return jsonify({"success": True, "msg": f"Uploaded: {file.filename}"})

@app.route("/download/<filename>")
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except:
        return jsonify({"error": "File not found"}), 404

@app.route("/files")
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify({"files": files})

# ---------------------------
#  RUN
# ---------------------------
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)

from flask import Flask, render_template, request, Response, jsonify
import subprocess
import threading
import time
import queue

app = Flask(__name__)

# ---------------------------
#  QUEUE FOR REAL-TIME LOGS
# ---------------------------
log_queue = queue.Queue()

def log_generator():
    """Stream logs to client using SSE."""
    while True:
        msg = log_queue.get()
        yield f"data: {msg}\n\n"
        time.sleep(0.1)


# ---------------------------
#  BACKGROUND LOG EMITTER
# ---------------------------
def dummy_logs():
    """Fake live logs for UI testing."""
    i = 1
    while True:
        log_queue.put(f"[INFO] Service running... Tick {i}")
        i += 1
        time.sleep(2)

threading.Thread(target=dummy_logs, daemon=True).start()


# ---------------------------
#  ROUTES
# ---------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/logs")
def stream_logs():
    return Response(log_generator(), mimetype="text/event-stream")


@app.route("/run", methods=["POST"])
def run_command():
    cmd = request.json.get("cmd", "")

    # SECURITY: Allow only safe commands
    allowed_cmds = ["echo", "ls", "pip", "pwd", "whoami"]

    if not any(cmd.startswith(ac) for ac in allowed_cmds):
        return jsonify({"output": "❌ Command not allowed for security."})

    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        result = e.output

    return jsonify({"output": result})


# ---------------------------
#  RUN APP
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

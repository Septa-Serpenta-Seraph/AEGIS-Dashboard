from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from playwright.sync_api import sync_playwright
import base64
import os
import requests
import docker
from threading import Thread, Event

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hermes_aegis_secret'
# Allow CORS for local dev flexibilty
socketio = SocketIO(app, cors_allowed_origins="*")
docker_client = None

try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"[!] Docker Init Failed: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/vision/scan', methods=['POST'])
def scan_url():
    """
    AEGIS Visual Cortex:
    Visits a URL using Headless Chromium and returns a base64 screenshot.
    """
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    print(f"[*] AEGIS Vision Scanning: {url}")
    try:
        with sync_playwright() as p:
            # Launch the browser (headless)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 720})
            page = context.new_page()
            
            # Navigate
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            
            # Take screenshot
            screenshot_bytes = page.screenshot(full_page=False)
            browser.close()
            
            # Encode
            b64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
            return jsonify({
                'success': True,
                'image': f"data:image/png;base64,{b64_img}",
                'message': f"Successfully scanned {url}"
            })
    except Exception as e:
        print(f"[!] Vision Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/containers', methods=['GET'])
def list_containers():
    """
    List running Docker containers for the Sandbox View.
    """
    if not docker_client:
        return jsonify({'error': 'Docker daemon not connected'}), 503
    
    try:
        containers = docker_client.containers.list()
        data = []
        for c in containers:
            data.append({
                'id': c.short_id,
                'name': c.name,
                'status': c.status,
                'image': c.image.tags[0] if c.image.tags else 'unknown'
            })
        return jsonify({'success': True, 'containers': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@socketio.on('stream_logs')
def handle_stream_logs(data):
    """
    Stream logs from a specific container ID to the client via SocketIO.
    """
    container_id = data.get('id')
    if not docker_client or not container_id:
        return
    
    print(f"[*] Starting log stream for {container_id}")
    # NOTE: In a real implementation, we'd spawn a background thread here
    # to tail logs and emit 'log_update' events. For MVP, we'll implement
    # that in the next iteration to prevent blocking.
    pass

@app.route('/api/supervisor/chat', methods=['POST'])
def supervisor_chat():
    """
    The Supervisor Agent Endpoint.
    Currently mocks a response or routes to OpenRouter if key is present.
    """
    data = request.json
    user_message = data.get('message', '')
    
    # Hardcoded context for the supervisor
    system_prompt = """
    You are the AEGIS Supervisor. You monitor the Docker Sandbox for security threats.
    You have access to container logs and status.
    Your job is to assist the user in debugging and securing the agent.
    """
    
    # Mock logic for MVP (replace with real LLM call later)
    if "status" in user_message.lower():
        response = "All systems nominal. Docker engine is active. No anomalies detected in logs."
    elif "error" in user_message.lower():
        response = "Scanning logs... No critical errors found in the last 5 minutes."
    elif "tryhackme" in user_message.lower():
        response = "Authorized. Loading penetration testing modules for TryHackMe simulation... Target: 10.10.x.x (VPN)."
    else:
        response = f"Supervisor acknowledges: {user_message}. (LLM connection standby)"

    return jsonify({
        'success': True, 
        'response': response,
        'sender': 'Supervisor (Phi-3)'
    })

if __name__ == '__main__':
    # Listen on all interfaces so we can access it from host
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

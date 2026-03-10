from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from playwright.sync_api import sync_playwright
import base64
import os
import requests
import docker
from threading import Thread, Event
import matplotlib
import matplotlib.pyplot as plt
import io
import json
import datetime
import re
from tryhackme_api import get_client
import persistence.database as db

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

@app.route('/data/screenshots/<filename>')
def serve_screenshot(filename):
    return send_from_directory('data/screenshots', filename)

@app.route('/api/vision/scan', methods=['POST'])
def scan_url():
    """
    AEGIS Visual Cortex:
    Visits a URL using Headless Chromium and returns a base64 screenshot.
    Also persists screenshot to disk for later retrieval.
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
            
            # Optional text extraction
            extracted_text = None
            if data.get('extract'):
                extracted_text = page.evaluate('document.body.innerText')
            
            browser.close()
            
            # --- PERSISTENCE: Save screenshot to disk ---
            # Create data directory if it doesn't exist
            os.makedirs('data/screenshots', exist_ok=True)
            
            # Sanitize URL for filename
            sanitized = re.sub(r'[^a-zA-Z0-9]', '_', url)
            if len(sanitized) > 50:
                sanitized = sanitized[:50]
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{sanitized}.png"
            filepath = os.path.join('data/screenshots', filename)
            
            with open(filepath, 'wb') as f:
                f.write(screenshot_bytes)
            
            print(f"[+] Screenshot saved to {filepath}")
            db.insert_screenshot(filename, url, None, filepath)
            # --- END PERSISTENCE ---
            
            # Encode
            b64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
            return jsonify({
                'success': True,
                'image': f"data:image/png;base64,{b64_img}",
                'message': f"Successfully scanned {url}",
                'persisted': True,
                'extracted_text': extracted_text,
                'filepath': filepath
            })
    except Exception as e:
        print(f"[!] Vision Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vision/screenshots', methods=['GET'])
def list_screenshots():
    """
    List persisted screenshots from the data/screenshots directory.
    """
    screenshot_dir = 'data/screenshots'
    if not os.path.exists(screenshot_dir):
        return jsonify({'success': True, 'screenshots': []})
    
    screenshots = []
    for filename in sorted(os.listdir(screenshot_dir), reverse=True):
        if filename.endswith('.png'):
            filepath = os.path.join(screenshot_dir, filename)
            stat = os.stat(filepath)
            screenshots.append({
                'filename': filename,
                'filepath': filepath,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'url': f'/api/vision/screenshots/{filename}'  # for future download endpoint
            })
    
    return jsonify({'success': True, 'screenshots': screenshots})

@app.route('/api/persistence/containers/history', methods=['GET'])
def persistence_containers_history():
    """
    Retrieve historical container snapshots from the database.
    """
    try:
        limit = request.args.get('limit', default=100, type=int)
        snapshots = db.get_recent_snapshots(limit=limit)
        return jsonify({'success': True, 'snapshots': snapshots})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/persistence/screenshots', methods=['GET'])
def persistence_screenshots():
    """
    Retrieve screenshot metadata from the database.
    """
    try:
        limit = request.args.get('limit', default=100, type=int)
        screenshots = db.get_recent_screenshots(limit=limit)
        return jsonify({'success': True, 'screenshots': screenshots})
    except Exception as e:
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
            container_id = c.short_id
            name = c.name
            status = c.status
            image = c.image.tags[0] if c.image.tags else 'unknown'
            data.append({
                'id': container_id,
                'name': name,
                'status': status,
                'image': image
            })
            # Persist snapshot
            db.insert_container_snapshot(container_id, name, status, image)
        return jsonify({'success': True, 'containers': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/containers/<container_id>/stats', methods=['GET'])
def container_stats(container_id):
    """
    Get current Docker stats for a container and store them in the database.
    """
    if not docker_client:
        return jsonify({'error': 'Docker daemon not connected'}), 503
    
    try:
        container = docker_client.containers.get(container_id)
        stats = container.stats(stream=False)
        
        # Parse Docker stats format
        cpu_stats = stats.get('cpu_stats', {})
        memory_stats = stats.get('memory_stats', {})
        network_stats = stats.get('networks', {})
        
        cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0)
        system_delta = cpu_stats.get('system_cpu_usage', 0)
        cpu_percent = 0.0
        if system_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * 100.0
        
        memory_mb = memory_stats.get('usage', 0) / (1024 * 1024)  # bytes to MB
        network_rx = network_stats.get('eth0', {}).get('rx_bytes', 0)
        network_tx = network_stats.get('eth0', {}).get('tx_bytes', 0)
        
        # Insert into database
        db.insert_container_stats(container_id, cpu_percent, memory_mb, network_rx, network_tx)
        
        # Return current stats
        return jsonify({
            'success': True,
            'container_id': container_id,
            'cpu_percent': cpu_percent,
            'memory_mb': memory_mb,
            'network_rx': network_rx,
            'network_tx': network_tx,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except docker.errors.NotFound:
        return jsonify({'success': False, 'error': 'Container not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/persistence/stats/<container_id>', methods=['GET'])
def persistence_container_stats(container_id):
    """
    Retrieve historical stats for a container from the database.
    """
    try:
        limit = request.args.get('limit', default=100, type=int)
        stats = db.get_container_stats(container_id, limit=limit)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for the AEGIS Dashboard.
    """
    try:
        # Check database connectivity
        db_conn_ok = False
        try:
            conn = db.get_db_connection()
            conn.execute('SELECT 1')
            db_conn_ok = True
            conn.close()
        except Exception:
            pass
        
        # Check Docker connectivity
        docker_ok = docker_client is not None
        
        return jsonify({
            'success': True,
            'database': 'ok' if db_conn_ok else 'error',
            'docker': 'connected' if docker_ok else 'disconnected',
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ------------------------------------------------------------------
# TryHackMe Integration Endpoints
# ------------------------------------------------------------------

@app.route('/api/tryhackme/profile', methods=['GET'])
def tryhackme_profile():
    """Fetch TryHackMe user profile."""
    client = get_client()
    profile = client.get_profile()
    return jsonify({'success': True, 'profile': profile})

@app.route('/api/tryhackme/rooms', methods=['GET'])
def tryhackme_rooms():
    """Fetch TryHackMe rooms with completion status."""
    client = get_client()
    limit = request.args.get('limit', default=20, type=int)
    rooms = client.get_rooms(limit=limit)
    return jsonify({'success': True, 'rooms': rooms})

@app.route('/api/tryhackme/progress', methods=['GET'])
def tryhackme_progress():
    """Fetch TryHackMe progress timeline."""
    client = get_client()
    days = request.args.get('days', default=30, type=int)
    progress = client.get_progress(days=days)
    return jsonify({'success': True, 'progress': progress})

# ------------------------------------------------------------------

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
        # Enhanced THM guidance
        try:
            client = get_client()
            rooms = client.get_rooms(limit=50)
            incomplete = [r for r in rooms if not r.get('completed')]
            if incomplete:
                # Suggest easiest incomplete room
                easy = [r for r in incomplete if r.get('difficulty') == 'Easy']
                target = easy[0] if easy else incomplete[0]
                response = f"THM module active. You have {len(incomplete)} incomplete rooms. Next recommended: **{target['title']}** ({target['difficulty']}, {target['category']}). Tags: {', '.join(target.get('tags', []))}"
            else:
                response = "THM module active. All rooms completed! 🎉 Consider exploring advanced paths like 'Red Team' or 'Blue Team'."
        except Exception as e:
            response = f"THM module encountered an error: {e}. (Using mock data)"
    elif any(word in user_message.lower() for word in ["what's next", "next room", "recommend", "suggest"]):
        try:
            client = get_client()
            rooms = client.get_rooms(limit=50)
            incomplete = [r for r in rooms if not r.get('completed')]
            if incomplete:
                # Pick a medium difficulty room
                med = [r for r in incomplete if r.get('difficulty') == 'Medium']
                easy = [r for r in incomplete if r.get('difficulty') == 'Easy']
                target = med[0] if med else (easy[0] if easy else incomplete[0])
                response = f"**{target['title']}** ({target['difficulty']}, {target['category']}) – {target.get('tags', [])[:3]}"
            else:
                response = "All rooms completed! Check out THM's 'Challenges' or 'Competitions' sections."
        except Exception as e:
            response = f"Could not fetch room data: {e}"
    elif "buffer overflow" in user_message.lower():
        response = "Buffer Overflow Prep room is completed. Next steps: practice stack pivoting, ROP chains, or try the 'Brainpan' room."
    elif "nmap" in user_message.lower() or "scan" in user_message.lower():
        response = "For Nmap scanning, try `nmap -sC -sV -oA scan <target>`. Common ports: 22, 80, 443, 8080, 3389. Use `-p-` for all ports (slower)."
    elif "help" in user_message.lower():
        response = "I can help with: THM room recommendations, Docker container status, error logs, and basic pentesting commands. Ask me about 'what's next' or 'buffer overflow'."
    else:
        response = f"Supervisor acknowledges: {user_message}. (LLM connection standby)"

    return jsonify({
        'success': True, 
        'response': response,
        'sender': 'Supervisor (Phi-3)'
    })

@app.route('/api/stats/visualize', methods=['POST'])
def visualize_metrics():
    """
    AEGIS Visual Data Endpoint.
    Accepts JSON metrics and returns a base64 PNG chart.
    """
    data = request.json
    metrics = data.get('metrics', {})
    chart_type = data.get('type', 'line')
    
    # Ensure matplotlib uses Agg backend (no GUI)
    matplotlib.use('Agg')
    
    try:
        # Create figure
        plt.figure(figsize=(8, 4))
        
        if chart_type == 'line':
            x = list(metrics.keys())
            y = list(metrics.values())
            plt.plot(x, y, marker='o', linestyle='-', color='teal')
            plt.title('AEGIS Metrics Timeline', fontsize=14)
            plt.xlabel('Metric')
            plt.ylabel('Value')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
        elif chart_type == 'bar':
            x = list(metrics.keys())
            y = list(metrics.values())
            plt.bar(x, y, color='steelblue', alpha=0.8)
            plt.title('AEGIS Metrics Distribution', fontsize=14)
            plt.xlabel('Metric')
            plt.ylabel('Value')
            plt.grid(True, alpha=0.3, axis='y')
            plt.xticks(rotation=45, ha='right')
        else:
            return jsonify({'error': f'Unsupported chart type: {chart_type}'}), 400
        
        plt.tight_layout()
        
        # Save to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        # Encode to base64
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': img_base64,
            'type': 'image/png',
            'chart_type': chart_type
        })
    
    except Exception as e:
        return jsonify({'error': f'Chart generation failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Listen on all interfaces so we can access it from host
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
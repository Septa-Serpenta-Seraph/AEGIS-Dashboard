from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from playwright.sync_api import sync_playwright
import base64
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hermes_aegis_secret'
# Allow CORS for local dev flexibilty
socketio = SocketIO(app, cors_allowed_origins="*")

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

if __name__ == '__main__':
    # Listen on all interfaces so we can access it from host
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

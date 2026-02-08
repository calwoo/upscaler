# Implementation Roadmap: Web UI for Real-ESRGAN Upscaler

Step-by-step guide to build the web interface, from MVP to full-featured application.

---

## Quick Start: MVP in 1-2 Hours

**Goal**: Get a basic working web UI with single image upload and upscaling.

### Files to Create

```
/home/user/upscaler/
├── web/
│   ├── app.py              # Flask backend
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css   # Styling
│   │   └── js/
│   │       └── main.js     # Frontend logic
│   └── templates/
│       └── index.html      # Main page
└── requirements-web.txt    # Web dependencies
```

---

## Phase 1: Basic Flask Setup (15 min)

### Step 1.1: Install Web Dependencies

Create `requirements-web.txt`:
```txt
flask==3.0.0
flask-cors==4.0.0
werkzeug==3.0.1
pillow==10.1.0
```

Install:
```bash
uv pip install -r requirements-web.txt
```

### Step 1.2: Create Flask App

Create `web/app.py`:
```python
#!/usr/bin/env python3
"""Flask web interface for Real-ESRGAN upscaler."""

import os
import uuid
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import cv2

# Import from existing upscale.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from upscale import setup_model

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = '/tmp/upscaler/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/upscaler/outputs'

# Create directories
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(parents=True, exist_ok=True)

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}

# Initialize model at startup (keeps it in memory)
print("Loading Real-ESRGAN model...")


class ModelConfig:
    """Simple object to mimic argparse args."""
    def __init__(self):
        self.scale = 4
        self.model = "general"
        self.face_enhance = False
        self.tile = 0
        self.gpu_id = None


MODELS = {}  # Cache models by config key


def get_model(scale=4, model_type="general", face_enhance=False):
    """Get or create model with given config."""
    key = f"{scale}_{model_type}_{face_enhance}"
    if key not in MODELS:
        config = ModelConfig()
        config.scale = scale
        config.model = model_type
        config.face_enhance = face_enhance
        print(f"Initializing model: {key}")
        upsampler, face_enhancer = setup_model(config)
        MODELS[key] = (upsampler, face_enhancer)
    return MODELS[key]


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve main page."""
    return render_template('index.html')


@app.route('/api/upscale', methods=['POST'])
def upscale_image():
    """Process image upscaling."""
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        # Get parameters
        scale = int(request.form.get('scale', 4))
        model_type = request.form.get('model', 'general')
        face_enhance = request.form.get('face_enhance', 'false').lower() == 'true'
        output_format = request.form.get('output_format', 'png')

        # Validate parameters
        if scale not in [2, 4]:
            return jsonify({'error': 'Scale must be 2 or 4'}), 400
        if model_type not in ['general', 'anime']:
            return jsonify({'error': 'Invalid model type'}), 400

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = Path(app.config['UPLOAD_FOLDER']) / f"{task_id}_{filename}"
        file.save(str(input_path))

        # Read image
        img = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            return jsonify({'error': 'Failed to read image'}), 400

        original_h, original_w = img.shape[:2]

        # Get model
        upsampler, face_enhancer = get_model(scale, model_type, face_enhance)

        # Process image
        if face_enhancer:
            _, _, output = face_enhancer.enhance(
                img, has_aligned=False, only_center_face=False, paste_back=True
            )
        else:
            output, _ = upsampler.enhance(img, outscale=scale)

        # Save output
        output_ext = f".{output_format}"
        output_filename = f"{task_id}_upscaled{output_ext}"
        output_path = Path(app.config['OUTPUT_FOLDER']) / output_filename
        cv2.imwrite(str(output_path), output)

        upscaled_h, upscaled_w = output.shape[:2]

        # Return result
        return jsonify({
            'status': 'success',
            'task_id': task_id,
            'download_url': f'/api/download/{task_id}',
            'original_size': [original_w, original_h],
            'upscaled_size': [upscaled_w, upscaled_h],
            'filename': output_filename
        })

    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<task_id>')
def download_image(task_id):
    """Download processed image."""
    try:
        # Find the file with this task_id
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        files = list(output_dir.glob(f"{task_id}_upscaled.*"))

        if not files:
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            files[0],
            as_attachment=True,
            download_name=f"upscaled_{files[0].name}"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Pre-load default model
    print("Pre-loading default model (4x general)...")
    get_model(4, "general", False)
    print("Ready!")

    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## Phase 2: HTML Template (20 min)

Create `web/templates/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-ESRGAN Image Upscaler</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 Real-ESRGAN Image Upscaler</h1>
            <p>AI-powered super-resolution for your images</p>
        </header>

        <!-- Configuration Panel -->
        <div class="config-panel">
            <h2>⚙️ Configuration</h2>
            <div class="config-row">
                <label>
                    Scale:
                    <div class="button-group">
                        <button class="btn-toggle" data-value="2">2x</button>
                        <button class="btn-toggle active" data-value="4">4x</button>
                    </div>
                    <input type="hidden" id="scale" value="4">
                </label>

                <label>
                    Model:
                    <div class="button-group">
                        <button class="btn-toggle active" data-value="general">General</button>
                        <button class="btn-toggle" data-value="anime">Anime</button>
                    </div>
                    <input type="hidden" id="model" value="general">
                </label>

                <label>
                    <input type="checkbox" id="face-enhance">
                    Face Enhancement
                </label>

                <label>
                    Format:
                    <select id="output-format">
                        <option value="png">PNG</option>
                        <option value="jpg">JPG</option>
                    </select>
                </label>
            </div>
        </div>

        <!-- Drop Zone -->
        <div id="drop-zone" class="drop-zone">
            <div class="drop-zone-content">
                <div class="drop-icon">📁 📷</div>
                <p class="drop-text">Drop your image here</p>
                <p class="drop-subtext">or</p>
                <button class="btn-browse" onclick="document.getElementById('file-input').click()">
                    Browse Files
                </button>
                <input type="file" id="file-input" accept="image/*" style="display: none;">
                <p class="drop-info">Supports: PNG, JPG, WEBP, BMP, TIFF | Max: 50 MB</p>
            </div>
        </div>

        <!-- Preview Area (hidden initially) -->
        <div id="preview-area" class="preview-area" style="display: none;">
            <div class="preview-column">
                <h3>📤 Original</h3>
                <div class="image-container">
                    <img id="original-image" alt="Original image">
                </div>
                <div class="image-info">
                    <span id="original-filename"></span><br>
                    <span id="original-dimensions"></span>
                </div>
                <button class="btn-secondary" onclick="resetUpload()">Upload New</button>
            </div>

            <div class="preview-column">
                <h3 id="result-title">✨ Upscaled</h3>
                <div class="image-container" id="result-container">
                    <div id="processing-overlay" style="display: none;">
                        <div class="spinner"></div>
                        <p id="progress-text">Processing...</p>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                        <p id="progress-percentage">0%</p>
                    </div>
                    <img id="upscaled-image" alt="Upscaled image" style="display: none;">
                </div>
                <div class="image-info" id="result-info" style="display: none;">
                    <span id="upscaled-dimensions"></span><br>
                    <span id="processing-time"></span>
                </div>
                <div id="result-actions" style="display: none;">
                    <button class="btn-primary" id="download-btn">Download</button>
                    <button class="btn-secondary" onclick="resetUpload()">New Image</button>
                </div>
                <button class="btn-primary" id="start-upscale-btn" onclick="startUpscaling()">
                    Start Upscale
                </button>
            </div>
        </div>

        <!-- Error Message -->
        <div id="error-message" class="error-message" style="display: none;"></div>
    </div>

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

---

## Phase 3: CSS Styling (20 min)

Create `web/static/css/style.css`:
```css
/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
    color: #212529;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

/* Header */
header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #e9ecef;
}

header h1 {
    font-size: 2.5em;
    color: #4A90E2;
    margin-bottom: 10px;
}

header p {
    color: #6c757d;
    font-size: 1.1em;
}

/* Configuration Panel */
.config-panel {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
}

.config-panel h2 {
    font-size: 1.3em;
    margin-bottom: 15px;
    color: #495057;
}

.config-row {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    align-items: center;
}

.config-row label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 500;
}

.button-group {
    display: flex;
    gap: 5px;
}

.btn-toggle {
    padding: 8px 16px;
    border: 2px solid #dee2e6;
    background: white;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.95em;
    transition: all 0.2s ease;
}

.btn-toggle:hover {
    border-color: #4A90E2;
}

.btn-toggle.active {
    background: #4A90E2;
    color: white;
    border-color: #4A90E2;
}

select {
    padding: 8px 12px;
    border: 2px solid #dee2e6;
    border-radius: 6px;
    font-size: 0.95em;
}

/* Drop Zone */
.drop-zone {
    border: 3px dashed #dee2e6;
    border-radius: 12px;
    padding: 60px 40px;
    text-align: center;
    background: #f8f9fa;
    transition: all 0.3s ease;
    cursor: pointer;
}

.drop-zone:hover,
.drop-zone.drag-over {
    border-color: #4A90E2;
    background: #e7f3ff;
    transform: scale(1.02);
}

.drop-icon {
    font-size: 3em;
    margin-bottom: 15px;
}

.drop-text {
    font-size: 1.3em;
    font-weight: 600;
    color: #495057;
    margin-bottom: 10px;
}

.drop-subtext {
    color: #6c757d;
    margin-bottom: 15px;
}

.drop-info {
    font-size: 0.9em;
    color: #6c757d;
    margin-top: 15px;
}

/* Buttons */
.btn-browse,
.btn-primary,
.btn-secondary {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary {
    background: #4A90E2;
    color: white;
}

.btn-primary:hover {
    background: #3a7bc8;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.btn-secondary {
    background: white;
    color: #4A90E2;
    border: 2px solid #4A90E2;
}

.btn-secondary:hover {
    background: #f8f9fa;
}

.btn-browse {
    background: #4A90E2;
    color: white;
}

/* Preview Area */
.preview-area {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin-top: 30px;
}

.preview-column {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
}

.preview-column h3 {
    margin-bottom: 15px;
    color: #495057;
}

.image-container {
    background: white;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 15px;
    position: relative;
    overflow: hidden;
}

.image-container img {
    max-width: 100%;
    max-height: 500px;
    object-fit: contain;
}

.image-info {
    font-size: 0.9em;
    color: #6c757d;
    margin-bottom: 15px;
}

/* Processing Overlay */
#processing-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.95);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 10;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 4px solid #e9ecef;
    border-top-color: #4A90E2;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 20px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.progress-bar {
    width: 80%;
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
    margin: 15px 0;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4A90E2, #7B68EE);
    width: 0%;
    transition: width 0.3s ease;
}

#progress-percentage {
    font-size: 1.2em;
    font-weight: 600;
    color: #4A90E2;
}

/* Error Message */
.error-message {
    background: #f8d7da;
    color: #721c24;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #f5c6cb;
    margin-top: 20px;
}

/* Result Actions */
#result-actions {
    display: flex;
    gap: 10px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .preview-area {
        grid-template-columns: 1fr;
    }

    .config-row {
        flex-direction: column;
        align-items: flex-start;
    }

    header h1 {
        font-size: 1.8em;
    }
}
```

---

## Phase 4: JavaScript Logic (30 min)

Create `web/static/js/main.js`:
```javascript
// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const previewArea = document.getElementById('preview-area');
const originalImage = document.getElementById('original-image');
const upscaledImage = document.getElementById('upscaled-image');
const processingOverlay = document.getElementById('processing-overlay');
const errorMessage = document.getElementById('error-message');
const startUpscaleBtn = document.getElementById('start-upscale-btn');
const downloadBtn = document.getElementById('download-btn');

// State
let uploadedFile = null;
let currentTaskId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setupToggleButtons();
});

function setupEventListeners() {
    // Drag and drop
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);

    // File input
    fileInput.addEventListener('change', handleFileSelect);
}

function setupToggleButtons() {
    document.querySelectorAll('.btn-toggle').forEach(btn => {
        btn.addEventListener('click', function() {
            const group = this.parentElement;
            const inputId = this.closest('label').querySelector('input[type="hidden"]').id;

            // Remove active from siblings
            group.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));

            // Add active to clicked
            this.classList.add('active');

            // Update hidden input
            document.getElementById(inputId).value = this.dataset.value;
        });
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function processFile(file) {
    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/bmp', 'image/tiff'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload an image (PNG, JPG, WEBP, BMP, TIFF).');
        return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showError('File too large. Maximum size is 50 MB.');
        return;
    }

    uploadedFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        originalImage.src = e.target.result;
        document.getElementById('original-filename').textContent = file.name;

        // Get image dimensions
        const img = new Image();
        img.onload = () => {
            document.getElementById('original-dimensions').textContent =
                `${img.width} × ${img.height} px`;
        };
        img.src = e.target.result;

        // Show preview area, hide drop zone
        dropZone.style.display = 'none';
        previewArea.style.display = 'grid';
        errorMessage.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

async function startUpscaling() {
    if (!uploadedFile) return;

    // Hide start button, show processing overlay
    startUpscaleBtn.style.display = 'none';
    processingOverlay.style.display = 'flex';
    upscaledImage.style.display = 'none';
    document.getElementById('result-info').style.display = 'none';
    document.getElementById('result-actions').style.display = 'none';

    // Get configuration
    const scale = document.getElementById('scale').value;
    const model = document.getElementById('model').value;
    const faceEnhance = document.getElementById('face-enhance').checked;
    const outputFormat = document.getElementById('output-format').value;

    // Prepare form data
    const formData = new FormData();
    formData.append('image', uploadedFile);
    formData.append('scale', scale);
    formData.append('model', model);
    formData.append('face_enhance', faceEnhance);
    formData.append('output_format', outputFormat);

    // Simulate progress (since we don't have real-time updates yet)
    simulateProgress();

    try {
        const startTime = Date.now();

        const response = await fetch('/api/upscale', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Upload failed');
        }

        const processingTime = ((Date.now() - startTime) / 1000).toFixed(1);

        // Update progress to 100%
        updateProgress(100, 'Complete!');

        // Wait a moment before showing result
        setTimeout(() => {
            displayResult(result, processingTime);
        }, 500);

    } catch (error) {
        processingOverlay.style.display = 'none';
        startUpscaleBtn.style.display = 'block';
        showError(`Error: ${error.message}`);
    }
}

function simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 95) {
            clearInterval(interval);
            progress = 95;
        }
        updateProgress(progress, 'Processing image...');
    }, 300);
}

function updateProgress(percent, message) {
    document.getElementById('progress-fill').style.width = percent + '%';
    document.getElementById('progress-percentage').textContent = Math.round(percent) + '%';
    document.getElementById('progress-text').textContent = message;
}

function displayResult(result, processingTime) {
    currentTaskId = result.task_id;

    // Hide processing overlay
    processingOverlay.style.display = 'none';

    // Show upscaled image
    upscaledImage.src = result.download_url;
    upscaledImage.style.display = 'block';

    // Show result info
    document.getElementById('upscaled-dimensions').textContent =
        `${result.upscaled_size[0]} × ${result.upscaled_size[1]} px`;
    document.getElementById('processing-time').textContent =
        `Processed in ${processingTime}s`;
    document.getElementById('result-info').style.display = 'block';

    // Show action buttons
    document.getElementById('result-actions').style.display = 'flex';

    // Setup download button
    downloadBtn.onclick = () => {
        window.location.href = result.download_url;
    };
}

function resetUpload() {
    uploadedFile = null;
    currentTaskId = null;
    fileInput.value = '';

    dropZone.style.display = 'block';
    previewArea.style.display = 'none';
    errorMessage.style.display = 'none';
    startUpscaleBtn.style.display = 'block';
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}
```

---

## Phase 5: Testing & Running (10 min)

### Start the Server

```bash
cd /home/user/upscaler/web
python app.py
```

### Test Workflow

1. Open browser: `http://localhost:5000`
2. Drag an image onto the drop zone
3. Configure settings (scale, model, etc.)
4. Click "Start Upscale"
5. Wait for processing
6. Click "Download" to get result

---

## Phase 6: Enhancements (Optional)

### 6.1: Add Real-Time Progress with WebSockets

Install:
```bash
uv pip install flask-socketio python-socketio
```

Update `app.py`:
```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

# In upscale_image function, emit progress:
socketio.emit('progress', {'task_id': task_id, 'percent': 50})
```

Update `main.js`:
```javascript
const socket = io();
socket.on('progress', (data) => {
    updateProgress(data.percent, data.message);
});
```

### 6.2: Add Batch Processing

```python
@app.route('/api/batch', methods=['POST'])
def batch_upscale():
    files = request.files.getlist('images')
    task_ids = []

    for file in files:
        # Process each file...
        task_id = process_single_image(file)
        task_ids.append(task_id)

    return jsonify({'task_ids': task_ids})
```

### 6.3: Add Before/After Comparison Slider

Install:
```bash
npm install img-comparison-slider
```

Or use pure CSS/JS solution in wireframes document.

---

## Deployment Checklist

### Local Development
- [x] Flask app runs on localhost:5000
- [ ] All features work as expected
- [ ] Error handling tested

### Production Deployment
- [ ] Use Gunicorn instead of Flask dev server
- [ ] Add Nginx reverse proxy
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Set up proper file cleanup (cron job)
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Set up logging and monitoring
- [ ] Use environment variables for configs

### Example Production Setup

```bash
# Install Gunicorn
uv pip install gunicorn

# Run with Gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 web.app:app
```

Nginx config (`/etc/nginx/sites-available/upscaler`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### Issue: "Model not loading"
**Solution**: Ensure models auto-download on first run. Check internet connection and GitHub access.

### Issue: "Out of GPU memory"
**Solution**: Reduce batch size, add `--tile 400` parameter, or use CPU mode.

### Issue: "File upload fails"
**Solution**: Check `MAX_CONTENT_LENGTH` in Flask config. Ensure temp directories exist.

### Issue: "Slow processing"
**Solution**:
- Pre-load models at startup
- Use GPU if available
- Optimize image size before processing

---

## Next Steps

1. **Run MVP**: Follow Phase 1-5 to get basic version working
2. **Test thoroughly**: Try different images, scales, and models
3. **Add enhancements**: Implement Phase 6 features as needed
4. **Deploy**: Follow deployment checklist for production
5. **Monitor**: Set up logging and analytics
6. **Iterate**: Gather user feedback and improve

---

**Estimated Time to MVP**: 1-2 hours
**Estimated Time to Production**: 4-6 hours
**Status**: Ready to implement

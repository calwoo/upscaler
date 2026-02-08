# UI Design Plan: Real-ESRGAN Image Upscaler Web Interface

## Overview

Transform the CLI-based Real-ESRGAN upscaler into a modern web application with drag-and-drop image upload and real-time upscaling preview.

## Design Goals

1. **Intuitive UX**: Simple drag-and-drop interface requiring no technical knowledge
2. **Visual Feedback**: Clear progress indicators and before/after comparison
3. **Responsive Design**: Works on desktop, tablet, and mobile devices
4. **Fast Processing**: Efficient backend processing with queue management
5. **Accessibility**: Keyboard navigation and screen reader support

---

## Technology Stack

### Option A: Flask + Vanilla JS (Recommended for simplicity)
- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, vanilla JavaScript
- **Benefits**: Minimal dependencies, easy integration with existing Python code
- **Trade-offs**: More manual DOM manipulation

### Option B: FastAPI + React (Modern alternative)
- **Backend**: FastAPI (async Python web framework)
- **Frontend**: React with Vite
- **Benefits**: Modern async processing, component reusability, better scalability
- **Trade-offs**: More complex setup, requires Node.js tooling

### Recommended: **Option A (Flask + Vanilla JS)** for faster MVP

---

## UI/UX Design

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│                     Header Bar                          │
│  [Logo] Real-ESRGAN Image Upscaler           [About]    │
└─────────────────────────────────────────────────────────┘
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │          Configuration Panel                     │   │
│  │  Scale: [2x] [4x*]                              │   │
│  │  Model: [General*] [Anime]                      │   │
│  │  □ Face Enhancement                             │   │
│  │  Output Format: [PNG*] [JPG]                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                  │   │
│  │         ┌───────────────────────┐               │   │
│  │         │   📁  Drop Image Here │               │   │
│  │         │                       │               │   │
│  │         │  or click to browse   │               │   │
│  │         └───────────────────────┘               │   │
│  │                                                  │   │
│  │            Drop Zone Area                       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  [After image is uploaded]                               │
│  ┌──────────────────────┬──────────────────────┐        │
│  │   Original Image     │   Upscaled Result    │        │
│  │                      │                      │        │
│  │  ┌────────────────┐ │  ┌────────────────┐  │        │
│  │  │                │ │  │   [Loading...]  │  │        │
│  │  │  [Image Preview]│ │  │   Progress Bar  │  │        │
│  │  │                │ │  │      45%        │  │        │
│  │  └────────────────┘ │  └────────────────┘  │        │
│  │  320 × 240         │  1280 × 960          │        │
│  │                      │                      │        │
│  │                      │  [Download] [Reset]  │        │
│  └──────────────────────┴──────────────────────┘        │
│                                                           │
│  [Processing Queue - for multiple images]                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ • image1.jpg ✓ Complete   [Download]            │   │
│  │ • image2.png ⏳ Processing... (23%)              │   │
│  │ • image3.jpg ⏸ Queued                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Key UI Components

#### 1. **Drop Zone**
- Large, prominent area (min 400px × 300px)
- Visual feedback on hover (border highlight)
- Shows accepted file types (.png, .jpg, .jpeg, .webp, .bmp, .tiff)
- Max file size indicator (configurable, e.g., 50MB)
- Support for multiple file uploads (batch processing)

#### 2. **Configuration Panel**
- **Scale Selector**: Toggle buttons for 2x/4x
- **Model Selector**: General vs Anime (radio buttons or toggle)
- **Face Enhancement**: Checkbox with tooltip explaining GFPGAN
- **Output Format**: PNG (lossless) vs JPG (smaller file size)
- **Advanced Options** (collapsible):
  - Tile size for memory management
  - GPU selection (if multiple available)

#### 3. **Image Preview Area**
- **Before/After Split View**: Side-by-side comparison
- **Zoom Controls**: Pan and zoom for detail inspection
- **Image Info**: Display resolution, file size, format
- **Comparison Slider** (optional): Draggable divider to compare quality

#### 4. **Progress Indicator**
- Linear progress bar showing processing percentage
- Estimated time remaining
- Current step indicator (e.g., "Loading model...", "Upscaling...", "Saving...")
- Cancel button to abort processing

#### 5. **Download/Actions Area**
- Download button (only enabled after processing completes)
- Option to download original + upscaled as ZIP (batch mode)
- Reset/Clear button to start over
- Share button (optional - for saved results)

#### 6. **Batch Processing Queue**
- List of uploaded images with individual status
- Drag to reorder queue priority
- Remove individual items from queue
- Bulk download all completed images

---

## User Flow

### Single Image Flow
1. User lands on page → sees drop zone and config panel
2. User selects settings (scale, model, etc.)
3. User drags image onto drop zone OR clicks to browse
4. Image preview appears in "Original" panel
5. User clicks "Upscale" button (or auto-start on upload)
6. Progress bar shows processing status
7. Upscaled image appears in "Result" panel
8. User can download, compare with slider, or reset

### Batch Processing Flow
1. User drags multiple images onto drop zone
2. All images appear in processing queue
3. Processing starts automatically (first in queue)
4. Each image shows individual progress
5. Completed images show download button
6. User can download individually or as batch ZIP

---

## Backend Architecture

### API Endpoints

#### `POST /api/upscale`
**Request:**
```json
{
  "image": "base64_encoded_image_data",
  "scale": 4,
  "model": "general",
  "face_enhance": false,
  "output_format": "png",
  "tile": 0
}
```

**Response:**
```json
{
  "status": "success",
  "task_id": "uuid-1234",
  "result_url": "/api/download/uuid-1234",
  "original_size": [320, 240],
  "upscaled_size": [1280, 960],
  "processing_time": 5.2
}
```

#### `GET /api/status/<task_id>`
**Response:**
```json
{
  "task_id": "uuid-1234",
  "status": "processing",  // "queued", "processing", "completed", "failed"
  "progress": 45,
  "message": "Upscaling image..."
}
```

#### `GET /api/download/<task_id>`
- Returns the upscaled image file
- Sets appropriate content-disposition headers for download

#### `POST /api/batch`
- Accepts multiple images in form data
- Returns array of task IDs for tracking

### Processing Strategy

1. **Task Queue**: Use Celery or simple threading for background jobs
2. **Progress Tracking**: WebSocket or SSE for real-time updates
3. **File Storage**:
   - Store uploads in `/tmp/upscaler/uploads/<task_id>/`
   - Store results in `/tmp/upscaler/results/<task_id>/`
   - Cleanup after 1 hour or on download
4. **Model Caching**: Load models once at startup, keep in memory
5. **Concurrent Processing**: Limit to 1-2 concurrent tasks to manage GPU memory

---

## Visual Design Specifications

### Color Scheme
- **Primary**: #4A90E2 (Blue - trustworthy, tech)
- **Secondary**: #7B68EE (Purple - creative, AI)
- **Success**: #5CB85C (Green)
- **Warning**: #F0AD4E (Amber)
- **Error**: #D9534F (Red)
- **Background**: #F8F9FA (Light gray)
- **Surface**: #FFFFFF (White)
- **Text**: #212529 (Dark gray)

### Typography
- **Headers**: Inter or Roboto (sans-serif, 600 weight)
- **Body**: System font stack for performance
- **Code/Specs**: Monospace for file info

### Spacing
- Base unit: 8px grid system
- Container max-width: 1200px
- Mobile breakpoint: 768px

### Animations
- Drop zone hover: 200ms ease-in-out border color transition
- Progress bar: Smooth fill animation
- Image fade-in: 300ms opacity transition
- Drag feedback: Scale transform on dragged items

---

## Accessibility Features

1. **Keyboard Navigation**
   - Tab through all interactive elements
   - Enter/Space to activate buttons
   - Escape to close modals/cancel operations

2. **Screen Reader Support**
   - ARIA labels for all controls
   - Live regions for progress updates
   - Alt text for image previews

3. **Visual Accessibility**
   - WCAG AA contrast ratios (4.5:1 for text)
   - Focus indicators on all interactive elements
   - No color-only information (use icons + color)

4. **Error Handling**
   - Clear error messages
   - Suggestions for fixes (e.g., "File too large, try compressing")
   - Graceful fallbacks for unsupported features

---

## File Structure

```
/home/user/upscaler/
├── web/
│   ├── app.py                 # Flask application
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css     # Main stylesheet
│   │   ├── js/
│   │   │   ├── main.js        # Core UI logic
│   │   │   ├── dropzone.js    # Drag-and-drop handler
│   │   │   └── uploader.js    # API communication
│   │   └── images/
│   │       └── logo.svg
│   ├── templates/
│   │   ├── index.html         # Main page
│   │   └── components/
│   │       ├── dropzone.html
│   │       └── config.html
│   └── uploads/               # Temp upload storage
├── upscale.py                 # Core processing (reused)
└── requirements-web.txt       # Web dependencies
```

---

## Implementation Phases

### Phase 1: Basic Web UI (MVP)
- [ ] Set up Flask application
- [ ] Create HTML/CSS layout with drop zone
- [ ] Implement file upload and validation
- [ ] Create API endpoint for single image upscaling
- [ ] Display results with download button
- [ ] Basic error handling

**Estimated Output**: Working single-image upscaler web interface

### Phase 2: Enhanced UX
- [ ] Add before/after comparison view
- [ ] Implement real-time progress tracking
- [ ] Add configuration panel (scale, model selection)
- [ ] Image zoom/pan functionality
- [ ] Responsive design for mobile

### Phase 3: Batch Processing
- [ ] Multiple file upload support
- [ ] Processing queue UI
- [ ] Batch download as ZIP
- [ ] Queue management (pause, cancel, reorder)

### Phase 4: Advanced Features
- [ ] Face enhancement toggle
- [ ] WebSocket for real-time updates
- [ ] Image comparison slider
- [ ] Session persistence (save results for 24h)
- [ ] Usage statistics/analytics

### Phase 5: Production Ready
- [ ] Docker containerization
- [ ] Rate limiting and abuse prevention
- [ ] HTTPS setup
- [ ] CDN for static assets
- [ ] Monitoring and logging

---

## Technical Considerations

### Performance Optimization
1. **Image Compression**: Compress previews for faster loading
2. **Lazy Loading**: Load components as needed
3. **Caching**: Cache model weights, serve static assets efficiently
4. **Throttling**: Limit upload size and concurrent requests

### Security
1. **File Validation**: Strict checking of uploaded files (magic bytes, not just extension)
2. **Size Limits**: Prevent resource exhaustion (e.g., 50MB max)
3. **Rate Limiting**: Prevent abuse (e.g., 10 requests per IP per hour)
4. **Sanitization**: Clean filenames, prevent path traversal
5. **CORS**: Configure properly if API is separate domain

### Scalability
1. **Horizontal Scaling**: Stateless design for multiple workers
2. **Cloud Storage**: S3/GCS for uploaded/processed images (instead of local disk)
3. **GPU Queue**: Manage GPU memory for concurrent requests
4. **Caching Layer**: Redis for session data and queue management

---

## Testing Plan

### Unit Tests
- [ ] File upload validation
- [ ] Image format conversion
- [ ] Configuration parameter validation
- [ ] API endpoint responses

### Integration Tests
- [ ] End-to-end upscaling workflow
- [ ] Batch processing pipeline
- [ ] Error handling scenarios
- [ ] Concurrent request handling

### UI Tests
- [ ] Drag-and-drop functionality
- [ ] Form validation
- [ ] Progress bar updates
- [ ] Download functionality

### Performance Tests
- [ ] Large image handling (4K+)
- [ ] Concurrent user simulation
- [ ] Memory leak detection
- [ ] GPU memory management

---

## Deployment Options

### Option 1: Local Server
- Run Flask dev server: `python web/app.py`
- Access at `http://localhost:5000`
- Best for: Personal use, testing

### Option 2: Production Server
- Use Gunicorn/uWSGI + Nginx
- Deploy on VPS (DigitalOcean, Linode, etc.)
- Requires GPU-enabled instance
- Best for: Small team, controlled access

### Option 3: Cloud Platform
- Deploy on Google Cloud Run, AWS Lambda (with GPU), or Hugging Face Spaces
- Serverless or container-based
- Auto-scaling capabilities
- Best for: Public access, high traffic

---

## Future Enhancements

1. **User Accounts**: Save processing history, favorites
2. **Presets**: Save common configurations
3. **AI Model Selection**: Support more models (GFPGAN, CodeFormer, etc.)
4. **Video Upscaling**: Frame-by-frame upscaling for short clips
5. **API Keys**: For programmatic access
6. **Comparison Gallery**: Community-shared before/after examples
7. **Mobile App**: Native iOS/Android wrapper
8. **Browser Extension**: Right-click to upscale any image

---

## Resources

- Flask Documentation: https://flask.palletsprojects.com/
- Real-ESRGAN: https://github.com/xinntao/Real-ESRGAN
- HTML Drag and Drop API: https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API
- Accessibility Guidelines: https://www.w3.org/WAI/WCAG21/quickref/

---

**Last Updated**: 2026-02-08
**Status**: Design phase - ready for implementation

/** @format */

const videoInput = document.getElementById('videoUpload');
const videoPreview = document.getElementById('previewVideo');
const uploadPrompt = document.getElementById('uploadPrompt');
const resetBtn = document.getElementById('resetVideoBtn');
const modelSelect = document.getElementById('modelSelect');
const detectBtn = document.getElementById('detectBtn');
const uploadCanvas = document.getElementById('uploadCanvas');
const uploadCtx = uploadCanvas.getContext('2d');
const status = document.getElementById('status');

let isDetecting = false;
let lastBoxes = [];

// ✅ Cập nhật kích thước canvas chính xác
function updateCanvasSize() {
    // Canvas sẽ có kích thước bằng container để overlay chính xác
    const containerRect = videoPreview.getBoundingClientRect();
    uploadCanvas.width = containerRect.width;
    uploadCanvas.height = containerRect.height;
    uploadCanvas.style.width = containerRect.width + 'px';
    uploadCanvas.style.height = containerRect.height + 'px';
}

// ✅ Tính toán tỷ lệ scale từ video gốc sang hiển thị
function getVideoScale() {
    if (!videoPreview.videoWidth || !videoPreview.videoHeight) {
        return { scaleX: 1, scaleY: 1, offsetX: 0, offsetY: 0 };
    }

    const videoAspect = videoPreview.videoWidth / videoPreview.videoHeight;
    const displayAspect = videoPreview.clientWidth / videoPreview.clientHeight;

    let scaleX,
        scaleY,
        offsetX = 0,
        offsetY = 0;

    if (displayAspect > videoAspect) {
        // Video có thanh đen hai bên
        scaleY = videoPreview.clientHeight / videoPreview.videoHeight;
        scaleX = scaleY;
        const actualWidth = videoPreview.videoWidth * scaleX;
        offsetX = (videoPreview.clientWidth - actualWidth) / 2;
    } else {
        // Video có thanh đen trên dưới
        scaleX = videoPreview.clientWidth / videoPreview.videoWidth;
        scaleY = scaleX;
        const actualHeight = videoPreview.videoHeight * scaleY;
        offsetY = (videoPreview.clientHeight - actualHeight) / 2;
    }

    return { scaleX, scaleY, offsetX, offsetY };
}

// Load model list from API
fetch('/api/models/get_all')
    .then((res) => res.json())
    .then((data) => {
        if (data.models) {
            modelSelect.innerHTML = '';
            data.models.forEach((m) => {
                const opt = document.createElement('option');
                opt.value = m.model_id;
                opt.textContent = m.model_name;
                modelSelect.appendChild(opt);
            });
            modelSelect.value = data.models[0].model_id;
        }
    })
    .catch((error) => {
        console.error('Error loading models:', error);
        // Fallback to mock data if API fails
        modelSelect.innerHTML = `
                        <option value="1">YOLOv8 Fire Detection</option>
                        <option value="2">Custom Fire Model</option>
                    `;
        modelSelect.value = '1';
    });

modelSelect.addEventListener('change', () => {
    detectBtn.disabled = !videoPreview.src;
});

videoInput.addEventListener('click', () => (videoInput.value = ''));
videoInput.addEventListener('change', () => {
    const file = videoInput.files[0];
    if (!file) return;

    // ✅ Reset lại video hoàn toàn trước khi gán mới
    videoPreview.pause();
    videoPreview.removeAttribute('src');
    videoPreview.load();

    const url = URL.createObjectURL(file);
    videoPreview.src = url;
    videoPreview.style.display = 'block';
    uploadPrompt.style.display = 'none';
    videoInput.style.pointerEvents = 'none';
    resetBtn.classList.remove('d-none');
    detectBtn.disabled = !modelSelect.value;

    videoPreview.addEventListener('loadedmetadata', () => {
        updateCanvasSize();
        uploadCanvas.style.display = 'block';
    });

    window.addEventListener('resize', updateCanvasSize);
});

resetBtn.addEventListener('click', () => {
    // Ngừng video
    videoPreview.pause();

    // Gỡ bỏ URL cũ
    if (videoPreview.src && videoPreview.src.startsWith('blob:')) {
        URL.revokeObjectURL(videoPreview.src);
    }

    // Reset src và load lại
    videoPreview.removeAttribute('src');
    videoPreview.load();

    // ✅ Ẩn thẻ video, hiện prompt ban đầu
    videoPreview.style.display = 'none';
    uploadPrompt.style.display = 'block';

    // ✅ Ẩn canvas và reset form
    uploadCanvas.style.display = 'none';
    videoInput.value = '';
    videoInput.style.pointerEvents = 'auto';
    resetBtn.classList.add('d-none');
    detectBtn.disabled = true;

    // ✅ Reset logic
    isDetecting = false;
    lastBoxes = [];
    status.innerHTML = '';
});

// ✅ Gửi frame để detect (real API call)
async function detectFrame(imageData) {
    const modelId = modelSelect.value;

    try {
        const res = await fetch('/api/predict/detect_video_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: imageData,
                model_id: modelId,
            }),
        });

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = await res.json();
        lastBoxes = data.detections || [];
    } catch (error) {
        console.error('Detection error:', error);
        lastBoxes = [];
        status.innerHTML =
            '<span class="text-danger">❌ Lỗi kết nối API</span>';
    }
}

// ✅ Vẽ bounding boxes với tỷ lệ chính xác
function drawBoundingBoxes() {
    uploadCtx.clearRect(0, 0, uploadCanvas.width, uploadCanvas.height);

    if (lastBoxes.length === 0) return;

    const { scaleX, scaleY, offsetX, offsetY } = getVideoScale();

    lastBoxes.forEach(({ bbox, confidence, label }) => {
        const [x1, y1, x2, y2] = bbox;

        // ✅ Chuyển từ tọa độ video gốc sang tọa độ hiển thị
        const displayX1 = x1 * scaleX + offsetX;
        const displayY1 = y1 * scaleY + offsetY;
        const displayX2 = x2 * scaleX + offsetX;
        const displayY2 = y2 * scaleY + offsetY;

        const width = displayX2 - displayX1;
        const height = displayY2 - displayY1;

        // Vẽ bbox
        uploadCtx.strokeStyle = '#ff0000';
        uploadCtx.lineWidth = 2;
        uploadCtx.strokeRect(displayX1, displayY1, width, height);

        // Vẽ label
        const labelText = `🔥 ${label} ${(confidence * 100).toFixed(1)}%`;
        uploadCtx.fillStyle = '#ff0000';
        uploadCtx.font = '14px Arial';

        // Background cho text
        const textMetrics = uploadCtx.measureText(labelText);
        uploadCtx.fillStyle = 'rgba(255, 0, 0, 0.8)';
        uploadCtx.fillRect(
            displayX1,
            displayY1 - 20,
            textMetrics.width + 8,
            20
        );

        // Text
        uploadCtx.fillStyle = '#ffffff';
        uploadCtx.fillText(labelText, displayX1 + 4, displayY1 - 6);
    });
}

// ✅ Main detection loop
function drawLoop() {
    if (!isDetecting || videoPreview.paused || videoPreview.ended) {
        return;
    }

    drawBoundingBoxes();

    // Gửi frame mới mỗi 300ms để tránh spam
    const now = Date.now();
    if (!drawLoop.lastDetectTime || now - drawLoop.lastDetectTime > 300) {
        drawLoop.lastDetectTime = now;

        // Tạo canvas để capture frame hiện tại
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = videoPreview.videoWidth;
        tempCanvas.height = videoPreview.videoHeight;
        const ctx = tempCanvas.getContext('2d');
        ctx.drawImage(videoPreview, 0, 0);
        const imageData = tempCanvas.toDataURL('image/jpeg', 0.8);

        detectFrame(imageData);
    }

    requestAnimationFrame(drawLoop);
}

// ✅ Event listeners
detectBtn.addEventListener('click', () => {
    if (!videoPreview.src || isDetecting) return;

    isDetecting = true;
    videoPreview.play();
    drawLoop();
    detectBtn.textContent = 'Đang phát hiện...';
    detectBtn.disabled = true;
    status.innerHTML =
        '<span class="text-success">🔴 Đang phát hiện cháy...</span>';
});

videoPreview.addEventListener('pause', () => {
    isDetecting = false;
    detectBtn.textContent = 'Tiếp tục';
    detectBtn.disabled = false;
    status.innerHTML = '<span class="text-warning">⏸️ Tạm dừng</span>';
});

videoPreview.addEventListener('ended', () => {
    isDetecting = false;
    detectBtn.textContent = 'Bắt đầu';
    detectBtn.disabled = false;
    status.innerHTML = '<span class="text-info">✅ Hoàn thành</span>';
});

videoPreview.addEventListener('play', () => {
    if (!isDetecting) {
        isDetecting = true;
        drawLoop();
        detectBtn.textContent = 'Đang phát hiện...';
        detectBtn.disabled = true;
        status.innerHTML =
            '<span class="text-success">🔴 Đang phát hiện cháy...</span>';
    }
});

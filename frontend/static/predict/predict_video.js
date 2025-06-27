/** @format */

const videoUpload = document.getElementById('videoUpload');
const fileNameSpan = document.getElementById('FileName');
const previewVideo = document.getElementById('previewVideo');
const uploadCanvas = document.getElementById('uploadCanvas');
const uploadCtx = uploadCanvas.getContext('2d');
const detectBtn = document.getElementById('detectBtn');
const modelSelect = document.getElementById('modelSelect');

let lastBoxes = [];
let isDetecting = false;
let scaleX = 1,
    scaleY = 1;

// 🧠 Load models từ API
fetch('/api/auth/me')
    .then((res) => res.json())
    .then((user) => {
        const currentUserId = user.user_id || null;

        return fetch('/api/models/get_all')
            .then((res) => res.json())
            .then((data) => {
                if (data.models && data.models.length > 0) {
                    const modelsToShow =
                        currentUserId === null ? [data.models[0]] : data.models;

                    modelSelect.innerHTML = '';
                    modelsToShow.forEach((m) => {
                        const opt = document.createElement('option');
                        opt.value = m.model_id;
                        opt.textContent = m.model_name;
                        modelSelect.appendChild(opt);
                    });

                    modelSelect.value = modelsToShow[0].model_id;
                }
            });
    })
    .catch((err) => {
        console.error('Không load được mô hình:', err);
    });

function updateCanvasSize() {
    const rect = previewVideo.getBoundingClientRect();
    uploadCanvas.style.width = rect.width + 'px';
    uploadCanvas.style.height = rect.height + 'px';
    scaleX = rect.width / previewVideo.videoWidth;
    scaleY = rect.height / previewVideo.videoHeight;
}

window.addEventListener('resize', () => {
    if (!previewVideo.videoWidth) return;
    updateCanvasSize();
});

videoUpload.addEventListener('change', () => {
    const file = videoUpload.files[0];
    if (!file) return;

    previewVideo.src = URL.createObjectURL(file);
    detectBtn.disabled = false;
    fileNameSpan.textContent = file.name;
    previewVideo.style.display = 'block';

    previewVideo.addEventListener('loadedmetadata', () => {
        previewVideo.style.display = 'block';
        uploadCanvas.style.display = 'block';

        const maxHeight = 400;
        const aspectRatio = previewVideo.videoWidth / previewVideo.videoHeight;
        const displayHeight = Math.min(maxHeight, previewVideo.videoHeight);
        const displayWidth = displayHeight * aspectRatio;

        previewVideo.style.height = displayHeight + 'px';
        previewVideo.style.width = displayWidth + 'px';

        uploadCanvas.style.height = displayHeight + 'px';
        uploadCanvas.style.width = displayWidth + 'px';

        uploadCanvas.width = previewVideo.videoWidth;
        uploadCanvas.height = previewVideo.videoHeight;
    });
});

async function detectFrame(imageData) {
    const modelId = modelSelect.value || '1';

    try {
        const res = await fetch('/api/predict/detect_video_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: imageData,
                model_id: modelId,
            }),
        });
        const data = await res.json();
        lastBoxes = data.detections || [];
    } catch (err) {
        console.error('Detection error:', err);
    }
}

function drawLoop() {
    if (!isDetecting || previewVideo.ended) return;

    uploadCtx.clearRect(0, 0, uploadCanvas.width, uploadCanvas.height);

    lastBoxes.forEach(({ bbox, confidence }) => {
        const [x1, y1, x2, y2] = bbox;
        const label = `Fire (${(confidence * 100).toFixed(1)}%)`;

        const dx1 = x1 * scaleX;
        const dy1 = y1 * scaleY;
        const dw = (x2 - x1) * scaleX;
        const dh = (y2 - y1) * scaleY;

        uploadCtx.strokeStyle = 'blue';
        uploadCtx.lineWidth = 2;
        uploadCtx.strokeRect(dx1, dy1, dw, dh);
        uploadCtx.fillStyle = 'blue';
        uploadCtx.font = '16px sans-serif';
        uploadCtx.fillText(label, dx1 + 4, dy1 - 6);
    });

    const now = Date.now();
    //200ms gui 1 lan
    if (!drawLoop.lastDetectTime || now - drawLoop.lastDetectTime > 200) {
        drawLoop.lastDetectTime = now;
        if (!previewVideo.paused) {
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = previewVideo.videoWidth;
            tempCanvas.height = previewVideo.videoHeight;
            const tempCtx = tempCanvas.getContext('2d');
            tempCtx.drawImage(previewVideo, 0, 0);
            const base64Image = tempCanvas.toDataURL('image/jpeg');
            detectFrame(base64Image);
        }
    }

    requestAnimationFrame(drawLoop);
}

detectBtn.addEventListener('click', () => {
    if (previewVideo.src && !isDetecting) {
        isDetecting = true;
        previewVideo.play();
        drawLoop();
        detectBtn.disabled = true;
    }
});

previewVideo.addEventListener('pause', () => {
    isDetecting = false;
    detectBtn.disabled = false;
});

previewVideo.addEventListener('ended', () => {
    isDetecting = false;
    detectBtn.disabled = false;
});

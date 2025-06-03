/** @format */

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const statusEl = document.getElementById('status');

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
        });
        video.srcObject = stream;
        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        };
        statusEl.textContent = '📸 Camera đang hoạt động...';
    } catch (err) {
        console.error('Không thể mở camera:', err);
        statusEl.textContent = '❌ Không thể truy cập camera.';
    }
}

async function detectFrame(imageData) {
    try {
        const res = await fetch('/detect-frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData }),
        });
        const data = await res.json();
        drawBoxes(data.detections || []);
    } catch (err) {
        console.error('Detection error:', err);
    }
}

function drawBoxes(detections) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    detections.forEach(({ bbox, confidence }) => {
        const [x1, y1, x2, y2] = bbox;
        const label = `Fire (${(confidence * 100).toFixed(1)}%)`;
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        ctx.font = '16px sans-serif';
        ctx.fillStyle = 'red';
        ctx.fillText(label, x1 + 5, y1 - 8);
    });
}

function sendFrameLoop() {
    if (video.readyState === 4) {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = video.videoWidth;
        tempCanvas.height = video.videoHeight;
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.drawImage(video, 0, 0);
        const imageData = tempCanvas.toDataURL('image/jpeg');
        detectFrame(imageData);
    }
    requestAnimationFrame(sendFrameLoop);
}

window.addEventListener('load', async () => {
    await startCamera();
    sendFrameLoop();
});

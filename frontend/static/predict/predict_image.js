/** @format */

const imageUpload = document.getElementById('imageUpload');
const preview = document.getElementById('preview');
const uploadCanvas = document.getElementById('uploadCanvas');
const uploadCtx = uploadCanvas.getContext('2d');
const detectBtn = document.getElementById('detectBtn');
let selectedFile = null;

imageUpload.addEventListener('change', () => {
    const file = imageUpload.files[0];
    selectedFile = file;
    detectBtn.disabled = !file;

    if (!file) {
        preview.src = '';
        uploadCtx.clearRect(0, 0, uploadCanvas.width, uploadCanvas.height);
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        preview.src = e.target.result;
        preview.style.display = 'block';
        preview.onload = () => {
            uploadCanvas.width = preview.naturalWidth;
            uploadCanvas.height = preview.naturalHeight;
            uploadCanvas.style.width = preview.width + 'px';
            uploadCanvas.style.height = preview.height + 'px';

            uploadCtx.clearRect(0, 0, uploadCanvas.width, uploadCanvas.height);
            uploadCtx.drawImage(preview, 0, 0);
        };
    };
    reader.readAsDataURL(file);
});

detectBtn.addEventListener('click', () => {
    if (!selectedFile) return;

    uploadCtx.clearRect(0, 0, uploadCanvas.width, uploadCanvas.height);
    uploadCtx.drawImage(preview, 0, 0);

    uploadCanvas.toBlob((blob) => {
        const formData = new FormData();
        formData.append('file', blob, 'upload.jpg');

        fetch('/predict', {
            method: 'POST',
            body: formData,
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.detections && data.detections.length > 0) {
                    uploadCtx.strokeStyle = 'blue';
                    uploadCtx.lineWidth = 3;
                    uploadCtx.font = '27px Arial';
                    uploadCtx.fillStyle = 'blue';

                    data.detections.forEach((det) => {
                        const [x1, y1, x2, y2] = det.bbox;
                        const w = x2 - x1;
                        const h = y2 - y1;

                        uploadCtx.strokeRect(x1, y1, w, h);
                        const confText =
                            (det.confidence * 100).toFixed(1) + '%';
                        uploadCtx.fillText(
                            confText,
                            x1,
                            y1 > 20 ? y1 - 5 : y1 + 20
                        );
                    });
                    const hasHighConfidence = data.detections.some(
                        (det) => det.confidence > 0.3
                    );

                    Swal.fire({
                        toast: true,
                        position: 'top-end',
                        icon: hasHighConfidence ? 'success' : 'warning',
                        title: hasHighConfidence
                            ? '🔥 Phát hiện cháy!'
                            : '🚫 Không phát hiện cháy',
                        showConfirmButton: false,
                        timer: 3000,
                        timerProgressBar: true,
                    });
                }
            })
            .catch((err) => {
                console.error('Lỗi khi gửi ảnh upload:', err);
            });
    }, 'image/jpeg');
});

/** @format */

const imageUpload = document.getElementById('imageUpload');
const preview = document.getElementById('preview');
const uploadCanvas = document.getElementById('uploadCanvas');
const uploadCtx = uploadCanvas.getContext('2d');
const detectBtn = document.getElementById('detectBtn');
const modelSelect = document.getElementById('modelSelect');
let selectedFile = null;

// Load danh sách mô hình từ backend
fetch('/api/models/get_all')
    .then((res) => res.json())
    .then((data) => {
        if (data.models && data.models.length > 0) {
            data.models.forEach((m) => {
                const opt = document.createElement('option');
                opt.value = m.model_id;
                opt.textContent = m.model_name;
                modelSelect.appendChild(opt);
            });
            // ✅ Chọn mặc định model ID = 1 nếu tồn tại
            const hasDefaultModel = data.models.some((m) => m.model_id == 1);
            if (hasDefaultModel) {
                modelSelect.value = '1';
            }
        }
    })
    .catch((err) => {
        console.error('Lỗi khi lấy danh sách mô hình:', err);
    });

// Khi người dùng chọn ảnh
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

// Khi nhấn nút Detect
// Khi nhấn nút Detect
detectBtn.addEventListener('click', () => {
    if (!selectedFile) return;

    const selectedModelId = modelSelect.value;
    if (!selectedModelId) {
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'warning',
            title: '⚠️ Vui lòng chọn mô hình!',
            showConfirmButton: false,
            timer: 2500,
            timerProgressBar: true,
        });
        return;
    }

    uploadCtx.clearRect(0, 0, uploadCanvas.width, uploadCanvas.height);
    uploadCtx.drawImage(preview, 0, 0);

    Swal.fire({
        title: 'Đang xử lý...',
        text: 'Hệ thống đang dự đoán ảnh, vui lòng chờ.',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        },
    });

    uploadCanvas.toBlob((blob) => {
        const formData = new FormData();
        formData.append('file', blob, 'upload.jpg');
        formData.append('model_id', selectedModelId);

        fetch('/api/predict/detect_image', {
            method: 'POST',
            body: formData,
        })
            .then((res) => res.json())
            .then((data) => {
                Swal.close(); // ✅ Đóng loading

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
                } else {
                    Swal.fire({
                        toast: true,
                        position: 'top-end',
                        icon: 'info',
                        title: 'Không phát hiện đối tượng nào.',
                        showConfirmButton: false,
                        timer: 2500,
                        timerProgressBar: true,
                    });
                }
            })
            .catch((err) => {
                Swal.close(); // ✅ Đóng loading nếu lỗi
                console.error('Lỗi khi gửi ảnh upload:', err);
                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: 'error',
                    title: '❌ Lỗi khi gửi yêu cầu đến server!',
                    showConfirmButton: false,
                    timer: 3000,
                    timerProgressBar: true,
                });
            });
    }, 'image/jpeg');
});

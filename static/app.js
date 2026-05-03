// PDF Password Remover - Frontend Logic

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const passwordInput = document.getElementById('passwordInput');
const submitBtn = document.getElementById('submitBtn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');
const form = document.getElementById('uploadForm');
const resultSection = document.getElementById('resultSection');
const resultCard = document.getElementById('resultCard');

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
const MAX_FILES = 50;

let selectedFiles = [];

// ==== Drop Zone Events ====
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
    fileInput.value = ''; // reset เพื่อให้เลือกไฟล์เดิมซ้ำได้
});

function handleFiles(files) {
    const newFiles = Array.from(files).filter(f => {
        if (!f.name.toLowerCase().endsWith('.pdf')) {
            showResult('error', 'ไฟล์ไม่ถูกต้อง', `${f.name} ไม่ใช่ไฟล์ PDF`);
            return false;
        }
        if (f.size > MAX_FILE_SIZE) {
            showResult('error', 'ไฟล์ใหญ่เกินไป', `${f.name} มีขนาดเกิน 50 MB`);
            return false;
        }
        // ตรวจสอบไฟล์ซ้ำ (ชื่อ+ขนาด)
        if (selectedFiles.some(sf => sf.name === f.name && sf.size === f.size)) {
            return false;
        }
        return true;
    });

    selectedFiles = [...selectedFiles, ...newFiles].slice(0, MAX_FILES);
    if (selectedFiles.length === MAX_FILES && (selectedFiles.length + newFiles.length) > MAX_FILES) {
        showResult('error', 'จำนวนไฟล์เกิน', `เลือกได้สูงสุด ${MAX_FILES} ไฟล์`);
    }
    renderFileList();
    updateSubmitButton();
}

function renderFileList() {
    fileList.innerHTML = '';
    selectedFiles.forEach((file, idx) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span class="file-icon">📄</span>
            <span class="file-name"></span>
            <span class="file-size">${formatSize(file.size)}</span>
            <button type="button" class="file-remove" data-idx="${idx}" aria-label="ลบไฟล์">×</button>
        `;
        // ใส่ชื่อไฟล์ผ่าน textContent กัน XSS
        item.querySelector('.file-name').textContent = file.name;
        item.querySelector('.file-remove').addEventListener('click', () => removeFile(idx));
        fileList.appendChild(item);
    });
}

function removeFile(idx) {
    selectedFiles.splice(idx, 1);
    renderFileList();
    updateSubmitButton();
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function updateSubmitButton() {
    submitBtn.disabled = selectedFiles.length === 0 || !passwordInput.value.trim();
}

passwordInput.addEventListener('input', updateSubmitButton);

// ==== Form Submit ====
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) return;

    setLoading(true);
    hideResult();

    try {
        const formData = new FormData();
        selectedFiles.forEach(f => formData.append('files', f));
        formData.append('passwords', passwordInput.value);

        const response = await fetch('/api/unlock', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            let errorMsg = 'เกิดข้อผิดพลาด';
            try {
                const data = await response.json();
                errorMsg = data.detail || errorMsg;
            } catch {}
            throw new Error(errorMsg);
        }

        // ดึง filename จาก Content-Disposition
        const contentDisposition = response.headers.get('Content-Disposition') || '';
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        const filename = match ? match[1] : 'unlocked.pdf';

        const successCount = response.headers.get('X-Success-Count');
        const totalCount = response.headers.get('X-Total-Count');

        // Download ไฟล์
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // แสดงผลสำเร็จ
        const summary = (successCount && totalCount)
            ? `ดาวน์โหลด ${filename} เรียบร้อย (สำเร็จ ${successCount}/${totalCount} ไฟล์)`
            : `ดาวน์โหลด ${filename} เรียบร้อย`;
        showResult('success', '✅ สำเร็จ!', summary);

        // เคลียร์ไฟล์ที่เลือก
        selectedFiles = [];
        renderFileList();
        updateSubmitButton();

    } catch (err) {
        showResult('error', '❌ ลบ password ไม่สำเร็จ', err.message);
    } finally {
        setLoading(false);
    }
});

function setLoading(loading) {
    submitBtn.disabled = loading;
    btnText.hidden = loading;
    btnLoading.hidden = !loading;
}

function showResult(type, title, message) {
    resultCard.className = `result-card ${type}`;
    resultCard.innerHTML = '';
    const h3 = document.createElement('h3');
    h3.textContent = title;
    const p = document.createElement('p');
    p.textContent = message;
    resultCard.appendChild(h3);
    resultCard.appendChild(p);
    resultSection.hidden = false;
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideResult() {
    resultSection.hidden = true;
}

"""
PDF Password Remover - FastAPI Web Application
================================================
เว็บแอปสำหรับลบ password ออกจากไฟล์ PDF ผ่านเบราว์เซอร์
รองรับการอัปโหลดหลายไฟล์พร้อมกัน
"""

import io
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

# จำกัดขนาดไฟล์ที่อัปโหลดได้ (ต่อไฟล์) - 50 MB
MAX_FILE_SIZE = 50 * 1024 * 1024
# จำกัดจำนวนไฟล์ต่อครั้ง
MAX_FILES = 50

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="Lab Parfumo PDF Password Remover",
    description="ลบ password ออกจาก PDF หลายไฟล์พร้อมกันผ่านเว็บ",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def remove_pdf_password(pdf_bytes: bytes, passwords: list[str]) -> tuple[bool, bytes | None, str, str | None]:
    """
    ลบ password จาก PDF bytes

    Returns:
        (success, output_bytes, message, used_password)
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except PdfReadError as e:
        return False, None, f"อ่านไฟล์ PDF ไม่ได้: {e}", None
    except Exception as e:
        return False, None, f"เกิดข้อผิดพลาด: {e}", None

    used_password = None

    if reader.is_encrypted:
        # ลอง password ทีละตัว
        decrypted = False
        for pwd in passwords:
            try:
                if reader.decrypt(pwd) != 0:
                    decrypted = True
                    used_password = pwd
                    break
            except Exception:
                continue

        if not decrypted:
            return False, None, "password ไม่ถูกต้อง", None

    # เขียนไฟล์ใหม่โดยไม่ใส่ password
    try:
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)

        msg = "ลบ password สำเร็จ" if reader.is_encrypted else "ไฟล์ไม่มี password อยู่แล้ว"
        return True, output_buffer.getvalue(), msg, used_password
    except Exception as e:
        return False, None, f"เขียนไฟล์ไม่ได้: {e}", None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """หน้าหลักของเว็บแอป"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/unlock")
async def unlock_pdfs(
    files: list[UploadFile] = File(...),
    passwords: str = Form(...),
):
    """
    Endpoint สำหรับลบ password จาก PDF

    - files: รายการไฟล์ PDF ที่อัปโหลด
    - passwords: password (คั่นด้วย comma หากมีหลายตัว)

    Returns:
        - ถ้ามีไฟล์เดียว → ส่ง PDF กลับ
        - ถ้ามีหลายไฟล์ → ส่ง ZIP กลับ
    """
    if not files:
        raise HTTPException(status_code=400, detail="ไม่มีไฟล์ที่อัปโหลด")

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"อัปโหลดได้สูงสุด {MAX_FILES} ไฟล์ต่อครั้ง",
        )

    pwd_list = [p.strip() for p in passwords.split(",") if p.strip()]
    if not pwd_list:
        raise HTTPException(status_code=400, detail="ต้องระบุ password อย่างน้อย 1 ตัว")

    # ประมวลผลแต่ละไฟล์
    results = []
    for upload in files:
        # ตรวจสอบนามสกุล
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            results.append({
                "filename": upload.filename or "unknown",
                "success": False,
                "message": "ไม่ใช่ไฟล์ PDF",
                "data": None,
            })
            continue

        # อ่านไฟล์ และตรวจสอบขนาด
        content = await upload.read()
        if len(content) > MAX_FILE_SIZE:
            results.append({
                "filename": upload.filename,
                "success": False,
                "message": f"ไฟล์ใหญ่เกิน {MAX_FILE_SIZE // (1024 * 1024)} MB",
                "data": None,
            })
            continue

        # ลบ password
        success, output_bytes, msg, _ = remove_pdf_password(content, pwd_list)
        results.append({
            "filename": upload.filename,
            "success": success,
            "message": msg,
            "data": output_bytes,
        })

    successful = [r for r in results if r["success"]]

    # ถ้าทุกไฟล์ล้มเหลว → ส่ง error กลับ
    if not successful:
        error_summary = "; ".join(f"{r['filename']}: {r['message']}" for r in results)
        raise HTTPException(status_code=400, detail=f"ลบ password ไม่สำเร็จ ({error_summary})")

    # ถ้ามีไฟล์เดียวที่สำเร็จและไฟล์ทั้งหมดมีไฟล์เดียว → ส่ง PDF กลับ
    if len(results) == 1 and len(successful) == 1:
        r = successful[0]
        original_name = Path(r["filename"]).stem
        return StreamingResponse(
            io.BytesIO(r["data"]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{original_name}_unlocked.pdf"',
                "X-Process-Status": "success",
            },
        )

    # หลายไฟล์ → zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # เพิ่มไฟล์ที่สำเร็จ
        for r in successful:
            original_name = Path(r["filename"]).stem
            zf.writestr(f"{original_name}_unlocked.pdf", r["data"])

        # เพิ่มไฟล์สรุปผล
        report_lines = ["PDF Password Remover - Report", "=" * 40, ""]
        for r in results:
            status = "✓" if r["success"] else "✗"
            report_lines.append(f"{status} {r['filename']}: {r['message']}")
        report_lines.extend([
            "",
            f"สำเร็จ: {len(successful)}/{len(results)} ไฟล์",
        ])
        zf.writestr("_report.txt", "\n".join(report_lines).encode("utf-8"))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="unlocked_pdfs.zip"',
            "X-Process-Status": "success",
            "X-Success-Count": str(len(successful)),
            "X-Total-Count": str(len(results)),
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint สำหรับ deployment"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

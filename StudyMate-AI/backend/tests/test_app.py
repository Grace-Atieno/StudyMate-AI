import io
import pytest
import app as appmod


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(appmod, "generate_study_material",
                        lambda text, cfg: {"summary": "s", "quiz": [{"question": "q", "options": ["a", "b"], "answer": 0}]})
    a = appmod.create_app({"TESTING": True, "ALLOWED_ORIGINS": ["http://good.test"], "MAX_UPLOAD_MB": 1})
    return a.test_client()


def up(client, name, data, **kw):
    return client.post("/upload", data={"file": (io.BytesIO(data), name)}, content_type="multipart/form-data", **kw)


LONG = b"Photosynthesis converts light energy into chemical energy in plants. " * 3


def test_txt_ok(client):
    r = up(client, "n.txt", LONG)
    assert r.status_code == 200 and r.json["quiz"][0]["answer"] == 0


def test_no_file(client):
    assert client.post("/upload").status_code == 400


def test_bad_extension(client):
    assert up(client, "evil.exe", LONG).status_code == 400


def test_fake_pdf_rejected(client):
    assert up(client, "x.pdf", LONG).status_code == 400


def test_fake_docx_rejected(client):
    assert up(client, "x.docx", LONG).status_code == 400


def test_path_traversal_name_is_harmless(client):
    assert up(client, "../../etc/passwd.txt", LONG).status_code == 200  # nothing is written to disk


def test_too_large(client):
    assert up(client, "big.txt", b"a" * (2 * 1024 * 1024)).status_code == 413


def test_too_little_text(client):
    assert up(client, "n.txt", b"hi").status_code == 422


def test_cors_only_for_allowed_origin(client):
    ok = client.get("/health", headers={"Origin": "http://good.test"})
    bad = client.get("/health", headers={"Origin": "http://evil.test"})
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://good.test"
    assert "Access-Control-Allow-Origin" not in bad.headers


def test_security_headers(client):
    h = client.get("/health").headers
    assert h["X-Content-Type-Options"] == "nosniff" and "frame-ancestors" in h["Content-Security-Policy"]


def test_rate_limit(client):
    codes = [up(client, "n.txt", LONG).status_code for _ in range(12)]
    assert 429 in codes


def test_missing_key_fails_closed():
    with pytest.raises(appmod.ConfigError):
        appmod.create_app({"GEMINI_API_KEY": ""})


def test_ai_output_validation():
    out = appmod.validate_ai_output({"summary": " hi ", "quiz": [{"question": "q", "options": ["a", "b"], "answer": 5},
                                                                  {"question": "q2", "options": ["a", "b"], "answer": 1}]})
    assert len(out["quiz"]) == 1 and out["summary"] == "hi"
    with pytest.raises(Exception):
        appmod.validate_ai_output({"summary": "", "quiz": []})


def test_real_pdf_and_docx_extract():
    import pymupdf
    from docx import Document
    pdf = pymupdf.open(); pdf.new_page().insert_text((72, 72), "Mitochondria produce ATP for the cell."); pdf_bytes = pdf.tobytes()
    assert "Mitochondria" in appmod.extract_text(pdf_bytes, "pdf")
    buf = io.BytesIO(); d = Document(); d.add_paragraph("Newton's second law: F = ma."); d.save(buf)
    assert "Newton" in appmod.extract_text(buf.getvalue(), "docx")

import io
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

def test_home_route(client):
    """Test homepage (ar trebui să răspundă 404 sau să fie setată o rută)."""
    response = client.get("/")
    assert response.status_code in (200, 404)

def test_upload_valid_pdf(client):
    """Test upload cu un fișier PDF valid."""
    data = {
        "job_description": "Backend Python developer"
    }
    # simulăm un PDF (în loc de fișier real, doar conținut binar dummy)
    fake_pdf = (io.BytesIO(b"%PDF-1.4 fake pdf content"), "cv.pdf")
    response = client.post(
        "/upload",
        data={"file": fake_pdf, "job_description": data["job_description"]},
        content_type="multipart/form-data"
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert "score" in json_data
    assert 0 <= json_data["score"] <= 100

def test_upload_valid_docx(client):
    """Test upload cu un fișier DOCX valid."""
    data = {
        "job_description": "Data Analyst"
    }
    fake_docx = (io.BytesIO(b"PK\x03\x04 fake docx content"), "cv.docx")
    response = client.post(
        "/upload",
        data={"file": fake_docx, "job_description": data["job_description"]},
        content_type="multipart/form-data"
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert "score" in json_data

def test_upload_missing_file(client):
    """Test caz când nu se trimite niciun fișier."""
    response = client.post(
        "/upload",
        data={"job_description": "Frontend developer"}
    )
    assert response.status_code == 400

def test_upload_invalid_file_type(client):
    """Test caz cu fișier neacceptat (ex. TXT)."""
    data = {
        "job_description": "Tester QA"
    }
    fake_txt = (io.BytesIO(b"just some text"), "cv.txt")
    response = client.post(
        "/upload",
        data={"file": fake_txt, "job_description": data["job_description"]},
        content_type="multipart/form-data"
    )
    assert response.status_code == 400

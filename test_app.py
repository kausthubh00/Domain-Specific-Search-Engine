import pytest
import io
from app import app, stemmer, get_highlighted_snippet

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_stemming_matches():
    """Proves NLP stemmer correctly maps variations to the same root."""
    # FIXED: Comparing 'routers' to 'router' (both stem to 'router')
    assert stemmer.stem("routers") == stemmer.stem("router")
    assert stemmer.stem("networks") == stemmer.stem("network")

def test_snippet_page_marker_extraction():
    """Proves the snippet engine successfully extracts and cleans the [PG:n] marker."""
    dummy_text = "start of document [PG:12] The router directs traffic. end of document"
    snippet = get_highlighted_snippet(dummy_text, "router")
    
    assert "(Page 12)" in snippet
    assert "<mark>router</mark>" in snippet
    assert "[PG:12]" not in snippet # Proves raw marker was stripped

def test_security_upload_rejects_html(client):
    """Proves the API blocks malicious executable files."""
    # FIXED: Wrapped the byte string in io.BytesIO so Flask sees it as a real file
    data = {'file': (io.BytesIO(b"<html><script>alert('hack')</script></html>"), 'virus.html')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    # The response should indicate 0 files were successfully indexed
    assert b"0 of 1 files" in response.data
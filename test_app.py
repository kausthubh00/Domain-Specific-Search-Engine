import io
import pytest
from app import app, stemmer, get_highlighted_snippet


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_stemming_matches():
    """Proves the NLP stemmer maps variations to the same root."""
    assert stemmer.stem("routers") == stemmer.stem("router")
    assert stemmer.stem("networks") == stemmer.stem("network")


def test_snippet_page_marker_extraction():
    """Proves the snippet engine extracts and cleans the [PG:n] marker."""
    dummy_text = "start of document [PG:12] the router directs traffic. end of document"
    snippet = get_highlighted_snippet(dummy_text, "router")

    assert "(Page 12)" in snippet
    assert "<mark>router</mark>" in snippet
    assert "[PG:12]" not in snippet  # the raw marker was stripped


def test_security_upload_rejects_html(client):
    """Proves the API blocks files that are not pdf/docx/txt."""
    data = {'file': (io.BytesIO(b"<html><script>alert('hack')</script></html>"), 'virus.html')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')

    # No file should have been indexed
    assert b"0 of 1 files" in response.data


def test_ranking_logic(client):
    """BM25 puts a routing-heavy document first for the query 'routing'."""
    response = client.get('/api/search?q=routing')
    assert response.status_code == 200

    results = response.get_json()
    assert results, "search returned nothing"
    assert results[0]['path'] in ("unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf")

    scores = [float(r['score'].split("BM25: ")[1].split(" |")[0]) for r in results]
    assert scores == sorted(scores, reverse=True)
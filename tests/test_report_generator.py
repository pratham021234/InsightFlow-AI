import pytest
import io
from services.report_generator import (
    build_report_data,
    generate_html_report,
    generate_pdf_report,
    generate_docx_report
)

@pytest.fixture
def sample_report_data():
    return {
        "dataset_type": "Sales",
        "rows": 100,
        "columns": 5,
        "executive_summary": "Test Executive Summary for validation.",
        "kpis": [
            {"name": "Total Revenue", "value": "$50,000", "description": "Sum of all sales"}
        ],
        "insights": [
            {"title": "Core Finding", "description": "High performance in primary segment."}
        ],
        "risks": [
            {"title": "Concentration Risk", "description": "Top client accounts for 40% of revenue.", "priority": "High"}
        ],
        "recommendations": [
            {"title": "Expand Offering", "description": "Target secondary markets."}
        ],
        "chat_history": [
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Revenue is $50,000."}
        ]
    }

@pytest.fixture
def branding():
    return {
        "title": "Quarterly Business Review",
        "company": "Acme Holdings",
        "analyst": "Senior QA Engineer"
    }

def test_generate_html_report(sample_report_data, branding):
    html = generate_html_report(sample_report_data, branding)
    assert "<!DOCTYPE html>" in html
    assert "Quarterly Business Review" in html
    assert "Acme Holdings" in html
    assert "$50,000" in html

def test_generate_pdf_report(sample_report_data, branding):
    pdf_buffer = generate_pdf_report(sample_report_data, branding)
    assert isinstance(pdf_buffer, io.BytesIO)
    content = pdf_buffer.getvalue()
    assert len(content) > 1000
    assert content.startswith(b"%PDF")

def test_generate_docx_report(sample_report_data, branding):
    docx_buffer = generate_docx_report(sample_report_data, branding)
    assert isinstance(docx_buffer, io.BytesIO)
    content = docx_buffer.getvalue()
    assert len(content) > 1000
    # DOCX is a zip file, starts with PK
    assert content.startswith(b"PK")


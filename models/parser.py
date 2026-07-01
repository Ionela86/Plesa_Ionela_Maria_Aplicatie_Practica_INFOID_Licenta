import os
from pdfminer.high_level import extract_text as extract_pdf
from docx import Document

def extract_text_from_file(path):
    if path.endswith('.pdf'):
        return extract_pdf(path)
    elif path.endswith('.docx'):
        doc = Document(path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file format")

import spacy
import re

nlp = spacy.load("en_core_web_sm")

def analyze_cv(text):
    report = {}
    
    # 1. Email
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}"
    report['has_email'] = bool(re.search(email_pattern, text))
    
    # 2. Telefon
    phone_pattern = r"\+?\d[\d -]{7,}\d"
    report['has_phone'] = bool(re.search(phone_pattern, text))
    
    # 3. Experiență (keywords exemplu)
    keywords = ["Python", "React", "Flask", "Machine Learning"]
    report['skills_found'] = [kw for kw in keywords if kw.lower() in text.lower()]
    
    # 4. Educație (keywords exemplu)
    education_keywords = ["Bachelor", "Master", "University", "Faculty"]
    report['education_found'] = [kw for kw in education_keywords if kw.lower() in text.lower()]
    
    # 5. Lungime CV
    report['length_ok'] = len(text.split()) >= 100  # minim 100 cuvinte
    
    # 6. Verificare gramaticală (număr de propoziții)
    doc = nlp(text)
    report['sentence_count'] = len(list(doc.sents))
    
    return report

import base64
import os
import re
import threading
from datetime import datetime
from html import escape as html_escape

import pdfplumber
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

import webbrowser

try:
    import fitz  
except Exception:
    fitz = None

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except Exception:
    nlp = None

from models.ai_model import generate_cv_opinion, generate_recruitment_suggestion, generate_summary, semantic_match
from models.parser import extract_text_from_file
from utils.skills import extract_skills

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_base64_logo():
    logo_path = os.path.join(BASE_DIR, "logo.png")
    try:
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return ""


def simple_keywords(text):
    words = re.findall(r"[a-zăâîșşțţ0-9+#.]+", (text or "").lower())
    stop = {"and", "or", "the", "for", "with", "din", "si", "și", "la", "de", "cu", "in", "în", "un", "o", "a", "ale", "al", "pe"}
    return [w for w in words if len(w) > 2 and w not in stop]


def lemmas(text):
    if nlp is not None:
        try:
            doc = nlp(text or "")
            return [t.lemma_.lower() for t in doc if t.is_alpha and not t.is_stop]
        except Exception:
            pass
    return simple_keywords(text)


def extract_years_experience(text):
    text = text or ""
    current_year = datetime.now().year
    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", text)]
    plausible = [y for y in years if 1970 <= y <= current_year]
    by_dates = current_year - min(plausible) if plausible else 0

    explicit = [int(x) for x in re.findall(r"\b(\d{1,2})\s*(?:\+)?\s*(?:ani|years?)\b", text.lower())]
    by_explicit = max(explicit) if explicit else 0
    return max(by_dates, by_explicit)


def extract_text_safely(path):
    ext = path.rsplit(".", 1)[-1].lower()
    try:
        if ext == "pdf":
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        if ext in {"docx", "txt"}:
            return extract_text_from_file(path) if ext == "docx" else open(path, encoding="utf-8", errors="ignore").read()
    except Exception as exc:
        raise ValueError(f"Nu s-a putut citi fișierul: {exc}")
    raise ValueError("Format neacceptat.")


def analyze_candidate(file_storage, job_title="", min_y=0, context_q=""):
    if not file_storage or not file_storage.filename:
        raise ValueError("Nu a fost trimis niciun fișier.")
    if not allowed_file(file_storage.filename):
        raise ValueError("Format neacceptat. Încarcă PDF, DOCX sau TXT.")

    clean_name = secure_filename(file_storage.filename) or "cv.pdf"
    clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean_name)
    f_path = os.path.join(UPLOAD_FOLDER, clean_name)
    file_storage.save(f_path)

    raw_text = extract_text_safely(f_path)
    text = raw_text.lower()
    job_title = (job_title or "").lower().strip()
    context_q = (context_q or "").lower().strip()


    if not context_q:
        raise ValueError("Introdu cerintele postului inainte de a lansa analiza AI.")

    job_text = " ".join(x for x in [job_title, context_q] if x)

    intro_text = text[:900]
    job_keywords = lemmas(job_title)
    title_match = int((len([kw for kw in job_keywords if kw in intro_text]) / len(job_keywords)) * 100) if job_keywords else 0

    actual_exp = extract_years_experience(text)
    cv_terms = set(lemmas(text))
    req_terms = set(lemmas(context_q))
    keyword_match = (len(req_terms & cv_terms) / len(req_terms) * 100) if req_terms else 0
    ai_score = semantic_match(job_text, text) if job_text else 0

    exp_score = 20 if actual_exp >= min_y else ((actual_exp / min_y) * 20 if min_y > 0 else 20)
    score = (title_match * 0.25) + (keyword_match * 0.25) + (ai_score * 0.30) + exp_score

    if actual_exp >= 15:
        score = max(score, 86)
        label = "Expert / Senior++"
    elif actual_exp >= 7:
        label = "Senior"
    elif actual_exp >= 3:
        label = "Middle"
    else:
        label = "Junior"

    if job_title and title_match < 10 and ai_score < 25 and actual_exp < 15:
        score *= 0.55

    score = int(min(max(score, 0), 100))
    skills = extract_skills(text)

    return {
        "name": file_storage.filename,
        "filename": clean_name,
        "score": score,
        "ai_score": int(ai_score),
        "title_match": int(title_match),
        "keyword_match": int(keyword_match),
        "years": int(actual_exp),
        "seniority_level": label,
        "skills": skills[:12],
        "summary": generate_cv_opinion(raw_text, score, job_text, skills),
        "recruitment_suggestion": generate_recruitment_suggestion(score, actual_exp, min_y, title_match, keyword_match, ai_score, job_title, context_q, skills),
        "decision": "RECOMANDAT" if score >= 50 else "DE REVIZUIT" if score >= 30 else "REJECTAT",
    }


@app.route("/")
def home():
    logo_b64 = get_base64_logo()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:100px; margin-bottom:15px;">' if logo_b64 else ""
    return f"""
    <!DOCTYPE html>
    <html lang="ro">
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{ --bg:#070b14; --panel:#111827; --accent:#38bdf8; --text:#f8fafc; --border:#1f2937; --card-bg:#1e293b; --success:#10b981; --danger:#ef4444; }}
            body {{ font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); margin:0; padding:20px; }}
            .container {{ max-width:1100px; margin:auto; background:var(--panel); padding:40px; border-radius:24px; border:1px solid var(--border); box-shadow:0 25px 50px rgba(0,0,0,.6); }}
            .header {{ text-align:center; margin-bottom:30px; }} h1 {{ color:var(--accent); font-weight:800; font-size:1.6rem; text-transform:uppercase; }}
            .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }} .full {{ grid-column:span 2; }}
            label {{ font-size:.75rem; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-bottom:8px; display:block; }}
            input,textarea {{ width:100%; padding:12px; border-radius:12px; border:1px solid var(--border); background:#0f172a; color:white; box-sizing:border-box; outline:none; }}
            .actions {{ display:flex; gap:15px; margin-top:30px; align-items:center; flex-wrap:wrap; }}
            .btn {{ padding:16px 28px; border-radius:14px; border:none; font-weight:800; cursor:pointer; text-transform:uppercase; font-size:.85rem; transition:.3s; }}
            .btn-upload {{ background:#334155; color:white; }} .btn-analyze {{ background:var(--accent); color:#070b14; flex-grow:1; }} .btn-reset {{ background:#b91c1c; color:white; }}
            .card {{ background:var(--card-bg); border-radius:20px; padding:25px; margin-top:20px; border:1px solid rgba(255,255,255,.05); transition:.4s; }}
            .card.accepted {{ border:2px solid var(--success); background:#064e3b; opacity:1; }} .card.rejected {{ border:2px solid var(--danger); opacity:.55; filter:grayscale(.5); }}
            .score-val {{ font-size:2.8rem; font-weight:900; color:var(--accent); }} .badge {{ background:rgba(56,189,248,.1); color:var(--accent); padding:6px 12px; border-radius:8px; font-size:.75rem; font-weight:600; margin:4px 5px 4px 0; display:inline-block; }}
            .summary {{ color:#cbd5e1; line-height:1.45; max-width:720px; margin-top:12px; }} .decision-btns {{ display:flex; gap:10px; margin-top:20px; }}
            .btn-check {{ background:var(--success); color:white; padding:10px 15px; font-size:.7rem; }} .btn-cross {{ background:var(--danger); color:white; padding:10px 15px; font-size:.7rem; }}
            .modal {{ display:none; position:fixed; z-index:1000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,.9); }} .modal-content {{ position:relative; margin:2% auto; width:90%; height:92%; background:#fff; border-radius:15px; overflow:hidden; }} .close-modal {{ position:absolute; right:20px; top:10px; font-size:30px; cursor:pointer; color:#000; z-index:1001; }}
        </style>
    </head>
    <body>
        <div id="pdfModal" class="modal"><div class="modal-content"><span class="close-modal" onclick="closePreview()">&times;</span><iframe id="pdfFrame" src="" width="100%" height="100%" style="border:none;"></iframe></div></div>
        <div class="container">
            <div class="header">{logo_html}<h1>SMART RECRUT – SISTEM INTELIGENT PENTRU OPTIMIZAREA PROCESULUI DE RECRUTARE</h1></div>
            <div class="grid">
                <div><label>Titlu Poziție Căutat:</label><input type="text" id="titlu" placeholder="ex: Economist, Inginer, Programator"></div>
                <div><label>Experiență Minimă (Ani):</label><input type="number" id="minY" value="0"></div>
                <div class="full"><label>Descrierea Rolului:</label><textarea id="desc" style="height:60px"></textarea></div>
                <div class="full"><label>Responsabilități Principale:</label><textarea id="resp" style="height:60px"></textarea></div>
                <div class="full"><label>Cerințe și Competențe Cheie:</label><textarea id="comp" style="height:60px"></textarea></div>
            </div>
            <div class="actions">
                <button class="btn btn-upload" onclick="document.getElementById('f').click()">Încarcă CV-uri</button>
                <input type="file" id="f" multiple accept=".pdf,.docx,.txt" style="display:none" onchange="showCount()">
                <div id="fileCount" style="font-weight:bold; color:var(--accent);"></div>
                <button class="btn btn-analyze" onclick="startAnalysis()">Lansează Analiza AI</button>
                <button class="btn btn-reset" onclick="location.reload()">Reset</button>
            </div><div id="results"></div>
        </div>
        <script>
            function showCount() {{ const input=document.getElementById('f'); document.getElementById('fileCount').innerHTML=input.files.length>0?'Ai pregătit '+input.files.length+' CV-uri.':''; }}
            function openPreview(url) {{ document.getElementById('pdfFrame').src=url; document.getElementById('pdfModal').style.display='block'; }}
            function closePreview() {{ document.getElementById('pdfModal').style.display='none'; document.getElementById('pdfFrame').src=''; }}
            function setDecision(btn,status,cardId) {{ const card=document.getElementById(cardId); card.classList.remove('accepted','rejected'); if(status==='accept') card.classList.add('accepted'); if(status==='reject') card.classList.add('rejected'); }}
            function esc(s) {{ return String(s ?? '').replace(/[&<>'"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}}[c])); }}
            async function startAnalysis() {{
                const files=Array.from(document.getElementById('f').files); const resultsDiv=document.getElementById('results'); if(files.length===0) return alert('Selectați CV-uri!');
                const jobRequirements=(document.getElementById('desc').value+' '+document.getElementById('resp').value+' '+document.getElementById('comp').value).trim();
                if(jobRequirements.length===0) return alert('Introduceți cerințele postului înainte de a lansa analiza AI.');
                resultsDiv.innerHTML='<p style="text-align:center;">Procesăm CV-urile cu AI local...</p>';
                for(let i=0;i<files.length;i++) {{
                    const fileObj=files[i], cardId='card_'+i, fd=new FormData(); fd.append('file',fileObj); fd.append('title',document.getElementById('titlu').value); fd.append('minY',document.getElementById('minY').value); fd.append('context', jobRequirements);
                    const res=await fetch('/analyze',{{method:'POST',body:fd}}).then(r=>r.json()).catch(e=>({{error:e.message}})); if(resultsDiv.innerHTML.includes('Procesăm')) resultsDiv.innerHTML='';
                    if(res.error) {{ resultsDiv.innerHTML += `<div class="card"><h2>Eroare la ${{esc(fileObj.name)}}</h2><p class="summary">${{esc(res.error)}}</p></div>`; continue; }}
                    const color=res.score>=50?'#10b981':(res.score>=30?'#f59e0b':'#ef4444'); const skills=(res.skills||[]).map(s=>`<span class="badge">${{esc(s)}}</span>`).join('');
                    resultsDiv.innerHTML += `<div class="card" id="${{cardId}}"><div style="display:flex; justify-content:space-between; gap:20px; align-items:flex-start;"><div><h2 style="margin:0;color:white;">${{esc(res.name)}}</h2><button class="btn" style="padding:8px 15px; font-size:.7rem; background:#475569; color:white; margin-top:10px; margin-bottom:10px;" onclick="openPreview('/preview_cv/'+encodeURIComponent('${{esc(res.filename)}}'))">👁️ VIZUALIZARE RAPIDĂ</button><div><span class="badge">🤖 AI semantic: ${{res.ai_score}}%</span><span class="badge">⌛ Vechime: ${{res.years}} ani</span><span class="badge">🎯 Match titlu: ${{res.title_match}}%</span><span class="badge">🔎 Cuvinte cheie: ${{res.keyword_match}}%</span><span class="badge">💼 ${{esc(res.seniority_level)}}</span></div><div style="margin-top:8px;">${{skills}}</div><p class="summary"><b>Rezumat CV:</b> ${{esc(res.summary)}}</p><p class="summary"><b>Sugestie recrutare:</b> ${{esc(res.recruitment_suggestion)}}</p><div class="decision-btns"><button class="btn btn-check" onclick="setDecision(this,'accept','${{cardId}}')">✅ PENTRU INTERVIU</button><button class="btn btn-cross" onclick="setDecision(this,'reject','${{cardId}}')">❌ REFUZ</button></div></div><div style="text-align:right;"><div class="score-val">${{res.score}}%</div><div style="color:${{color}}; font-weight:800; text-transform:uppercase;">${{esc(res.decision)}}</div></div></div></div>`;
                }}
            }}
        </script>
    </body></html>"""


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        min_y = int(request.form.get("minY", 0) or 0)
        return jsonify(analyze_candidate(request.files.get("file"), request.form.get("title", ""), min_y, request.form.get("context", "")))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/upload", methods=["POST"])
def upload():
    try:
        min_y = int(request.form.get("minY", 0) or 0)
        job_description = request.form.get("job_description", "")
        return jsonify(analyze_candidate(request.files.get("file"), request.form.get("title", ""), min_y, job_description))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/file_cv/<path:filename>")
def file_cv(filename):
    # Servește fișierul inline, nu ca atașament, ca PDF-ul să se vadă direct în fereastra aplicației.
    response = send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)
    response.headers["Content-Disposition"] = f"inline; filename={filename}"
    return response


@app.route("/preview_pdf_page/<path:filename>/<int:page_index>")
def preview_pdf_page(filename, page_index):
    safe_name = secure_filename(filename)
    path = os.path.join(UPLOAD_FOLDER, safe_name)
    if not os.path.exists(path):
        return "Fișierul nu a fost găsit.", 404
    if fitz is None:
        return "PyMuPDF nu este instalat. Rulează: pip install PyMuPDF", 500

    cache_dir = os.path.join(UPLOAD_FOLDER, "_preview_cache", safe_name)
    os.makedirs(cache_dir, exist_ok=True)
    img_path = os.path.join(cache_dir, f"page_{page_index + 1}.png")

    if not os.path.exists(img_path):
        doc = fitz.open(path)
        try:
            if page_index < 0 or page_index >= doc.page_count:
                return "Pagina nu există.", 404
            page = doc.load_page(page_index)
          
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pix.save(img_path)
        finally:
            doc.close()

    return send_file(img_path, mimetype="image/png")


@app.route("/preview_cv/<path:filename>")
def preview_cv(filename):
    safe_name = secure_filename(filename)
    path = os.path.join(UPLOAD_FOLDER, safe_name)
    if not os.path.exists(path):
        return "Fișierul nu a fost găsit.", 404

    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""


    if ext == "pdf" and fitz is not None:
        try:
            doc = fitz.open(path)
            page_count = doc.page_count
            doc.close()
        except Exception as exc:
            return f"Nu pot afișa PDF-ul: {html_escape(str(exc))}", 500

        pages = "\n".join(
            f'<img class="pdf-page" src="/preview_pdf_page/{html_escape(safe_name)}/{i}" alt="Pagina {i + 1}">'
            for i in range(page_count)
        )
        return f"""
        <!doctype html><html><head><meta charset='utf-8'>
        <style>
          html, body{{margin:0; min-height:100%; background:#e5e7eb; color:#0f172a; font-family:Arial, sans-serif;}}
          .top{{position:sticky; top:0; z-index:10; background:#0f172a; color:white; padding:12px 20px; font-weight:700; box-shadow:0 2px 10px rgba(0,0,0,.2);}}
          .hint{{font-size:12px; color:#cbd5e1; font-weight:400; margin-top:4px;}}
          .viewer{{padding:28px 12px 45px;}}
          .pdf-page{{display:block; width:min(96%, 1050px); height:auto; margin:0 auto 24px; background:white; box-shadow:0 12px 32px rgba(15,23,42,.22); border-radius:4px;}}
        </style></head><body>
          <div class='top'>Vizualizare CV: {html_escape(safe_name)}<div class='hint'>PDF-ul este afișat în format original, ca imagine. Poți face scroll sus/jos fără descărcare.</div></div>
          <div class='viewer'>{pages}</div>
        </body></html>
        """

   
    try:
        text = extract_text_safely(path)
    except Exception as exc:
        text = f"Nu pot afișa previzualizarea: {exc}"

    text = html_escape(text or "Nu s-a putut extrage text din fișier.")
    return f"""
    <!doctype html><html><head><meta charset='utf-8'>
    <style>
      html, body{{margin:0; height:100%; background:#e5e7eb; color:#0f172a; font-family:Arial, sans-serif;}}
      .top{{position:sticky; top:0; z-index:10; background:#0f172a; color:white; padding:12px 20px; font-weight:700; box-shadow:0 2px 10px rgba(0,0,0,.2);}}
      .page{{max-width:900px; min-height:92vh; margin:24px auto; background:white; border:1px solid #cbd5e1; box-shadow:0 15px 35px rgba(15,23,42,.18); padding:38px 46px; border-radius:8px;}}
      pre{{white-space:pre-wrap; word-wrap:break-word; line-height:1.55; font-size:14px; margin:0;}}
      .hint{{font-size:12px; color:#cbd5e1; font-weight:400; margin-top:4px;}}
    </style></head><body>
      <div class='top'>Vizualizare CV: {html_escape(safe_name)}<div class='hint'>Scroll sus/jos pentru citirea rapidă a conținutului. Nu se descarcă fișierul.</div></div>
      <div class='page'><pre>{text}</pre></div>
    </body></html>
    """


if __name__ == "__main__":

    url = "http://127.0.0.1:5000"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=5000, debug=False)

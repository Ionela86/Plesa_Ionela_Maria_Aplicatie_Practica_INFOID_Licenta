# Integrare AI gratuită în SMART-RECRUT

Am integrat AI local/gratuit, fără API plătit și fără chei externe.

Ce face:
- calculează scor semantic între cerințele jobului și CV (`ai_score`);
- generează rezumat AI pentru CV;
- combină scorul AI cu titlul, competențele și vechimea;
- are fallback offline/rapid dacă modelele `sentence-transformers` sau `transformers` nu sunt instalate;
- acceptă PDF, DOCX și TXT;
- corectează ruta `/upload` folosită în teste și păstrează `/analyze` pentru interfață;
- corectează calea logo-ului, importurile AI și pornirea fără `pywebview`.

Rulare:
```bash
pip install -r requirements.txt
python app.py
```

Prima rulare cu modelele AI complete poate descărca modele gratuite open-source. Dacă nu sunt disponibile, aplicația funcționează cu fallback local.

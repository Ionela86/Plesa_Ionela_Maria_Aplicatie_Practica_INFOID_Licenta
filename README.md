Autor: Plesa Ionela Maria
Denumirea proiectului
SMART-RECRUT -- SISTEM INTELIGENT PENTRU OPTIMIZAREA PROCESULUI DE RECRUTARE 
Descriere
SMART-RECRUT este o aplicatie dezvoltata in Python, cu interfata
web/desktop, care permite incarcarea si analiza CV-urilor. Aplicatia
extrage informatii relevante din CV si evalueaza compatibilitatea
candidatului cu cerintele unui post utilizand tehnici de inteligenta
artificiala si procesare a limbajului natural.

Repository-ul contine: - codul sursa al aplicatiei; - fisierele Python
necesare rularii; - fisierele pentru interfata aplicatiei; - fisierele
de configurare; - fisierul `requirements.txt` cu dependintele
necesare; - scripturi pentru rulare si compilare locala.
Repository-ul nu contine fisiere binare compilate (executabile,
folderele `build/` si `dist/`, fisiere temporare sau cache).
Tehnologii utilizate
Python
Flask
Flask-CORS
PyWebView
spaCy
pdfplumber
HTML
CSS
JavaScript
PyInstaller
Cerinte software
Windows
Python 3.10 sau versiune mai noua
pip
Git
Instalare
Clonarea repository-ului:
``` bash
git clone https://github.com/Ionela86/Plesa_Ionela_Maria_Aplicatie_Practica_INFOID_Licenta.git
```
Accesarea directorului proiectului:
``` bash
cd Plesa_Ionela_Maria_Aplicatie_Practica_INFOID_Licenta
```
Instalarea dependintelor:
``` bash
pip install -r requirements.txt
```
Lansarea aplicatiei
Din linia de comanda:
``` bash
python app.py
```
sau, pentru varianta desktop:
``` bash
python app_desktop.py
```
Alternativ:
``` text
RUN_SMART_RECRUT.bat
```
Compilarea aplicatiei
Executati:
``` text
BUILD_APP_EXE_LOCAL.bat
```
sau:
``` bash
pyinstaller app.spec
```
Executabilul va fi generat local in folderul `dist/`.
Functionalitati principale
Incarcarea CV-urilor in format PDF;
Vizualizarea CV-urilor;
Extragerea automata a informatiilor relevante;
Analiza CV-urilor cu ajutorul inteligentei artificiale;
Compararea CV-ului cu cerintele unui post;
Evaluarea compatibilitatii candidatului;
Generarea unui raport al analizei.

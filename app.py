import os, re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PyPDF2 import PdfReader
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

nltk_packages = ["stopwords", "punkt"]
for pkg in nltk_packages:
    try:
        nltk.data.find(f"corpora/{pkg}")
    except:
        nltk.download(pkg)

STOP_PT = set(stopwords.words('portuguese'))
STOP_EN = set(stopwords.words('english'))
stem_pt = SnowballStemmer('portuguese')
stem_en = SnowballStemmer('english')

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_DIR = "trained_model"
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval() 

def classify_email(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1).squeeze().tolist()

    if isinstance(probs, float):
        probs = [1 - probs, probs]
    label = "Produtivo" if probs[1] > probs[0] else "Improdutivo"
    confidence = max(probs)
    return label, confidence

def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(file_stream)
        text = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(text)
    except:
        return ""

def preprocess_text(text):
    t = text.lower()
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\S+@\S+', ' ', t)  # emails
    t = re.sub(r'http\S+', ' ', t)  # links
    tokens = re.findall(r'\b\w+\b', t, flags=re.UNICODE)
    lang = "pt" if sum(1 for w in STOP_PT if w in t) >= sum(1 for w in STOP_EN if w in t) else "en"
    stops = STOP_PT if lang == 'pt' else STOP_EN
    stemmer = stem_pt if lang == 'pt' else stem_en
    tokens = [stemmer.stem(tok) for tok in tokens if tok not in stops and len(tok) > 1]
    return " ".join(tokens), lang

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    email_text = None
    if 'file' in request.files and request.files['file'].filename != '':
        f = request.files['file']
        name = f.filename.lower()
        if name.endswith('.pdf'):
            email_text = extract_text_from_pdf(f.stream)
        elif name.endswith('.txt'):
            email_text = f.read().decode('utf-8', errors='ignore')
        else:
            return jsonify({"error":"Formato não suportado"}), 400
    if not email_text:
        email_text = request.form.get('email_text','').strip()
    if not email_text:
        return jsonify({"error":"Nenhum texto fornecido"}), 400

    preproc, lang = preprocess_text(email_text)

    cat, conf = classify_email(email_text)

    if cat == "Produtivo":
        suggested = (
            "Olá,\n\nRecebemos sua mensagem e já estamos verificando. "
            "Por favor, envie mais detalhes (nº do caso, prints ou arquivos) se possível, "
            "para agilizar o atendimento.\n\nAtenciosamente,\nEquipe de Suporte"
        )
    else:
        suggested = (
            "Olá,\n\nAgradecemos sua mensagem! No momento não é necessária nenhuma ação. "
            "Se precisar de algo específico, estamos à disposição.\n\nAtenciosamente,\nEquipe"
        )

    return jsonify({"category": cat, "confidence": conf, "suggested_reply": suggested})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

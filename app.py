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

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

STOP_PT = set(stopwords.words('portuguese'))
STOP_EN = set(stopwords.words('english'))
stem_pt = SnowballStemmer('portuguese')
stem_en = SnowballStemmer('english')

PRODUCTIVE_KEYWORDS_PT = {
    "solicit", "pedid", "requer", "necessit",
    "erro", "falh", "bug", "problem",
    "suport", "atend", "ajud", "auxil",
    "anex", "document", "arquiv", "comprov",
    "status", "andament", "atualiz", "respost",
    "fatur", "nota", "bolet", "pagament",
    "reclam", "denunc", "inconsist",
    "dúvid", "pergunt", "quest"
}

UNPRODUCTIVE_KEYWORDS_PT = {
    "feliz", "natal", "ano", "boas", "fest",
    "parabén", "congratul",
    "saud", "obrig", "agradec", "valeu",
    "bom", "dia", "boa", "tarde", "noite",
    "felicidad", "abraç", "att", "cordial"
}

PRODUCTIVE_KEYWORDS_EN = {
    "request", "requir", "need",
    "issu", "error", "bug", "failur", "problem",
    "support", "help", "assist", "ticket",
    "attach", "document", "file", "proof",
    "status", "updat", "respons",
    "invoic", "bill", "payment", "refund", "charg",
    "question", "doubt", "inquir", "clarif"
}

UNPRODUCTIVE_KEYWORDS_EN = {
    "happi", "birth", "new", "year", "christma", "season", "greet",
    "congratul", "congrats",
    "thank", "appreci", "grate",
    "best", "regard", "cheer",
    "greet", "hello", "hi", "team"
}


def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(file_stream)
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except:
        return ""

def simple_language_guess(text):
    t = text.lower()
    pt_count = sum(1 for w in STOP_PT if w in t)
    en_count = sum(1 for w in STOP_EN if w in t)
    return "pt" if pt_count >= en_count else "en"

def preprocess_text(text):
    t = text.lower()
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\S+@\S+', ' ', t)  # emails
    t = re.sub(r'http\S+', ' ', t)  # links
    tokens = re.findall(r'\b\w+\b', t, flags=re.UNICODE)
    lang = simple_language_guess(text)
    stops = STOP_PT if lang == 'pt' else STOP_EN
    stemmer = stem_pt if lang == 'pt' else stem_en
    tokens = [stemmer.stem(tok) for tok in tokens if tok not in stops and len(tok) > 1]
    return " ".join(tokens), lang

def rule_based_classify(text, lang):
    tokens = text.lower()
    score_prod = 0
    score_unprod = 0
    if lang == 'pt':
        for kw in PRODUCTIVE_KEYWORDS_PT:
            if kw in tokens:
                score_prod += 1
        for kw in UNPRODUCTIVE_KEYWORDS_PT:
            if kw in tokens:
                score_unprod += 0.5
    else:
        for kw in PRODUCTIVE_KEYWORDS_EN:
            if kw in tokens:
                score_prod += 1
        for kw in UNPRODUCTIVE_KEYWORDS_EN:
            if kw in tokens:
                score_unprod += 1

    if score_prod == 0 and score_unprod == 0:
        return "Produtivo", 0.55
    if score_prod >= score_unprod:
        conf = 0.6 + 0.1 * (score_prod - score_unprod)
        return "Produtivo", min(conf, 0.98)
    if score_prod == 0 and score_unprod == 0:
        return "Indefinido", 0.5
    else:
        conf = 0.6 + 0.1 * (score_unprod - score_prod)
        return "Improdutivo", min(conf, 0.98)

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
    cat, conf = rule_based_classify(preproc, lang)

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

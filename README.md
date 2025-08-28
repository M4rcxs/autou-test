# 📧 AutoU — Classificador de Emails (MVP)

Este projeto é um **classificador de emails produtivos vs. improdutivos**, baseado em regras linguísticas simples (keywords + stemming) para português e inglês.  

Ele roda como uma aplicação **Flask** com API REST e front-end básico em HTML/JS.

---

## ⚡ Funcionalidades

- Upload de **.pdf** ou **.txt** contendo emails  
- Colar texto diretamente na interface web  
- Detecção automática do idioma (**PT/EN**)  
- Classificação em:
  - ✅ **Produtivo** → requer ação, suporte, solicitação, problema etc.  
  - ❌ **Improdutivo** → mensagens sociais, agradecimentos, cumprimentos, etc.  
- Sugestão automática de resposta padrão baseada na categoria  

---

## 🛠️ Tecnologias

- Python 3.10+  
- Flask + Flask-CORS  
- PyPDF2 (extração de texto de PDFs)  
- NLTK (stopwords + stemming)  

---

## 📦 Instalação

Clone o repositório e instale as dependências:

```bash
git clone https://github.com/seu-usuario/autou.git
cd autou
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

Se necessário, baixe os pacotes do NLTK:

```python
import nltk
nltk.download("stopwords")
nltk.download("punkt")
```

---

## 🚀 Executando

Rodar o servidor Flask:

```bash
python app.py
```

A aplicação ficará disponível em:

👉 [http://localhost:5000](http://localhost:5000)

---

## 📤 API

### Endpoint: `/analyze`  
**Método:** `POST`

- **Parâmetros:**
  - `email_text` → texto do email (opcional se enviar arquivo)  
  - `file` → upload de `.pdf` ou `.txt`  

**Resposta JSON:**

```json
{
  "category": "Produtivo",
  "confidence": 0.75,
  "suggested_reply": "Olá, recebemos sua mensagem..."
}
```

---

## 🎨 Interface Web

O projeto já inclui um **front-end simples** em `static/index.html` para testar:

- Colar texto do email ou enviar arquivo  
- Ver classificação (Produtivo x Improdutivo)  
- Ver sugestão de resposta  

---

## 📊 Exemplos

### Produtivo
```
Assunto: Erro no sistema
Olá, não consigo acessar o portal. Aparece a mensagem "erro 502".
```
➡️ Classificação: **Produtivo**

### Improdutivo
```
Assunto: Feliz Natal
Desejo a todos boas festas e um próspero ano novo!
```
➡️ Classificação: **Improdutivo**

---

## 📌 Próximos Passos

- [ ] Melhorar heurísticas de keywords  
- [ ] Treinar modelo supervisionado (Hugging Face)  
- [ ] Adicionar suporte a mais idiomas  
- [ ] Interface mais avançada (React/Vue)  

---

## 👨‍💻 Autor

Feito por [Seu Nome] ✨  
📧 Contato: seuemail@exemplo.com  

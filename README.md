# ⚡ AI Study Buddy

A Flask web app that transforms raw study notes or uploaded PDF documents into clear, structured summaries and interactive self-testing quizzes — powered by Google's Gemini API (`gemini-3.6-flash`).

🔗 **Live Demo:** https://ai-study-buddy-dezb.onrender.com/generate

---

## ✨ Features

- 📄 **Multi-Format Input:** Paste raw text or upload multi-page PDF documents.
- 📝 **Automated Summary:** Generates concise, core-concept summaries instantly.
- 🧠 **Interactive Knowledge Check:** Real-time answer evaluation with option-locking and instant correct/incorrect visual feedback.
- 🔄 **Dynamic Question Set Regeneration:** Generate a fresh set of 5 new questions targeting unexplored angles without page reloads.
- 💾 **Persistent Study History:** SQLite database storage to review previous study sessions and revisit quizzes.
- 🛡️ **Resilient Architecture:** Automated retry mechanism for structured JSON extraction and clear handling for rate limits.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Database** | SQLite, Flask-SQLAlchemy (ORM) |
| **AI Integration** | Google GenAI SDK (`gemini-3.6-flash`) |
| **PDF Extraction** | `pypdf` |
| **Frontend** | HTML5, CSS3, JavaScript (Fetch API), Jinja2 |
| **Deployment** | Gunicorn, Render |

---

## 🚀 Getting Started (Run Locally)

### Prerequisites
- Python 3.9+
- pip
- A Gemini API key from [Google AI Studio](https://aistudio.google.com)

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/swagath20/Ai-study-buddy.git](https://github.com/swagath20/Ai-study-buddy.git)
   cd Ai-study-buddy

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up your environment variables

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
SECRET_KEY=dev-secret-key-123

> ⚠️ Never commit your `.env` file. It's already listed in `.gitignore`.

5. Run the app
```bash
python app.py
```

6. Open your browser at `http://localhost:5000`

---

## 📁 Project Structure

```
ai-study-buddy/
├── app.py                  # Flask application routes, PDF parsing, and Gemini API logic
├── models.py               # SQLAlchemy schema (StudySession model)
├── Procfile                # Gunicorn process definition for production deployment
├── requirements.txt        # Python dependency manifest
├── .env                    # Local secrets (ignored)
├── .gitignore
├── templates/
│   ├── base.html           # Base layout and navigation
│   ├── index.html          # File upload and text input form
│   ├── results.html        # Interactive summary and quiz interface
│   └── history.html        # Past study sessions review
└── static/
    ├── css/style.css       # Custom dark theme styling
    └── js/main.js          # Dynamic DOM rendering and quiz evaluation logic

---

## 🧠 How It Works

1. User pastes text into a form and submits it.
2. The app builds a structured prompt instructing Gemini to return **only valid JSON** — a summary plus 5 quiz questions with multiple-choice options and correct answers.
3. Gemini's response is parsed and validated. If the model returns malformed JSON, the app retries once before failing gracefully.
4. The summary and quiz are saved to the database and rendered on the results page.
5. Users can revisit any past session from the history page.

**Why structured JSON output matters:** without explicit formatting instructions, LLMs often return conversational text around the actual answer (e.g. "Sure, here's your summary:"), which breaks automated parsing. Asking for strict JSON — and validating/retrying when it isn't — is what makes this a reliable feature instead of a fragile demo.

---

## 🔐 Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your free API key from Google AI Studio. Required to run the app. |

When deploying, set this as an environment variable in your hosting platform's dashboard — never hardcode it or commit it.

---

## 🗺️ Roadmap / What I'd Add Next

- [ ] Difficulty selector (easy/medium/hard quiz questions)
- [ ] Flashcard mode
- [ ] Export summary as PDF
- [ ] User accounts (currently sessions aren't tied to a login)

---

## 🐛 Challenges & What I Learned

<!-- Fill this in with a real example once you hit one — great interview talking point -->
One challenge I ran into was ___. I fixed it by ___. This taught me ___.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
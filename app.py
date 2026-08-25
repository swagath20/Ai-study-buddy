import os
import json
import io
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader
from models import db, StudySession

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_buddy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def extract_text_from_pdf(file_stream):
    """Extract plain text from an in-memory PDF byte stream."""
    try:
        reader = PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""


def call_gemini_json(prompt: str):
    """Call Gemini API requiring strict JSON response."""
    if not client:
        raise ValueError("GEMINI_API_KEY is not configured.")

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3
        )
    )
    return json.loads(response.text)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'GET':
        return redirect(url_for('index'))

    notes_text = request.form.get('notes', '').strip()
    pdf_file = request.files.get('pdf_file')

    # Handle PDF input if provided
    if pdf_file and pdf_file.filename != '':
        if pdf_file.filename.lower().endswith('.pdf'):
            pdf_text = extract_text_from_pdf(pdf_file.stream)
            if pdf_text:
                notes_text = f"{notes_text}\n\n{pdf_text}".strip()
            else:
                flash("Could not extract readable text from the uploaded PDF.", "warning")
        else:
            flash("Please upload a valid .pdf file.", "warning")

    if not notes_text:
        flash("Please provide text notes or upload a valid PDF document.", "danger")
        return redirect(url_for('index'))

    prompt = f"""
You are an expert study tutor. Analyze the study material below and return a structured JSON object.

Your response MUST follow this exact schema:
{{
  "summary": "A clear, concise, bulleted or multi-paragraph breakdown highlighting key concepts and takeaways.",
  "quiz": [
    {{
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"
    }}
  ]
}}

Generate exactly 5 high-quality multiple choice questions testing understanding of core concepts.
The "answer" must match one of the items in the "options" array verbatim.

Study Material:
\"\"\"{notes_text}\"\"\"
"""

    try:
        data = call_gemini_json(prompt)
        summary = data.get('summary', 'No summary generated.')
        quiz = data.get('quiz', [])

        # Save session to SQLite
        session_record = StudySession(
            notes=notes_text[:5000],  # store excerpt/full text
            summary=summary,
            quiz_json=json.dumps(quiz)
        )
        db.session.add(session_record)
        db.session.commit()

        return render_template(
            'results.html',
            summary=summary,
            quiz=quiz,
            session_id=session_record.id,
            notes=notes_text
        )

    except Exception as e:
        flash(f"Failed to generate study materials: {str(e)}", "danger")
        return redirect(url_for('index'))


@app.route('/regenerate_quiz', methods=['POST'])
def regenerate_quiz():
    """AJAX endpoint to generate a fresh set of 5 questions without reloading."""
    payload = request.get_json() or {}
    notes_text = payload.get('notes', '').strip()
    session_id = payload.get('session_id')

    if not notes_text and session_id:
        record = StudySession.query.get(session_id)
        if record:
            notes_text = record.notes

    if not notes_text:
        return jsonify({"error": "No study content available to generate questions."}), 400

    prompt = f"""
You are an expert study tutor. Based on the following study material, generate 5 NEW and DISTINCT multiple-choice questions exploring different angles or details.

Return JSON with this schema:
{{
  "quiz": [
    {{
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"
    }}
  ]
}}

The "answer" field must match one of the string items in "options" exactly.

Study Material:
\"\"\"{notes_text}\"\"\"
"""

    try:
        data = call_gemini_json(prompt)
        quiz = data.get('quiz', [])
        return jsonify({"quiz": quiz})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/history')
def history():
    sessions = StudySession.query.order_by(StudySession.created_at.desc()).all()
    return render_template('history.html', sessions=sessions)


@app.route('/history/<int:session_id>')
def view_session(session_id):
    record = StudySession.query.get_or_404(session_id)
    quiz = json.loads(record.quiz_json) if record.quiz_json else []
    return render_template(
        'results.html',
        summary=record.summary,
        quiz=quiz,
        session_id=record.id,
        notes=record.notes
    )


if __name__ == '__main__':
    app.run(debug=True)
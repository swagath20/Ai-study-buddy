import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader
from models import db, StudySession

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_buddy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

with app.app_context():
    db.create_all()

def extract_text_from_pdf(file_storage):
    reader = PdfReader(file_storage)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()

def build_prompt(notes_text):
    return f"""
You are an AI study assistant. Read the provided study notes and generate:
1. A concise, clear summary of the core concepts.
2. A 5-question multiple-choice quiz testing key points.

Study Notes:
\"\"\"{notes_text}\"\"\"

Return ONLY valid JSON matching this exact structure:
{{
  "summary": "Summary text here",
  "quiz": [
    {{
      "question": "Question text here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A"
    }}
  ]
}}
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    notes = request.form.get('notes', '').strip()
    pdf_file = request.files.get('pdf_file')

    # If PDF is provided, extract its text
    if pdf_file and pdf_file.filename != '':
        try:
            pdf_text = extract_text_from_pdf(pdf_file)
            if pdf_text:
                notes = f"{notes}\n\n{pdf_text}".strip()
        except Exception as e:
            flash(f'Failed to parse PDF file: {str(e)}', 'error')
            return redirect(url_for('index'))

    if not notes:
        flash('Please enter notes or upload a PDF file.', 'error')
        return redirect(url_for('index'))

    prompt = build_prompt(notes)

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        data = json.loads(response.text)
        summary = data.get('summary', '')
        quiz = data.get('quiz', [])

        session_entry = StudySession(
            notes_text=notes,
            summary=summary,
            quiz_json=json.dumps(quiz)
        )
        db.session.add(session_entry)
        db.session.commit()

        return render_template('results.html', summary=summary, quiz=quiz, session_id=session_entry.id)

    except json.JSONDecodeError:
        flash('Failed to parse AI response. Please try again.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/generate_more_questions/<int:session_id>', methods=['POST'])
def generate_more_questions(session_id):
    try:
        session_entry = StudySession.query.get(session_id)
        if not session_entry:
            return jsonify({"success": False, "error": "Session not found."}), 404

        existing_quiz = json.loads(session_entry.quiz_json)
        existing_questions = [q.get('question') for q in existing_quiz]

        prompt = f"""
You are an AI study assistant. The user is studying these notes:
\"\"\"{session_entry.notes_text}\"\"\"

Generate 5 brand NEW multiple-choice quiz questions testing different angles than these previous questions:
{json.dumps(existing_questions)}

Return ONLY valid JSON matching this exact structure:
{{
  "quiz": [
    {{
      "question": "New question text here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A"
    }}
  ]
}}
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        new_data = json.loads(response.text)
        new_quiz = new_data.get('quiz', [])

        # Update database history
        updated_history = existing_quiz + new_quiz
        session_entry.quiz_json = json.dumps(updated_history)
        db.session.commit()

        return jsonify({"success": True, "new_questions": new_quiz})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
# Medical Diagnosis Expert System (Flask)

A rule-based expert system built for a Fundamentals of AI course project.
It accepts patient symptoms and suggests the top 3 possible diseases using a
knowledge base and both forward and backward chaining.

## Features

- Symptom input using checkbox list plus free-text description
- Disease-symptom knowledge base with 30+ diseases
- Forward chaining inference engine (data-driven)
- Backward chaining inference engine (goal-driven proof)
- Confidence score ranking (top 3 diagnoses)
- Severity classification (Minor / Moderate / Urgent)
- Age and gender risk modifiers
- Printable patient report (browser print)
- Basic treatment suggestions (non-prescriptive)
- Built-in medical disclaimer

## Project Structure

```
medical_expert_system/
  app.py
  requirements.txt
  README.md
  data/
    diseases.json
    symptoms.json
    disclaimer.txt
  engine/
    knowledge_base.py
    nlp_utils.py
    forward_chaining.py
    backward_chaining.py
    diagnosis.py
  templates/
    base.html
    index.html
    results.html
    report.html
  static/
    css/styles.css
    css/print.css
    js/app.js
  tests/
    test_forward_chaining.py
    test_backward_chaining.py
    test_diagnosis.py
```

## Setup

1. Open a terminal in `medical_expert_system`.
2. Create virtual environment:
   - Windows PowerShell: `python -m venv .venv`
3. Activate environment:
   - PowerShell: `.venv\\Scripts\\Activate.ps1`
4. Install dependencies:
   - `pip install -r requirements.txt`
5. Run app:
   - `python app.py`
6. Open browser:
   - `http://127.0.0.1:5000`

## Quick Cleanup Before Submission

To keep the project lightweight and presentation-ready:

- Do not include `.venv/` in your ZIP/repo (already ignored via `.gitignore`)
- Keep only source files, `data/`, `templates/`, `static/`, and `requirements.txt`
- Remove local cache folders if they appear (`__pycache__/`, `.pytest_cache/`)

## How Inference Works

### Forward Chaining (facts -> conclusions)

- Start with known facts: selected symptom IDs + free-text extracted symptom IDs.
- For each disease rule, if all required symptoms are present, the rule fires.
- Firing creates a candidate disease fact and captures matched symptom tiers.
- Continue until no new rules fire.

### Backward Chaining (goal -> evidence)

- Each disease is treated as a goal hypothesis.
- Required symptoms are checked as an AND condition.
- Common symptoms are represented as an OR boost group.
- A proof tree is generated and displayed in result/report trace output.

## Confidence Scoring

For each fired disease rule:

- `raw = 3.0 * matched_required + 1.5 * matched_common + 0.7 * matched_rare`
- `confidence = 100 * raw * age_modifier * gender_modifier / max_possible`
- score is clipped to `0..99`
- highest confidence diagnoses are ranked and top 3 returned

Severity is taken from KB and can be escalated to Urgent when red-flag symptom
patterns are present (e.g., chest pain + shortness of breath).

## Worked Example

### Example A (Forward chaining)

Input symptoms:

- fever, fatigue, cough, sore_throat, muscle_aches

Likely fired rules include:

- `influenza`
- `covid19` (depending on overlap)
- `pneumonia_viral` (depending on overlap)

The system scores all fired candidates and displays the top 3.

### Example B (Backward chaining)

Goal: prove `influenza`

- Required set = `{fever, fatigue}`
- If both exist in facts, goal is proved.
- Common symptom matches (cough, sore_throat, etc.) increase confidence and
  are shown in the reasoning trace.

## Running Tests

From project root:

- `pytest -q`

Tests cover:

- forward chaining rule firing behavior
- backward chaining proof success/failure
- diagnosis scoring and ranking behavior

## Deployment (Production)

This project is ready for common Python hosting platforms.

- Entry point: `wsgi.py`
- Process file: `Procfile`
- Production server: `gunicorn`

### Required environment variables

- `SECRET_KEY` (required in production)
- `PORT` (provided by hosting platform automatically)
- Optional: `FLASK_DEBUG=0`

### Example platform settings

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT wsgi:app`

## Medical Disclaimer

This application is an educational AI coursework demo only.
It is NOT a medical device and does NOT provide medical diagnosis or treatment.
Always seek professional medical care for real health concerns.

## Suggested Demo Flow (for class presentation)

1. Show knowledge base format in `data/diseases.json`
2. Enter symptoms in UI and run diagnosis
3. Explain top-3 ranking and severity badges
4. Open printable report and show reasoning trace
5. Briefly compare forward vs backward chaining on one disease

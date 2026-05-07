"""Flask web application: Medical Diagnosis Expert System (educational)."""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from engine.diagnosis import diagnose
from engine.knowledge_base import load_knowledge_base, symptoms_by_category
from engine.nlp_utils import extract_symptoms_from_text

APP_ROOT = Path(__file__).resolve().parent
DEBUG_LOG_PATH = APP_ROOT.parent / "debug-42d9a8.log"
DEBUG_LOG_PATH_ALT = APP_ROOT / "debug-42d9a8.log"

app = Flask(
    __name__,
    template_folder=str(APP_ROOT / "templates"),
    static_folder=str(APP_ROOT / "static"),
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")


def _load_disclaimer() -> str:
    p = APP_ROOT / "data" / "disclaimer.txt"
    return p.read_text(encoding="utf-8")


def _append_debug_log(payload: dict) -> None:
    line = json.dumps(payload, ensure_ascii=True) + "\n"
    for p in (DEBUG_LOG_PATH, DEBUG_LOG_PATH_ALT):
        try:
            with p.open("a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            continue


def _age_band(age: int | None) -> str:
    if age is None:
        return "Unknown"
    if age <= 12:
        return "Child"
    if age <= 17:
        return "Adolescent"
    if age <= 64:
        return "Adult"
    return "Older adult"


@app.context_processor
def inject_globals():
    return {"disclaimer_short": "Educational demo only - not medical advice."}


@app.route("/")
def index():
    _append_debug_log(
        {
            "sessionId": "42d9a8",
            "runId": "run1",
            "hypothesisId": "H5",
            "location": "app.py:index",
            "message": "index route hit",
            "data": {"path": "/"},
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
    )
    symptoms, diseases = load_knowledge_base()
    grouped = symptoms_by_category(symptoms)
    category_titles = {
        "general": "General",
        "respiratory": "Respiratory",
        "cardiovascular": "Cardiovascular",
        "gastrointestinal": "Gastrointestinal",
        "neurological": "Neurological",
        "dermatological": "Dermatological",
        "musculoskeletal": "Musculoskeletal",
        "genitourinary": "Genitourinary",
        "endocrine_metabolic": "Endocrine & metabolic",
        "infectious_other": "Infectious & other",
    }
    return render_template(
        "index.html",
        grouped_symptoms=grouped,
        category_titles=category_titles,
        symptom_count=len(symptoms),
        disease_count=len(diseases),
    )


@app.route("/diagnose", methods=["POST"])
def diagnose_route():
    symptoms, diseases = load_knowledge_base()
    selected = set(request.form.getlist("symptoms"))
    free = request.form.get("free_text", "") or ""
    selected |= extract_symptoms_from_text(free, symptoms)

    age_raw = request.form.get("age", "").strip()
    age: int | None
    try:
        age = int(age_raw) if age_raw else None
    except ValueError:
        age = None

    gender = request.form.get("gender") or None

    results, meta = diagnose(
        patient_symptoms=selected,
        diseases=diseases,
        symptoms_catalog=symptoms,
        age=age,
        gender=gender,
        top_n=3,
    )

    # Serializable for session / report
    results_payload = [
        {
            "disease_id": r.disease_id,
            "disease_name": r.disease_name,
            "confidence": r.confidence,
            "severity": r.severity,
            "matched_required": r.matched_required,
            "matched_common": r.matched_common,
            "matched_rare": r.matched_rare,
            "missing_required": r.missing_required,
            "unmatched_common": r.unmatched_common,
            "treatment": r.treatment,
            "forward_iteration": r.forward_iteration,
            "backward_proof_lines": r.backward_proof_lines,
            "age_modifier": r.age_modifier,
            "gender_modifier": r.gender_modifier,
        }
        for r in results
    ]
    session["last_report"] = {
        "patient": {
            "age": age,
            "gender": gender,
            "symptom_ids": sorted(selected),
            "free_text": free,
        },
        "results": results_payload,
        "meta": meta,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    return render_template(
        "results.html",
        results=results,
        meta=meta,
        patient_symptoms=sorted(selected),
        symptom_labels={s.id: s.label for s in symptoms},
        age=age,
        gender=gender,
        free_text=free,
    )


@app.route("/report", methods=["GET"])
def report():
    data = session.get("last_report")
    if not data:
        _append_debug_log(
            {
                "sessionId": "42d9a8",
                "runId": "run1",
                "hypothesisId": "H6",
                "location": "app.py:report",
                "message": "report route hit but no report in session",
                "data": {"path": "/report"},
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
        )
        return redirect(url_for("index"))
    _append_debug_log(
        {
            "sessionId": "42d9a8",
            "runId": "run1",
            "hypothesisId": "H6",
            "location": "app.py:report",
            "message": "report route hit with session report",
            "data": {"path": "/report", "resultsCount": len(data.get("results") or [])},
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
    )
    symptoms, _ = load_knowledge_base()
    labels = {s.id: s.label for s in symptoms}
    patient = data["patient"]
    patient["symptom_labels"] = [labels.get(sid, sid) for sid in patient.get("symptom_ids", [])]
    patient["age_band"] = _age_band(patient.get("age"))
    patient["symptom_total"] = len(patient.get("symptom_ids") or [])
    top_result = (data.get("results") or [None])[0]
    patient["primary_impression"] = top_result["disease_name"] if top_result else "No likely diagnosis"
    patient["primary_confidence"] = top_result["confidence"] if top_result else 0.0
    disclaimer = _load_disclaimer()
    # Rehydrate as simple dicts for template
    results = copy.deepcopy(data["results"])
    return render_template(
        "report.html",
        patient=patient,
        results=results,
        meta=data.get("meta") or {},
        disclaimer=disclaimer,
        generated_at=data.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M"),
    )


@app.route("/_debug/client-log", methods=["POST"])
def debug_client_log():
    payload = request.get_json(silent=True) or {}
    payload.setdefault("sessionId", "42d9a8")
    payload.setdefault("timestamp", int(datetime.now().timestamp() * 1000))
    _append_debug_log(payload)
    return jsonify({"ok": True})


@app.route("/_debug/probe", methods=["GET"])
def debug_probe():
    payload = {
        "sessionId": "42d9a8",
        "runId": "run1",
        "hypothesisId": "H7",
        "location": "app.py:_debug/probe",
        "message": "probe route hit",
        "data": {
            "cwd": os.getcwd(),
            "appRoot": str(APP_ROOT),
            "logPathPrimary": str(DEBUG_LOG_PATH),
            "logPathAlt": str(DEBUG_LOG_PATH_ALT),
        },
        "timestamp": int(datetime.now().timestamp() * 1000),
    }
    _append_debug_log(payload)
    return jsonify(payload["data"])


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=debug, host=host, port=port)

import sqlite3
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import json
import numpy as np
from fastapi import Query
from fastapi.staticfiles import StaticFiles


DB_PATH = "clinic.db"
STATIC_DIR = Path("static")
PHOTO_DIR = STATIC_DIR / "patient_photos"

# Ensure folders exist
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Clinic Medical Records API",
    description="FastAPI backend for patients, encounters, and face search (skeleton).",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# CORS (optional, but useful if you’ll call from a browser frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in real production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# DB helper
# -------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys every time
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# -------------------------------------------------------------------
# Pydantic models (request/response schemas)
# -------------------------------------------------------------------
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # 'YYYY-MM-DD'
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class Patient(BaseModel):
    patient_id: int
    first_name: str
    last_name: str
    date_of_birth: str
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    photo_path: Optional[str] = None


class PatientSummary(BaseModel):
    patient_id: int
    first_name: str
    last_name: str
    date_of_birth: str
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    photo_path: Optional[str]
    active_conditions: Optional[str] = None
    active_medications: Optional[str] = None
    active_allergies: Optional[str] = None


class EncounterCreate(BaseModel):
    patient_id: int
    encounter_date: str            # 'YYYY-MM-DD HH:MM:SS'
    encounter_type: Optional[str] = None
    presenting_complaint: str
    history_of_present_illness: Optional[str] = None
    doctor_name: Optional[str] = None
    disposition: Optional[str] = None


class Encounter(BaseModel):
    encounter_id: int
    patient_id: int
    encounter_date: str
    encounter_type: Optional[str]
    presenting_complaint: str
    history_of_present_illness: Optional[str]
    doctor_name: Optional[str]
    disposition: Optional[str]


class FaceSearchResult(BaseModel):
    match_found: bool
    confidence: float
    patient: Optional[PatientSummary] = None

class MedicationOut(BaseModel):
    medication_id: int
    drug_name: str
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool


class AllergyOut(BaseModel):
    allergy_id: int
    allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = None
    noted_date: Optional[str] = None
    is_active: bool


class VitalsOut(BaseModel):
    recorded_at: str
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature_c: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None


class LabResultOut(BaseModel):
    lab_result_id: int
    test_name: str
    result_value: str
    units: Optional[str] = None
    reference_range: Optional[str] = None
    result_date: Optional[str] = None


class EncounterVitalsLabs(BaseModel):
    encounter_id: int
    encounter_date: str
    encounter_type: Optional[str] = None
    presenting_complaint: Optional[str] = None
    vitals: Optional[VitalsOut] = None
    lab_results: List[LabResultOut] = []

class EncounterCreate(BaseModel):
    encounter_type: str
    presenting_complaint: str
    doctor_name: Optional[str] = None


# -------------------------------------------------------------------
# Utility: convert sqlite Row -> dict
# -------------------------------------------------------------------
def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


# -------------------------------------------------------------------
# Placeholder for face embedding extraction
# -------------------------------------------------------------------
def extract_face_embedding(image_bytes: bytes) -> List[float]:
    """
    TODO: Replace this with real face embedding extraction using a model
    like face-recognition, deepface, etc.

    For now, this just raises an error to remind you to implement it.
    """
    raise NotImplementedError("Face embedding extraction not implemented yet.")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    a_arr = np.array(a, dtype=float)
    b_arr = np.array(b, dtype=float)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


def find_best_face_match(query_embedding: List[float], min_similarity: float = 0.85):
    """
    Load all embeddings from the DB and return best (patient_id, score) if above threshold.
    Otherwise return (None, best_score).
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT patient_id, embedding_json FROM patient_face_embeddings")
    rows = cur.fetchall()
    conn.close()

    best_patient_id = None
    best_score = -1.0

    for row in rows:
        emb = json.loads(row["embedding_json"])
        score = cosine_similarity(query_embedding, emb)
        if score > best_score:
            best_score = score
            best_patient_id = row["patient_id"]

    if best_score >= min_similarity:
        return best_patient_id, best_score
    else:
        return None, best_score


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Clinic API is running"}


# ---------------- Patients ----------------

@app.get("/patients/search", response_model=List[Patient])
def search_patients(
    name: Optional[str] = Query(
        None,
        description="Partial match on first or last name",
    ),
    date_of_birth: Optional[str] = Query(
        None,
        description="Exact DOB in 'YYYY-MM-DD' format",
    ),
    limit: int = 20,
    offset: int = 0,
):
    """
    Search patients by partial name and/or exact date of birth.
    This will be the main search endpoint your frontend uses.
    """
    conn = get_db()
    cur = conn.cursor()

    sql = "SELECT * FROM patients WHERE 1=1"
    params = []

    if name:
        like = f"%{name.lower()}%"
        sql += " AND (LOWER(first_name) LIKE ? OR LOWER(last_name) LIKE ?)"
        params.extend([like, like])

    if date_of_birth:
        sql += " AND date_of_birth = ?"
        params.append(date_of_birth)

    sql += " ORDER BY last_name, first_name LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return [Patient(**row_to_dict(r)) for r in rows]

@app.post("/patients", response_model=Patient)
def create_patient(patient: PatientCreate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO patients (first_name, last_name, date_of_birth, sex, phone_number, email, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            patient.first_name,
            patient.last_name,
            patient.date_of_birth,
            patient.sex,
            patient.phone_number,
            patient.email,
            patient.address,
        ),
    )
    conn.commit()
    patient_id = cur.lastrowid

    cur.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    row = cur.fetchone()
    conn.close()

    return Patient(**row_to_dict(row))


@app.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return Patient(**row_to_dict(row))


@app.get("/patients/{patient_id}/summary", response_model=PatientSummary)
def get_patient_summary(patient_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM patient_summary WHERE patient_id = ?",
        (patient_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Patient summary not found")

    data = row_to_dict(row)
    # Rename keys from snake_case in view to Pydantic model fields:
    return PatientSummary(
        patient_id=data["patient_id"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        date_of_birth=data["date_of_birth"],
        sex=data.get("sex"),
        phone_number=data.get("phone_number"),
        email=data.get("email"),
        address=data.get("address"),
        photo_path=data.get("photo_path"),
        active_conditions=data.get("active_conditions"),
        active_medications=data.get("active_medications"),
        active_allergies=data.get("active_allergies"),
    )


@app.get("/patients", response_model=List[Patient])
def list_patients(limit: int = 50, offset: int = 0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM patients ORDER BY patient_id LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    return [Patient(**row_to_dict(r)) for r in rows]


# ---------------- Encounters ----------------
@app.post("/encounters", response_model=Encounter)
def create_encounter(enc: EncounterCreate):
    # Check patient exists
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM patients WHERE patient_id = ?", (enc.patient_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")

    cur.execute(
        """
        INSERT INTO encounters (
            patient_id, encounter_date, encounter_type,
            presenting_complaint, history_of_present_illness,
            doctor_name, disposition
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            enc.patient_id,
            enc.encounter_date,
            enc.encounter_type,
            enc.presenting_complaint,
            enc.history_of_present_illness,
            enc.doctor_name,
            enc.disposition,
        ),
    )
    conn.commit()
    encounter_id = cur.lastrowid

    cur.execute("SELECT * FROM encounters WHERE encounter_id = ?", (encounter_id,))
    row = cur.fetchone()
    conn.close()

    return Encounter(**row_to_dict(row))


@app.get("/encounters/{encounter_id}", response_model=Encounter)
def get_encounter(encounter_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM encounters WHERE encounter_id = ?", (encounter_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Encounter not found")

    return Encounter(**row_to_dict(row))


@app.get("/patients/{patient_id}/encounters", response_model=List[Encounter])
def list_patient_encounters(patient_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM encounters WHERE patient_id = ? ORDER BY encounter_date DESC",
        (patient_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [Encounter(**row_to_dict(r)) for r in rows]


@app.post("/patients/{patient_id}/encounters", response_model=Encounter)
def create_patient_encounter(patient_id: int, payload: EncounterCreate):
    conn = get_db()
    cur = conn.cursor()

    # Check patient exists
    cur.execute("SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")

    # timestamp
    encounter_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Insert
    cur.execute(
        """
        INSERT INTO encounters (
            patient_id,
            encounter_date,
            encounter_type,
            presenting_complaint,
            doctor_name
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            encounter_date,
            payload.encounter_type,
            payload.presenting_complaint,
            payload.doctor_name,
        ),
    )
    conn.commit()

    new_id = cur.lastrowid

    cur.execute(
        """
        SELECT encounter_id, patient_id, encounter_date,
               encounter_type, presenting_complaint, doctor_name
        FROM encounters WHERE encounter_id = ?
        """,
        (new_id,),
    )
    row = cur.fetchone()
    conn.close()

    return Encounter(**row_to_dict(row))


@app.get("/patients/{patient_id}/medications", response_model=List[MedicationOut])
def list_patient_medications(patient_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            medication_id,
            drug_name,
            dose,
            route,
            frequency,
            start_date,
            end_date,
            is_active
        FROM medications
        WHERE patient_id = ?
        ORDER BY is_active DESC, start_date DESC
        """,
        (patient_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [MedicationOut(**row_to_dict(r)) for r in rows]


@app.get("/patients/{patient_id}/allergies", response_model=List[AllergyOut])
def list_patient_allergies(patient_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            allergy_id,
            allergen,
            reaction,
            severity,
            noted_date,
            is_active
        FROM allergies
        WHERE patient_id = ?
        ORDER BY is_active DESC, noted_date DESC
        """,
        (patient_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [AllergyOut(**row_to_dict(r)) for r in rows]


@app.get(
    "/patients/{patient_id}/vitals-labs",
    response_model=List[EncounterVitalsLabs],
)
def list_patient_vitals_labs(patient_id: int):
    """
    For each encounter, return latest vitals (if any) and all lab results.
    """
    conn = get_db()
    cur = conn.cursor()

    # get encounters for this patient
    cur.execute(
        """
        SELECT
            encounter_id,
            encounter_date,
            encounter_type,
            presenting_complaint
        FROM encounters
        WHERE patient_id = ?
        ORDER BY encounter_date DESC
        """,
        (patient_id,),
    )
    encounters = cur.fetchall()

    results: List[EncounterVitalsLabs] = []

    for enc in encounters:
        enc_dict = row_to_dict(enc)
        enc_id = enc_dict["encounter_id"]

        # latest vitals for this encounter
        cur.execute(
            """
            SELECT
                recorded_at,
                systolic_bp,
                diastolic_bp,
                heart_rate,
                respiratory_rate,
                temperature_c,
                oxygen_saturation,
                weight_kg,
                height_cm
            FROM vitals
            WHERE encounter_id = ?
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (enc_id,),
        )
        v_row = cur.fetchone()
        vitals = VitalsOut(**row_to_dict(v_row)) if v_row else None

        # all lab results for this encounter
        cur.execute(
            """
            SELECT
                lab_result_id,
                test_name,
                result_value,
                units,
                reference_range,
                result_date
            FROM lab_results
            WHERE encounter_id = ?
            ORDER BY result_date DESC
            """,
            (enc_id,),
        )
        lab_rows = cur.fetchall()
        labs = [LabResultOut(**row_to_dict(r)) for r in lab_rows]

        results.append(
            EncounterVitalsLabs(
                encounter_id=enc_id,
                encounter_date=enc_dict["encounter_date"],
                encounter_type=enc_dict.get("encounter_type"),
                presenting_complaint=enc_dict.get("presenting_complaint"),
                vitals=vitals,
                lab_results=labs,
            )
        )

    conn.close()
    return results

# ---------------- Photo upload + face embedding skeleton ----------------
@app.post("/patients/{patient_id}/photo", response_model=Patient)
async def upload_patient_photo(patient_id: int, file: UploadFile = File(...)):
    conn = get_db()
    cur = conn.cursor()

    # Check patient exists
    cur.execute("SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")

    # Save file to static/patient_photos
    filename = f"patient_{patient_id}_{file.filename}"
    file_path = PHOTO_DIR / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store URL-style relative path (with forward slashes)
    photo_path = f"static/patient_photos/{filename}"

    cur.execute(
        "UPDATE patients SET photo_path = ? WHERE patient_id = ?",
        (photo_path, patient_id),
    )
    conn.commit()

    # Return updated patient
    cur.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    row = cur.fetchone()
    conn.close()
    return Patient(**row_to_dict(row))



@app.post("/patients/search/face", response_model=FaceSearchResult)
async def search_patient_by_face(file: UploadFile = File(...)):
    image_bytes = await file.read()

    # Extract embedding (NOT IMPLEMENTED YET)
    try:
        query_embedding = extract_face_embedding(image_bytes)
    except NotImplementedError as e:
        # For now, clearly signal that the model isn't implemented
        raise HTTPException(status_code=501, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not process face image")

    # Find best match
    patient_id, score = find_best_face_match(query_embedding, min_similarity=0.85)

    if patient_id is None:
        return FaceSearchResult(match_found=False, confidence=score, patient=None)

    # Fetch summary for matched patient
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM patient_summary WHERE patient_id = ?",
        (patient_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        # Should not normally happen if DB is consistent
        raise HTTPException(status_code=404, detail="Matched patient summary not found")

    data = row_to_dict(row)
    patient_summary = PatientSummary(
        patient_id=data["patient_id"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        date_of_birth=data["date_of_birth"],
        sex=data.get("sex"),
        phone_number=data.get("phone_number"),
        email=data.get("email"),
        address=data.get("address"),
        active_conditions=data.get("active_conditions"),
        active_medications=data.get("active_medications"),
        active_allergies=data.get("active_allergies"),
    )

    return FaceSearchResult(
        match_found=True,
        confidence=score,
        patient=patient_summary,
    )

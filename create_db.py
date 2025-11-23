import sqlite3
from pathlib import Path

DB_PATH = "clinic.db"

schema = """
PRAGMA foreign_keys = ON;

-- ===============================
-- PATIENTS
-- ===============================
CREATE TABLE IF NOT EXISTS patients (
    patient_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name       TEXT NOT NULL,
    last_name        TEXT NOT NULL,
    date_of_birth    TEXT NOT NULL,        -- 'YYYY-MM-DD'
    sex              TEXT,
    phone_number     TEXT,
    email            TEXT,
    address          TEXT,
    photo_path       TEXT,                 -- optional path to stored face image
    created_at       TEXT DEFAULT (datetime('now'))
);

-- ===============================
-- ENCOUNTERS (VISITS)
-- ===============================
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id                INTEGER NOT NULL,
    encounter_date            TEXT NOT NULL,      -- 'YYYY-MM-DD HH:MM:SS'
    encounter_type            TEXT,               -- 'A&E', 'OPD', 'Ward', etc.
    presenting_complaint      TEXT NOT NULL,
    history_of_present_illness TEXT,
    doctor_name               TEXT,
    disposition               TEXT,               -- 'Discharged', 'Admitted', etc.
    created_at                TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- CHRONIC & PAST MEDICAL CONDITIONS
-- ===============================
CREATE TABLE IF NOT EXISTS medical_conditions (
    condition_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL,
    name           TEXT NOT NULL,     -- e.g. 'Type 2 Diabetes Mellitus'
    code_system    TEXT,              -- e.g. 'ICD10', 'SNOMED'
    code           TEXT,
    onset_date     TEXT,              -- 'YYYY-MM-DD'
    resolved_date  TEXT,
    is_active      INTEGER DEFAULT 1, -- 1 = active, 0 = inactive
    notes          TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- SURGERIES / PROCEDURES
-- ===============================
CREATE TABLE IF NOT EXISTS surgeries (
    surgery_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL,
    name           TEXT NOT NULL,    -- e.g. 'Appendectomy'
    surgery_date   TEXT,             -- 'YYYY-MM-DD'
    complications  TEXT,
    notes          TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- MEDICATIONS (CURRENT + PAST)
-- ===============================
CREATE TABLE IF NOT EXISTS medications (
    medication_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL,
    drug_name      TEXT NOT NULL,
    dose           TEXT,             -- '500 mg'
    route          TEXT,             -- 'oral', 'IV', etc.
    frequency      TEXT,             -- 'once daily', 'bd', etc.
    start_date     TEXT,
    end_date       TEXT,
    is_active      INTEGER DEFAULT 1, -- 1 = currently taking
    prescribed_by  TEXT,
    notes          TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- ALLERGIES & ADVERSE REACTIONS
-- ===============================
CREATE TABLE IF NOT EXISTS allergies (
    allergy_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL,
    allergen      TEXT NOT NULL,       -- 'Penicillin'
    reaction      TEXT,                -- 'Rash', 'Anaphylaxis'
    severity      TEXT,                -- 'Mild', 'Moderate', 'Severe'
    noted_date    TEXT,
    is_active     INTEGER DEFAULT 1,
    notes         TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- FAMILY HISTORY
-- ===============================
CREATE TABLE IF NOT EXISTS family_history (
    family_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id        INTEGER NOT NULL,
    relationship      TEXT,            -- 'Mother', 'Father', 'Sibling'
    condition_name    TEXT,            -- 'Hypertension'
    age_at_diagnosis  INTEGER,
    notes             TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- SOCIAL HISTORY (CURRENT SNAPSHOT)
-- ===============================
CREATE TABLE IF NOT EXISTS social_history (
    social_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id        INTEGER NOT NULL UNIQUE,
    smoking_status    TEXT,           -- 'Never', 'Former', 'Current'
    pack_years        REAL,
    alcohol_use       TEXT,           -- e.g. '10 units/week'
    drug_use          TEXT,
    occupation        TEXT,
    living_situation  TEXT,           -- 'Lives alone', 'With family'
    last_updated      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- IMMUNIZATIONS
-- ===============================
CREATE TABLE IF NOT EXISTS immunizations (
    immunization_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id       INTEGER NOT NULL,
    vaccine_name     TEXT NOT NULL,    -- 'Influenza', 'COVID-19'
    dose_number      INTEGER,
    vaccination_date TEXT,
    lot_number       TEXT,
    notes            TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- VITAL SIGNS (PER ENCOUNTER)
-- ===============================
CREATE TABLE IF NOT EXISTS vitals (
    vital_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id      INTEGER NOT NULL,
    recorded_at       TEXT NOT NULL,    -- 'YYYY-MM-DD HH:MM:SS'
    systolic_bp       INTEGER,
    diastolic_bp      INTEGER,
    heart_rate        INTEGER,
    respiratory_rate  INTEGER,
    temperature_c     REAL,
    oxygen_saturation REAL,
    weight_kg         REAL,
    height_cm         REAL,
    notes             TEXT,
    FOREIGN KEY(encounter_id) REFERENCES encounters(encounter_id)
);

-- ===============================
-- LAB RESULTS (PER ENCOUNTER)
-- ===============================
CREATE TABLE IF NOT EXISTS lab_results (
    lab_result_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id     INTEGER NOT NULL,
    test_name        TEXT NOT NULL,   -- 'HbA1c', 'Creatinine'
    result_value     TEXT,
    units            TEXT,
    reference_range  TEXT,
    result_date      TEXT,
    notes            TEXT,
    FOREIGN KEY(encounter_id) REFERENCES encounters(encounter_id)
);

-- ===============================
-- DIAGNOSES PER ENCOUNTER
-- ===============================
CREATE TABLE IF NOT EXISTS encounter_diagnoses (
    encounter_diagnosis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id           INTEGER NOT NULL,
    diagnosis_name         TEXT NOT NULL,
    code_system            TEXT,
    code                   TEXT,
    is_primary             INTEGER DEFAULT 0, -- 1 = primary diagnosis
    notes                  TEXT,
    FOREIGN KEY(encounter_id) REFERENCES encounters(encounter_id)
);

-- ===============================
-- FACE EMBEDDINGS FOR FACE SEARCH
-- ===============================
CREATE TABLE IF NOT EXISTS patient_face_embeddings (
    embedding_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL,
    embedding_json TEXT NOT NULL,       -- e.g. "[0.123, -0.045, ...]"
    created_at     TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

-- ===============================
-- USEFUL INDEXES
-- ===============================
CREATE INDEX IF NOT EXISTS idx_encounters_patient
    ON encounters (patient_id);

CREATE INDEX IF NOT EXISTS idx_medical_conditions_patient_active
    ON medical_conditions (patient_id, is_active);

CREATE INDEX IF NOT EXISTS idx_medications_patient_active
    ON medications (patient_id, is_active);

CREATE INDEX IF NOT EXISTS idx_allergies_patient_active
    ON allergies (patient_id, is_active);

CREATE INDEX IF NOT EXISTS idx_vitals_encounter
    ON vitals (encounter_id);

CREATE INDEX IF NOT EXISTS idx_lab_results_encounter
    ON lab_results (encounter_id);

CREATE INDEX IF NOT EXISTS idx_face_embeddings_patient
    ON patient_face_embeddings (patient_id);

-- ===============================
-- PATIENT SUMMARY VIEW
-- ===============================
DROP VIEW IF EXISTS patient_summary;

CREATE VIEW patient_summary AS
SELECT 
    p.patient_id,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.sex,
    p.phone_number,
    p.email,
    p.address,
    -- Semicolon-separated lists of key clinical info
    (
        SELECT GROUP_CONCAT(mc.name, '; ')
        FROM medical_conditions mc
        WHERE mc.patient_id = p.patient_id
          AND mc.is_active = 1
    ) AS active_conditions,
    (
        SELECT GROUP_CONCAT(m.drug_name || 
                            CASE WHEN m.dose IS NOT NULL THEN ' ' || m.dose ELSE '' END, '; ')
        FROM medications m
        WHERE m.patient_id = p.patient_id
          AND m.is_active = 1
    ) AS active_medications,
    (
        SELECT GROUP_CONCAT(a.allergen || 
                            CASE WHEN a.severity IS NOT NULL THEN ' (' || a.severity || ')' ELSE '' END, '; ')
        FROM allergies a
        WHERE a.patient_id = p.patient_id
          AND a.is_active = 1
    ) AS active_allergies
FROM patients p;
"""

def create_database(db_path: str = DB_PATH):
    """Create the SQLite database and all tables/views."""
    db_file = Path(db_path)
    conn = sqlite3.connect(db_file)
    try:
        # Important: enable foreign keys for this connection
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema)
        conn.commit()
        print(f"Database created/updated at: {db_file.resolve()}")
    finally:
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    create_database()

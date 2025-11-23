import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = "clinic.db"

FIRST_NAMES = [
    "John", "Jane", "Michael", "Sarah", "David", "Emily", "James", "Olivia",
    "Daniel", "Sophia", "Matthew", "Amina", "Ibrahim", "Fatima", "Oluwadamilola",
    "Chinedu", "Kofi", "Amara", "Hassan", "Grace"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Okafor", "Adeyemi", "Mensah", "Bello",
    "Ibrahim", "Ahmed", "Khan", "Osei", "Taylor", "Clark"
]

SEXES = ["Male", "Female", "Other"]

CONDITIONS = [
    ("Hypertension", "I10"),
    ("Type 2 Diabetes Mellitus", "E11"),
    ("Asthma", "J45"),
    ("Chronic Kidney Disease", "N18"),
    ("Ischaemic Heart Disease", "I25"),
    ("Depression", "F32"),
    ("Epilepsy", "G40"),
]

MEDICATIONS = [
    "Metformin 500 mg",
    "Lisinopril 10 mg",
    "Amlodipine 5 mg",
    "Salbutamol Inhaler",
    "Sertraline 50 mg",
    "Atorvastatin 20 mg",
    "Omeprazole 20 mg",
]

ALLERGENS = [
    ("Penicillin", "Rash"),
    ("Penicillin", "Anaphylaxis"),
    ("Peanuts", "Anaphylaxis"),
    ("Shellfish", "Swelling"),
    ("Latex", "Rash"),
]

VACCINES = [
    "Influenza", "COVID-19", "Tetanus", "Hepatitis B", "HPV"
]

LAB_TESTS = [
    ("HbA1c", "mmol/mol", "20-48"),
    ("Creatinine", "umol/L", "60-110"),
    ("Hemoglobin", "g/dL", "12-16"),
    ("WBC", "x10^9/L", "4-11"),
    ("Platelets", "x10^9/L", "150-400"),
]

OCCUPATIONS = [
    "Teacher", "Engineer", "Trader", "Student", "Farmer",
    "Software Developer", "Nurse", "Driver", "Accountant", "Chef"
]

LIVING_SITUATIONS = [
    "Lives alone", "With family", "With partner", "Shared accommodation"
]


def random_date(start_year=1940, end_year=2015):
    """Return a random date between start_year-01-01 and end_year-12-31."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")


def random_datetime_in_last_year():
    now = datetime.now()
    start = now - timedelta(days=365)
    random_seconds = random.randint(0, int((now - start).total_seconds()))
    dt = start + timedelta(seconds=random_seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def seed_patients(conn, num_patients=79):
    cur = conn.cursor()
    patients_ids = []

    for _ in range(num_patients):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        dob = random_date(1940, 2015)
        sex = random.choice(SEXES)
        phone = f"+44 7{random.randint(100000000, 999999999)}"
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
        address = f"{random.randint(1, 200)} Example Street, City"

        cur.execute(
            """
            INSERT INTO patients (first_name, last_name, date_of_birth, sex, phone_number, email, address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (first_name, last_name, dob, sex, phone, email, address),
        )
        patients_ids.append(cur.lastrowid)

    conn.commit()
    return patients_ids


def seed_social_history(conn, patient_ids):
    cur = conn.cursor()
    for pid in patient_ids:
        smoking_status = random.choice(["Never", "Former", "Current"])
        pack_years = round(random.uniform(0, 40), 1) if smoking_status != "Never" else 0.0
        alcohol_use = f"{random.randint(0, 30)} units/week"
        drug_use = random.choice(["None", "Occasional", "Regular"])
        occupation = random.choice(OCCUPATIONS)
        living = random.choice(LIVING_SITUATIONS)

        cur.execute(
            """
            INSERT OR REPLACE INTO social_history (
                patient_id, smoking_status, pack_years,
                alcohol_use, drug_use, occupation, living_situation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (pid, smoking_status, pack_years, alcohol_use, drug_use, occupation, living),
        )
    conn.commit()


def seed_conditions(conn, patient_ids):
    cur = conn.cursor()
    for pid in patient_ids:
        num_conditions = random.randint(0, 3)
        for _ in range(num_conditions):
            name, code = random.choice(CONDITIONS)
            onset = random_date(1990, 2023)
            is_active = random.choice([0, 1, 1])  # bias slightly towards active
            cur.execute(
                """
                INSERT INTO medical_conditions (patient_id, name, code_system, code, onset_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pid, name, "ICD10", code, onset, is_active),
            )
    conn.commit()


def seed_medications(conn, patient_ids):
    cur = conn.cursor()
    for pid in patient_ids:
        num_meds = random.randint(0, 4)
        for _ in range(num_meds):
            med = random.choice(MEDICATIONS)
            parts = med.split()
            drug_name = " ".join(parts[:-2]) if len(parts) > 2 else med
            dose = " ".join(parts[-2:]) if len(parts) > 2 else None

            start_date = random_date(2015, 2024)
            is_active = random.choice([0, 1, 1])  # more likely active
            end_date = None
            if not is_active:
                # some time after start date
                end_date = random_date(2016, 2024)

            cur.execute(
                """
                INSERT INTO medications (
                    patient_id, drug_name, dose, route, frequency,
                    start_date, end_date, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid,
                    drug_name,
                    dose,
                    "oral",
                    random.choice(["once daily", "bd", "tid"]),
                    start_date,
                    end_date,
                    is_active,
                ),
            )
    conn.commit()


def seed_allergies(conn, patient_ids):
    cur = conn.cursor()
    for pid in patient_ids:
        num_allergies = random.randint(0, 2)
        for _ in range(num_allergies):
            allergen, reaction = random.choice(ALLERGENS)
            severity = random.choice(["Mild", "Moderate", "Severe"])
            noted_date = random_date(2000, 2024)
            cur.execute(
                """
                INSERT INTO allergies (
                    patient_id, allergen, reaction, severity, noted_date, is_active
                )
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (pid, allergen, reaction, severity, noted_date),
            )
    conn.commit()


def seed_immunizations(conn, patient_ids):
    cur = conn.cursor()
    for pid in patient_ids:
        num_vaccines = random.randint(0, 3)
        for _ in range(num_vaccines):
            vaccine = random.choice(VACCINES)
            dose_number = random.randint(1, 3)
            vaccination_date = random_date(2000, 2024)
            lot_number = f"LOT{random.randint(10000, 99999)}"
            cur.execute(
                """
                INSERT INTO immunizations (
                    patient_id, vaccine_name, dose_number, vaccination_date, lot_number
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (pid, vaccine, dose_number, vaccination_date, lot_number),
            )
    conn.commit()


def seed_encounters_vitals_labs(conn, patient_ids):
    cur = conn.cursor()
    for pid in patient_ids:
        num_encounters = random.randint(1, 4)
        for _ in range(num_encounters):
            encounter_date = random_datetime_in_last_year()
            encounter_type = random.choice(["A&E", "OPD", "Ward", "Telehealth"])
            complaint = random.choice([
                "Chest pain", "Shortness of breath", "Headache",
                "Abdominal pain", "Fever", "Routine check-up"
            ])
            hpi = f"{complaint} for {random.randint(1, 14)} days."
            doctor_name = random.choice(["Dr Smith", "Dr Brown", "Dr Ahmed", "Dr Taylor"])
            disposition = random.choice(["Discharged", "Admitted", "Referred"])

            cur.execute(
                """
                INSERT INTO encounters (
                    patient_id, encounter_date, encounter_type,
                    presenting_complaint, history_of_present_illness,
                    doctor_name, disposition
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (pid, encounter_date, encounter_type, complaint, hpi, doctor_name, disposition),
            )
            encounter_id = cur.lastrowid

            # Vitals
            systolic = random.randint(90, 180)
            diastolic = random.randint(60, 110)
            hr = random.randint(55, 120)
            rr = random.randint(12, 30)
            temp = round(random.uniform(36.0, 40.5), 1)
            spo2 = round(random.uniform(88.0, 100.0), 1)
            weight = round(random.uniform(45.0, 120.0), 1)
            height = round(random.uniform(150.0, 200.0), 1)

            cur.execute(
                """
                INSERT INTO vitals (
                    encounter_id, recorded_at, systolic_bp, diastolic_bp,
                    heart_rate, respiratory_rate, temperature_c,
                    oxygen_saturation, weight_kg, height_cm
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    encounter_id, encounter_date, systolic, diastolic,
                    hr, rr, temp, spo2, weight, height,
                ),
            )

            # Labs (some encounters may have labs)
            if random.random() < 0.7:
                num_tests = random.randint(1, 4)
                for _ in range(num_tests):
                    test_name, units, ref = random.choice(LAB_TESTS)
                    # generate rough plausible-ish value as string
                    if test_name == "HbA1c":
                        value = str(round(random.uniform(30, 90), 1))
                    elif test_name == "Creatinine":
                        value = str(round(random.uniform(50, 400), 1))
                    elif test_name == "Hemoglobin":
                        value = str(round(random.uniform(8, 18), 1))
                    elif test_name == "WBC":
                        value = str(round(random.uniform(2, 20), 1))
                    elif test_name == "Platelets":
                        value = str(round(random.uniform(50, 600), 1))
                    else:
                        value = str(round(random.uniform(1, 100), 1))

                    cur.execute(
                        """
                        INSERT INTO lab_results (
                            encounter_id, test_name, result_value,
                            units, reference_range, result_date
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            encounter_id, test_name, value,
                            units, ref, encounter_date
                        ),
                    )
    conn.commit()


def main():
    db_file = Path(DB_PATH)
    if not db_file.exists():
        raise FileNotFoundError(f"{DB_PATH} not found. Run create_db.py first.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    print("Seeding database with fictitious data...")

    patient_ids = seed_patients(conn, num_patients=79)
    print(f"Inserted {len(patient_ids)} patients.")

    seed_social_history(conn, patient_ids)
    print("Social history seeded.")

    seed_conditions(conn, patient_ids)
    print("Medical conditions seeded.")

    seed_medications(conn, patient_ids)
    print("Medications seeded.")

    seed_allergies(conn, patient_ids)
    print("Allergies seeded.")

    seed_immunizations(conn, patient_ids)
    print("Immunizations seeded.")

    seed_encounters_vitals_labs(conn, patient_ids)
    print("Encounters, vitals, and lab results seeded.")

    conn.close()
    print("Seeding complete.")


if __name__ == "__main__":
    main()

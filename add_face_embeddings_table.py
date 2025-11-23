import sqlite3

DB_PATH = "clinic.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create table if it doesn't exist
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS face_embeddings (
            embedding_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id     INTEGER NOT NULL,
            embedding_json TEXT NOT NULL,
            created_at     TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );
        """
    )

    # Optional: ensure one embedding per patient (if you want)
    # This is just a comment; logic will be in code.

    conn.commit()
    conn.close()
    print("face_embeddings table is ready.")

if __name__ == "__main__":
    main()

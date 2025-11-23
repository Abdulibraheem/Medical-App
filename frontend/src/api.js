const API_BASE = "http://127.0.0.1:8000";

export async function searchPatients(name, dob) {
  const params = new URLSearchParams();
  if (name) params.append("name", name);
  if (dob) params.append("date_of_birth", dob);

  const res = await fetch(`${API_BASE}/patients/search?` + params.toString());
  if (!res.ok) throw new Error("Failed to search patients");
  return res.json();
}

export async function getPatientSummary(patientId) {
  const res = await fetch(`${API_BASE}/patients/${patientId}/summary`);
  if (!res.ok) throw new Error("Failed to fetch patient summary");
  return res.json();
}

export async function getPatientEncounters(patientId) {
  const res = await fetch(`${API_BASE}/patients/${patientId}/encounters`);
  if (!res.ok) throw new Error("Failed to fetch encounters");
  return res.json();
}

export async function getPatientMedications(patientId) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/medications`);
    if (!res.ok) throw new Error("Failed to fetch medications");
    return res.json();
  }
  
  export async function getPatientAllergies(patientId) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/allergies`);
    if (!res.ok) throw new Error("Failed to fetch allergies");
    return res.json();
  }
  
  export async function getPatientVitalsLabs(patientId) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/vitals-labs`);
    if (!res.ok) throw new Error("Failed to fetch vitals/labs");
    return res.json();
  }

  export async function uploadPatientPhoto(patientId, file) {
    const formData = new FormData();
    formData.append("file", file);
  
    const res = await fetch(`${API_BASE}/patients/${patientId}/photo`, {
      method: "POST",
      body: formData,
    });
  
    if (!res.ok) {
      throw new Error("Failed to upload photo");
    }
    return res.json(); // updated Patient
  }
  
  export async function createEncounter(patientId, payload) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/encounters`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  
    if (!res.ok) {
      throw new Error("Failed to create encounter");
    }
    return res.json();
  }
  
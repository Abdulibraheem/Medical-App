import { useState, useEffect, useRef } from "react";
import {
  searchPatients,
  getPatientSummary,
  getPatientEncounters,
  getPatientMedications,
  getPatientAllergies,
  getPatientVitalsLabs,
  createEncounter,
  uploadPatientPhoto, 
} from "./api";


function CameraCapture({ onCapture, onClose }) {
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const [facingMode, setFacingMode] = useState("user"); // 'user' (front) or 'environment' (back)
    const [error, setError] = useState("");
  
    useEffect(() => {
      async function startCamera() {
        setError("");
  
        // stop previous stream if any
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
  
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode },
          });
          streamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.play();
          }
        } catch (err) {
          console.error(err);
          setError(
            "Unable to access camera. Check permissions or try a different device."
          );
        }
      }
  
      startCamera();
  
      // cleanup on unmount
      return () => {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
        }
      };
    }, [facingMode]);
  
    function handleCaptureClick() {
      const video = videoRef.current;
      if (!video) return;
  
      const canvas = document.createElement("canvas");
      const width = video.videoWidth || 640;
      const height = video.videoHeight || 480;
      canvas.width = width;
      canvas.height = height;
  
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, width, height);
  
      canvas.toBlob(
        (blob) => {
          if (!blob) return;
          const file = new File([blob], "camera_capture.jpg", {
            type: "image/jpeg",
          });
          onCapture(file);
        },
        "image/jpeg",
        0.9
      );
    }
  
    return (
      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: 6,
          padding: 8,
          backgroundColor: "#f9fafb",
        }}
      >
        <div
          style={{
            marginBottom: 6,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: 13, fontWeight: 600 }}>
            Camera capture (beta)
          </span>
          <button
            type="button"
            onClick={onClose}
            style={{ fontSize: 11, padding: "2px 6px" }}
          >
            Close
          </button>
        </div>
  
        <div style={{ marginBottom: 6 }}>
          <button
            type="button"
            onClick={() => setFacingMode("user")}
            style={{ fontSize: 11, padding: "3px 6px", marginRight: 4 }}
          >
            Front camera
          </button>
          <button
            type="button"
            onClick={() => setFacingMode("environment")}
            style={{ fontSize: 11, padding: "3px 6px" }}
          >
            Back camera
          </button>
        </div>
  
        {error && (
          <p style={{ color: "red", fontSize: 11, marginBottom: 6 }}>{error}</p>
        )}
  
        <div
          style={{
            width: 240,
            height: 180,
            background: "#000",
            marginBottom: 6,
          }}
        >
          <video
            ref={videoRef}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>
  
        <button
          type="button"
          onClick={handleCaptureClick}
          style={{ fontSize: 12, padding: "4px 8px" }}
        >
          Capture &amp; Use Photo
        </button>
      </div>
    );
  }

function App() {

  // Auth state (purely front-end)
  const [loginRole, setLoginRole] = useState("Field doctor");
  const [staffToken, setStaffToken] = useState(null);
  const [staffRole, setStaffRole] = useState("");

  // Patient/Search state
  const [name, setName] = useState("");
  const [dob, setDob] = useState("");
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [summary, setSummary] = useState(null);
  const [encounters, setEncounters] = useState([]);
  const [medications, setMedications] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [vitalsLabs, setVitalsLabs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("summary"); // summary | encounters | meds | vitals


  // New encounter form state
  const [newEncounterType, setNewEncounterType] = useState("A&E");
  const [newEncounterComplaint, setNewEncounterComplaint] = useState("");
  const [newEncounterDoctor, setNewEncounterDoctor] = useState("");


  const canEditClinical =
    staffRole === "Field doctor" || staffRole === "Hospital admin";
  const isPolicyMaker = staffRole === "Policy maker";

  // Photo upload state
  const [photoFile, setPhotoFile] = useState(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [showCamera, setShowCamera] = useState(false);


  function handleLogin(e) {
    e.preventDefault();
    // For now, just mark the user as logged in with the chosen role
    setStaffToken("demo-token");
    setStaffRole(loginRole);
  }

  async function handleSearch(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setSelectedPatient(null);
    setSummary(null);
    setEncounters([]);
    setMedications([]);
    setAllergies([]);
    setVitalsLabs([]);
    setActiveTab("summary");

    try {
      const results = await searchPatients(name.trim(), dob.trim());
      setPatients(results);
      if (results.length === 0) setError("No patients found");
    } catch (err) {
      console.error(err);
      setError("Error searching patients");
    } finally {
      setLoading(false);
    }
  }

  async function loadDetails(patient) {
    setSelectedPatient(patient);
    setLoading(true);
    setError("");
    setActiveTab("summary");

    try {
      const [s, e, meds, alls, vitLabs] = await Promise.all([
        getPatientSummary(patient.patient_id),
        getPatientEncounters(patient.patient_id),
        getPatientMedications(patient.patient_id),
        getPatientAllergies(patient.patient_id),
        getPatientVitalsLabs(patient.patient_id),
      ]);
      setSummary(s);
      setEncounters(e);
      setMedications(meds);
      setAllergies(alls);
      setVitalsLabs(vitLabs);
    } catch (err) {
      console.error(err);
      setError("Error loading patient details");
    } finally {
      setLoading(false);
    }
  }


  async function handlePhotoUpload(fileOverride) {
    const fileToUse = fileOverride || photoFile;
    if (!selectedPatient || !fileToUse) return;

    if (!canEditClinical) {
      alert("This role has read-only access and cannot change photos.");
      return;
    }

    try {
      setUploadingPhoto(true);

      // Upload photo
      await uploadPatientPhoto(selectedPatient.patient_id, fileToUse);

      // Refresh summary to pick up new photo_path
      const freshSummary = await getPatientSummary(selectedPatient.patient_id);
      setSummary(freshSummary);

      if (!fileOverride) {
        setPhotoFile(null);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to upload photo");
    } finally {
      setUploadingPhoto(false);
    }
  }

  async function handleCreateEncounter(e) {
    e.preventDefault();

    if (!canEditClinical) {
        alert("This role has read-only access and cannot add encounters.");
        return;
      }

    if (!selectedPatient) return;
    if (!newEncounterComplaint.trim()) {
      alert("Enter presenting complaint");
      return;
    }
  
    try {
      await createEncounter(selectedPatient.patient_id, {
        encounter_type: newEncounterType,
        presenting_complaint: newEncounterComplaint,
        doctor_name: newEncounterDoctor || null,
      });
  
      // Refresh encounters
      const updated = await getPatientEncounters(selectedPatient.patient_id);
      setEncounters(updated);
  
      // Reset form
      setNewEncounterComplaint("");
      setNewEncounterDoctor("");
      setNewEncounterType("A&E");
    } catch (error) {
      console.error(error);
      alert("Failed to add encounter");
    }
  }

  const tabButtonStyle = (tab) => ({
    padding: "6px 12px",
    marginRight: 8,
    borderRadius: 4,
    border: "1px solid #ccc",
    backgroundColor: activeTab === tab ? "#1d4ed8" : "#f3f4f6",
    color: activeTab === tab ? "#fff" : "#111",
    cursor: "pointer",
    fontSize: 14,
  });

  // ---------- If not logged in, show role-based login screen ----------
  if (!staffToken) {
    return (
      <div
        style={{
          padding: 20,
          fontFamily: "Arial, sans-serif",
          color: "#111",
          maxWidth: 420,
          margin: "40px auto",
          border: "1px solid #ddd",
          borderRadius: 8,
          backgroundColor: "#fff",
        }}
      >
        <h1 style={{ marginBottom: 10 }}>Clinic Access</h1>
        <p style={{ marginBottom: 16, fontSize: 14, color: "#555" }}>
          Choose how you&apos;re accessing the system:
        </p>

        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: 12 }}>
            <label
              style={{
                display: "block",
                marginBottom: 6,
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Select role
            </label>
            <select
              value={loginRole}
              onChange={(e) => setLoginRole(e.target.value)}
              style={{ width: "100%", padding: 8 }}
            >
              <option value="Field doctor">Field doctor</option>
              <option value="Policy maker">Policy maker</option>
              <option value="Hospital admin">Hospital admin</option>
            </select>
          </div>

          <button
            type="submit"
            style={{ padding: "8px 15px", width: "100%", marginTop: 4 }}
          >
            Continue
          </button>
        </form>
      </div>
    );
  }


  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif", color: "#111" }}>
  
      {/* ---- TOP HEADER WITH ROLE + LOGOUT ---- */}
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h1 style={{ marginBottom: 10 }}>A&amp;E Patient Lookup</h1>
  
        <div style={{ textAlign: "right", fontSize: 13 }}>
          <div>Logged in as: {staffRole}</div>
  
          <button
            type="button"
            onClick={() => {
              setStaffToken(null);
              setStaffRole("");
              setPatients([]);
              setSelectedPatient(null);
              setSummary(null);
            }}
            style={{
              marginTop: 4,
              padding: "4px 8px",
              fontSize: 12,
              borderRadius: 4,
            }}
          >
            Logout
          </button>
        </div>
      </div> 

      <form
        onSubmit={handleSearch}
        style={{ marginBottom: 20, display: "flex", gap: 10 }}
      >
        <input
          type="text"
          placeholder="Search by name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ padding: 8, flex: 1 }}
        />
        <input
          type="text"
          placeholder="DOB: YYYY-MM-DD"
          value={dob}
          onChange={(e) => setDob(e.target.value)}
          style={{ padding: 8, width: 160 }}
        />
        <button type="submit" style={{ padding: "8px 15px" }}>
          {loading ? "Working..." : "Search"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ display: "flex", gap: 30, alignItems: "flex-start" }}>
        {/* Left: search results */}
        <div style={{ flex: 1 }}>
          <h2>Results</h2>
          {patients.length === 0 && !loading && <p>No patients loaded.</p>}
          {patients.map((p) => (
            <div
              key={p.patient_id}
              onClick={() => loadDetails(p)}
              style={{
                border: "1px solid #ccc",
                padding: 10,
                marginBottom: 10,
                cursor: "pointer",
                background:
                  selectedPatient?.patient_id === p.patient_id ? "#eef" : "#fff",
              }}
            >
              <strong>
                {p.first_name} {p.last_name}
              </strong>
              <br />
              DOB: {p.date_of_birth}
              <br />
              Phone: {p.phone_number}
            </div>
          ))}
        </div>

        {/* Right: patient details with tabs */}
        <div style={{ flex: 1 }}>
          <h2>Patient Details</h2>

          {!selectedPatient && <p>Select a patient to view details.</p>}

          {selectedPatient && (
            <>
              {/* Tabs */}
              <div style={{ marginBottom: 10 }}>
                <button
                  type="button"
                  style={tabButtonStyle("summary")}
                  onClick={() => setActiveTab("summary")}
                >
                  Summary
                </button>
                <button
                  type="button"
                  style={tabButtonStyle("encounters")}
                  onClick={() => setActiveTab("encounters")}
                >
                  Encounters
                </button>
                <button
                  type="button"
                  style={tabButtonStyle("meds")}
                  onClick={() => setActiveTab("meds")}
                >
                  Meds &amp; Allergies
                </button>
                <button
                  type="button"
                  style={tabButtonStyle("vitals")}
                  onClick={() => setActiveTab("vitals")}
                >
                  Vitals &amp; Labs
                </button>
              </div>

              {/* Tab content */}
              <div
                style={{
                  border: "1px solid #ddd",
                  borderRadius: 6,
                  padding: 12,
                  backgroundColor: "#fff",
                }}
              >
                {activeTab === "summary" && summary && (
                  <div>
                    <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
                      {/* Photo column */}
                      <div>
                        {summary.photo_path ? (
                          <img
                            src={`http://127.0.0.1:8000/${summary.photo_path}`}
                            alt="Patient"
                            style={{
                              width: 120,
                              height: 120,
                              objectFit: "cover",
                              borderRadius: "8px",
                              border: "1px solid #ccc",
                            }}
                          />
                        ) : (
                          <div
                            style={{
                              width: 120,
                              height: 120,
                              borderRadius: "8px",
                              border: "1px solid #ccc",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: 12,
                              color: "#666",
                            }}
                           >
                            No photo
                          </div>
                        )}

                        {/* Upload controls - only for Field doctor & Admin */}
                        {canEditClinical && (
                          <div style={{ marginTop: 8 }}>
                            <input
                              type="file"
                              accept="image/*"
                              onChange={(e) => setPhotoFile(e.target.files?.[0] || null)}
                              style={{ marginBottom: 4, fontSize: 12 }}
                            />
                            <br />
                            <button
                              type="button"
                              onClick={() => handlePhotoUpload()}
                              disabled={!photoFile || uploadingPhoto}
                              style={{ padding: "4px 10px", fontSize: 12, marginBottom: 4 }}
                            >
                              {uploadingPhoto ? "Uploading..." : "Upload Photo"}
                            </button>

                            <br />

                            <button
                              type="button"
                              onClick={() => setShowCamera(true)}
                              style={{ padding: "4px 10px", fontSize: 12, marginTop: 2 }}
                            >
                              Open Camera
                            </button>

                            {showCamera && (
                              <div style={{ marginTop: 8 }}>
                                <CameraCapture
                                  onCapture={(file) => {
                                    // Upload immediately using captured file
                                    handlePhotoUpload(file);
                                    setShowCamera(false);
                                  }}
                                  onClose={() => setShowCamera(false)}
                                />
                              </div>
                            )}
                          </div>
                        )}

                        {/* Policy maker info */}
                        {isPolicyMaker && (
                          <p
                            style={{
                              marginTop: 8,
                              fontSize: 11,
                              color: "#777",
                              fontStyle: "italic",
                              maxWidth: 140,
                            }}
                           >
                            Policy maker role: photo is view-only.
                          </p>
                        )}
                      </div>

                    {/* Text info column */}
                    <div>
                        <h3>
                          {summary.first_name} {summary.last_name}
                        </h3>
                        <p>
                          DOB: {summary.date_of_birth}
                          <br />
                          Sex: {summary.sex || "N/A"}
                          <br />
                          Address: {summary.address || "N/A"}
                        </p>

                        <h4>Key Medical History</h4>
                        <p>
                          <strong>Conditions:</strong>{" "}
                          {summary.active_conditions || "None recorded"}
                          <br />
                          <strong>Medications:</strong>{" "}
                          {summary.active_medications || "None recorded"}
                          <br />
                          <strong>Allergies:</strong>{" "}
                          {summary.active_allergies || "None recorded"}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === "encounters" && (
                  <div>
                    <h3>
                      Encounters for {selectedPatient.first_name}{" "}
                      {selectedPatient.last_name}
                    </h3>

                    {/* Role-based behaviour */}
                    {canEditClinical ? (
                      // ✅ Field doctor & Hospital admin: show form
                      <form
                        onSubmit={handleCreateEncounter}
                        style={{
                          border: "1px solid #eee",
                          padding: 8,
                          marginBottom: 12,
                          borderRadius: 4,
                          backgroundColor: "#f9fafb",
                        }}
                      >
                        <div style={{ marginBottom: 6 }}>
                          <label style={{ fontSize: 13 }}>
                            Type:&nbsp;
                            <select
                              value={newEncounterType}
                              onChange={(e) => setNewEncounterType(e.target.value)}
                            >
                              <option value="A&E">A&amp;E</option>
                              <option value="OPD">OPD</option>
                              <option value="Ward">Ward</option>
                              <option value="Clinic">Clinic</option>
                            </select>
                          </label>
                        </div>

                        <div style={{ marginBottom: 6 }}>
                          <textarea
                            placeholder="Presenting complaint"
                            value={newEncounterComplaint}
                            onChange={(e) => setNewEncounterComplaint(e.target.value)}
                            rows={3}
                            style={{ width: "100%", padding: 6, fontSize: 13 }}
                        />
                        </div>

                        <div style={{ marginBottom: 6 }}>
                          <input
                            type="text"
                            placeholder="Doctor / clinician name (optional)"
                            value={newEncounterDoctor}
                            onChange={(e) => setNewEncounterDoctor(e.target.value)}
                            style={{ width: "100%", padding: 6, fontSize: 13 }}
                          />
                        </div>

                        <button
                          type="submit"
                          style={{ padding: "4px 10px", fontSize: 13 }}
                        >
                          Add Encounter
                        </button>
                      </form>
                    ) : (
                    // ❌ Policy maker: read-only
                    <p
                      style={{
                        fontSize: 13,
                        color: "#666",
                        marginBottom: 12,
                        fontStyle: "italic",
                        }}
                       >
                        This role has read-only access. Encounters can be viewed but not
                        modified.
                      </p>
                    )}

                    {/* Existing encounters list (everyone can see) */}
                    {encounters.length === 0 && <p>No encounters recorded.</p>}
                    {encounters.map((enc) => (
                      <div
                        key={enc.encounter_id}
                        style={{
                          marginBottom: 10,
                          paddingBottom: 8,
                          borderBottom: "1px solid #eee",
                        }}
                       >
                        <strong>{enc.encounter_date}</strong> ({enc.encounter_type})
                        <br />
                        Complaint: {enc.presenting_complaint}
                      </div>
                    ))}
                 </div>
               )}

                {activeTab === "meds" && (
                  <div>
                    <h3>Meds &amp; Allergies</h3>

                    <h4>Medications</h4>
                    {medications.length === 0 && (
                      <p>No medications recorded.</p>
                    )}
                    {medications.map((m) => (
                      <div key={m.medication_id} style={{ marginBottom: 8 }}>
                        <strong>{m.drug_name}</strong>{" "}
                        {m.dose && <span>({m.dose})</span>}
                        <br />
                        {m.route && <span>Route: {m.route} · </span>}
                        {m.frequency && <span>Freq: {m.frequency}</span>}
                        <br />
                        {m.start_date && <span>From: {m.start_date} </span>}
                        {m.end_date && <span> to {m.end_date}</span>}
                        {!m.is_active && <span> · (Stopped)</span>}
                      </div>
                    ))}

                    <h4>Allergies</h4>
                    {allergies.length === 0 && <p>No allergies recorded.</p>}
                    {allergies.map((a) => (
                      <div key={a.allergy_id} style={{ marginBottom: 8 }}>
                        <strong>{a.allergen}</strong>{" "}
                        {a.severity && <span>({a.severity})</span>}
                        <br />
                        {a.reaction && <span>Reaction: {a.reaction}</span>}
                        <br />
                        {a.noted_date && <span>Noted: {a.noted_date}</span>}
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === "vitals" && (
                  <div>
                    <h3>Vitals &amp; Labs</h3>
                    {vitalsLabs.length === 0 && (
                      <p>No vitals or lab results recorded.</p>
                    )}
                    {vitalsLabs.map((item) => (
                      <div
                        key={item.encounter_id}
                        style={{
                          marginBottom: 12,
                          paddingBottom: 8,
                          borderBottom: "1px solid #eee",
                        }}
                      >
                        <strong>{item.encounter_date}</strong> (
                        {item.encounter_type})<br />
                        Complaint: {item.presenting_complaint}
                        {item.vitals && (
                          <p style={{ marginTop: 4 }}>
                            <em>Vitals:</em>{" "}
                            {item.vitals.systolic_bp &&
                              item.vitals.diastolic_bp && (
                                <>
                                  BP: {item.vitals.systolic_bp}/
                                  {item.vitals.diastolic_bp} mmHg ·{" "}
                                </>
                              )}
                            {item.vitals.heart_rate &&
                              `HR: ${item.vitals.heart_rate} bpm · `}
                            {item.vitals.temperature_c &&
                              `Temp: ${item.vitals.temperature_c} °C · `}
                            {item.vitals.oxygen_saturation &&
                              `SpO₂: ${item.vitals.oxygen_saturation}%`}
                          </p>
                        )}
                        {item.lab_results && item.lab_results.length > 0 && (
                          <div style={{ marginTop: 4 }}>
                            <em>Lab Results:</em>
                            <ul>
                              {item.lab_results.map((lab) => (
                                <li key={lab.lab_result_id}>
                                  {lab.test_name}: {lab.result_value}{" "}
                                  {lab.units || ""}{" "}
                                  {lab.reference_range &&
                                    `(ref: ${lab.reference_range})`}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

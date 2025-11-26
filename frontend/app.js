const API_BASE =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "http://backend:8000";

const fileInput = document.getElementById("fileInput");
const resultBox = document.getElementById("result");
const summaryBox = document.getElementById("summary");
const countsBox = document.getElementById("counts");
const alertBox = document.getElementById("alertBox");
const spinner = document.getElementById("spinner");
const sendBtn = document.getElementById("sendBtn");

function setLoading(isLoading) {
  spinner.classList.toggle("d-none", !isLoading);
  sendBtn.disabled = isLoading;
}

function clearUI() {
  resultBox.textContent = "";
  summaryBox.textContent = "";
  countsBox.textContent = "";
  alertBox.classList.add("d-none");
  alertBox.textContent = "";
}

function showError(message) {
  alertBox.textContent = message;
  alertBox.classList.remove("d-none");
}

function showResult(data) {
  const samples = data.samples ?? "-";
  const separator = data.preprocessing?.separator ?? "?";
  const labelFlag = data.preprocessing?.label_column ?? "no";

  const activities = Array.isArray(data.predicted_labels)
    ? [...new Set(data.predicted_labels)].join(", ")
    : "n/a";

  summaryBox.textContent = `Ventanas: ${samples} | Actividades: ${activities} | Separador: ${separator} | Ultima columna: ${labelFlag}`;
  countsBox.innerHTML = renderCounts(data.predicted_labels);
  resultBox.textContent = JSON.stringify(data, null, 2);
}

function renderCounts(labels) {
  if (!Array.isArray(labels) || labels.length === 0) return "";

  const counts = labels.reduce((acc, label) => {
    acc[label] = (acc[label] || 0) + 1;
    return acc;
  }, {});

  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const dominant = entries[0] ? `${entries[0][0]} (${entries[0][1]})` : "n/a";

  const pills = entries
    .map(([label, count]) => `<span class="badge text-bg-light me-1 mb-1">${label}: ${count}</span>`)
    .join("");

  return `<div class="text-secondary">Actividad dominante: <strong>${dominant}</strong></div><div class="mt-1">${pills}</div>`;
}

async function sendFile() {
  clearUI();

  const file = fileInput.files[0];
  if (!file) {
    showError("Selecciona un archivo .log");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  setLoading(true);
  try {
    const response = await fetch(`${API_BASE}/detect`, {
      method: "POST",
      body: formData,
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      const detail = payload?.detail || `Error del servidor (${response.status})`;
      throw new Error(detail);
    }

    showResult(payload);
  } catch (error) {
    showError(error.message || "Error inesperado al procesar el archivo.");
  } finally {
    setLoading(false);
  }
}

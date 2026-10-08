const form = document.getElementById("transmission-form");
const result = document.getElementById("form-result");
const rows = document.getElementById("transmission-rows");
const health = document.getElementById("health");

function makeMessageId() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replaceAll("-", "");
  const random = Math.random().toString(36).slice(2, 8).toUpperCase();
  return `MSG-${date}-${random}`;
}

document.getElementById("message-id").value = makeMessageId();

async function checkHealth() {
  try {
    const response = await fetch("/health/ready");
    if (!response.ok) throw new Error("not ready");
    health.textContent = "Gateway ready";
    health.className = "health ready";
  } catch {
    health.textContent = "Gateway unavailable";
    health.className = "health failed";
  }
}

function statusBadge(status) {
  return `<span class="status status-${status.toLowerCase()}">${status}</span>`;
}

async function loadTransmissions() {
  try {
    const response = await fetch("/api/v1/transmissions?limit=25");
    const data = await response.json();
    if (!response.ok) throw new Error(data?.error?.message || "Unable to load data");
    if (!data.items.length) {
      rows.innerHTML = '<tr><td colspan="6">No transmissions yet.</td></tr>';
      return;
    }
    rows.innerHTML = data.items.map(item => `
      <tr data-message-id="${item.message_id}">
        <td><a href="/api/v1/transmissions/${item.message_id}" target="_blank">${item.message_id}</a></td>
        <td>${item.source_system} → ${item.target_system}</td>
        <td>${item.priority}</td>
        <td>${statusBadge(item.status)}</td>
        <td>${item.attempt_count}</td>
        <td>${new Date(item.updated_at).toLocaleTimeString()}</td>
      </tr>`).join("");
  } catch (error) {
    rows.innerHTML = `<tr><td colspan="6">${error.message}</td></tr>`;
  }
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  result.textContent = "Submitting…";
  result.className = "result";
  let payload;
  try {
    payload = JSON.parse(document.getElementById("payload").value);
  } catch {
    result.textContent = "Payload is not valid JSON.";
    result.className = "result error";
    return;
  }

  const body = {
    message_id: document.getElementById("message-id").value,
    schema_version: "1.0",
    source_system: document.getElementById("source-system").value,
    target_system: document.getElementById("target-system").value,
    priority: document.getElementById("priority").value,
    data_sensitivity: "CONTROLLED",
    payload_format: "JSON",
    payload
  };

  try {
    const response = await fetch("/api/v1/transmissions", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data?.error?.message || "Request failed");
    result.textContent = `${data.message_id} accepted with status ${data.status}.`;
    result.className = "result success";
    document.getElementById("message-id").value = makeMessageId();
    await loadTransmissions();
  } catch (error) {
    result.textContent = error.message;
    result.className = "result error";
  }
});

document.getElementById("refresh").addEventListener("click", loadTransmissions);
checkHealth();
loadTransmissions();
setInterval(loadTransmissions, 2000);

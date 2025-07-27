const room_id = document.body.dataset.room_id;
let charChart = null;

require.config({
  paths: {
    vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs",
  },
});

let editorsMap = {};
let staticEditorsMap = {}; // For template-generated editors
let userColors = [
  "#3a86ff",
  "#8338ec",
  "#ff006e",
  "#fb5607",
  "#ffbe0b",
  "#06d6a0",
];
let colorIndex = 0;
let connectionStatusEl = document.getElementById("connection-status");
let userCountEl = document.getElementById("user-count");
let connectionIndicatorEl = document.getElementById("connection-indicator");
let sessionTimeEl = document.getElementById("session-time");

// Monaco Editor configuration
const editorConfig = {
  language: "javascript", // Default language
  theme: "vs-dark",
  automaticLayout: true,
  readOnly: true, // Set to false if you want editable editors
  fontSize: 14,
  fontFamily: "JetBrains Mono, Consolas, Monaco, monospace",
  lineNumbers: "on",
  minimap: { enabled: true },
  scrollBeyondLastLine: false,
  wordWrap: "on",
};

// Function to create editor for static template candidates
function createEditor(userid, code_content) {
  const container = document.getElementById(`editor-${userid}`);
  const loadingState = container.querySelector(".loading-state");

  if (!container) {
    console.error(`Editor container not found for user ${userid}`);
    return;
  }

  try {
    const editor = monaco.editor.create(container, {
      ...editorConfig,
      value: code_content,
    });

    staticEditorsMap[userid] = editor;

    if (loadingState) {
      loadingState.style.display = "none";
    }

    console.log(`Static editor created for user ${userid}`);
  } catch (error) {
    console.error(`Failed to create static editor for user ${userid}:`, error);
    if (loadingState) {
      loadingState.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="color: #ff4757; font-size: 1.5rem;"></i>
            <span style="color: #ff4757;">Failed to load editor</span>
          `;
    }
  }
}

const startat = document.body.dataset.startat; // e.g. "14:00"
const endat = document.body.dataset.endat; // e.g. "16:00"

// Convert time strings to Date objects (today's date)
function toTodayTime(timeStr) {
  const now = new Date();
  const [hours, minutes] = timeStr.split(":").map(Number);
  const date = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
    hours,
    minutes,
    0
  );
  return date;
}

const sessionStartTime = toTodayTime(startat);
const sessionEndTime = toTodayTime(endat);
function updateSessionTime() {
  const now = new Date();
  const elapsedMs = now - sessionStartTime;
  const remainingMs = sessionEndTime - now;

  // Elapsed
  // const elapsedSeconds = Math.floor(elapsedMs / 1000);
  // const elapsedMin = Math.floor(elapsedSeconds / 60);
  // const elapsedSec = elapsedSeconds % 60;

  // Remaining
  const remainingSeconds = Math.max(0, Math.floor(remainingMs / 1000));
  const remainingMin = Math.floor(remainingSeconds / 60);
  const remainingSec = remainingSeconds % 60;

  // Update timer
  sessionTimeEl.textContent =
    // `Elapsed: ${elapsedMin.toString().padStart(2, "0")}:${elapsedSec
    //   .toString()
    //   .padStart(2, "0")} | ` +
    `Remaining: ${remainingMin.toString().padStart(2, "0")}:${remainingSec
      .toString()
      .padStart(2, "0")}`;

  // If time is up
  if (remainingMs <= 0) {
    clearInterval(timerInterval);
    alert("Time is up! Test will now end.");
    // Optionally auto-submit the form or redirect:
    // document.getElementById("test-form").submit();
    // window.location.href = "/test-ended/";
  }
}
setInterval(updateSessionTime, 1000);

function updateConnectionStatus(status, message) {
  const badge = connectionStatusEl.querySelector(".status-badge");
  badge.className = `status-badge status-${status}`;
  badge.innerHTML = `
        <i class="fas ${
          status === "connected"
            ? "fa-check-circle"
            : status === "disconnected"
            ? "fa-times-circle"
            : "fa-circle-notch fa-spin"
        }"></i>
        <span>${message}</span>
      `;
  connectionIndicatorEl.textContent = message;

  // Hide badge after 3 seconds
  badge.style.display = "inline-block";
  clearTimeout(updateConnectionStatus._hideTimeout);
  updateConnectionStatus._hideTimeout = setTimeout(() => {
    badge.style.display = "none";
  }, 3000);
}

function getUserInitials(userId) {
  return userId.substring(0, 2).toUpperCase();
}

function getUserColor(userId) {
  if (!getUserColor.colorMap) getUserColor.colorMap = {};
  if (!getUserColor.colorMap[userId]) {
    getUserColor.colorMap[userId] = userColors[colorIndex % userColors.length];
    colorIndex++;
  }
  return getUserColor.colorMap[userId];
}

function hideFinishConfirm() {
  const block = document.getElementById("finish-confirm");
  if (block) {
    block.style.display = "none";
  }
}

function showTypingModal(userId, userName) {
  const modal = document.getElementById("typingModal");
  const title = document.getElementById("typingModalTitle");

  title.textContent = `Typing Statistics for @${userName}`;
  modal.style.display = "flex";

  // Fetch statistics from backend
  fetch("/get-statistic/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // 'X-CSRFToken': csrftoken  // If you use CSRF protection
    },
    body: JSON.stringify({
      user: userId,
      room_id: room_id,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      console.log(
        "time label and char deltas are",
        data.time_labels,
        data.char_deltas
      );
      console.log(
        "time label and char deltas are",
        data.time_labels,
        data.char_deltas[0]
      );

      updateChart(data.time_labels, data.char_deltas[0]);
    })
    .catch((error) => {
      console.error("Error fetching statistics:", error);
      // Show dummy data on error
      updateChart(["10s", "20s", "30s", "40s", "50s"], [10, 25, 15, 30, 20]);
    });
}

function hideTypingModal() {
  document.getElementById("typingModal").style.display = "none";
  // Clean up chart when modal is closed
  if (charChart) {
    charChart.destroy();
    charChart = null;
  }
}

function updateChart(labels, data) {
  const ctx = document.getElementById("charChart").getContext("2d");

  // Destroy previous chart if it exists
  if (charChart) {
    charChart.destroy();
  }

  charChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Characters Typed per 10s",
          data: data,
          borderColor: "rgb(75, 192, 192)",
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderWidth: 2,
          tension: 0.1,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Characters Typed",
          },
        },
        x: {
          title: {
            display: true,
            text: "Time",
          },
        },
      },
    },
  });
}

document
  .getElementById("finishtest")
  ?.addEventListener("submit", async function (e) {
    e.preventDefault();
    try {
      const response = await fetch("/finish-lab-test/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams(new FormData(e.target)),
      });

      if (response.ok) {
        const data = await response.json();
        window.location.assign(`/channel/${data.room_id}`);
      } else {
        console.error("Error occurred:", response.status, response.statusText);
        alert("An error occurred while finishing the lab test.");
      }
    } catch (error) {
      console.error("Network error:", error);
      alert("A network error occurred. Please try again.");
    }
  });

function toggleForm() {
  const form = document.getElementById("questionForm");
  if (form) {
    form.style.display = form.style.display === "none" ? "block" : "none";
  }
}

document
  .getElementById("labtestform")
  ?.addEventListener("submit", async function (e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    const response = await fetch("/manage-lab-test/", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      window.location.reload();
    } else {
      console.log("error occurred");
    }
  });

// Initialize Monaco Editor and WebSocket
require(["vs/editor/editor.main"], function () {
  // Initialize static editors from template
  const staticEditorContainers = document.querySelectorAll('[id^="editor-"]');
  staticEditorContainers.forEach((container) => {
    const userId = container.id.replace("editor-", "");
    const code_content = container.dataset.code_content;
    createEditor(userId, code_content);
  });

  // Update initial user count
  userCountEl.textContent = staticEditorContainers.length;

  const wrapper = document.getElementById("editors-wrapper");
  const emptyState = document.getElementById("empty-state");

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(
    `${protocol}://${window.location.host}/ws/test-monitor/${room_id}/`
  );

  socket.onopen = () => {
    console.log("WebSocket connected to", socket.url);
    updateConnectionStatus("connected", "Connected");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const user_id = data.user_id;
    const content = data.content;
    const user_name = data.user_name;
    const user_profile = data.user_profile;

    if (Object.keys(editorsMap).length === 0 && emptyState) {
      emptyState.style.display = "none";
    }

    if (staticEditorsMap[user_id]) {
      const model = staticEditorsMap[user_id].getModel();
      if (model) {
        model.setValue(content || "");
      }
      return;
    }

    // If this user does not have a dynamic editor yet, create one
    if (!editorsMap[user_id]) {
      const col = document.createElement("div");
      col.className = "col-lg-6 col-12";

      const userColor = getUserColor(user_id);

      col.innerHTML = `
            <div class="editor-card">
              <div class="editor-header">
                <div class="user-info">
                  <div class="user-avatar" style="background-color: ${userColor}; overflow: hidden">
                    <img src="${user_profile}" height="30" alt="${user_name}">
                  </div>
                  <div class="user-details">
                    <h6>@${user_name}</h6>
                    <small>JavaScript Editor</small>
                  </div>
                </div>
                <div class="editor-status">
                  <button onclick="showTypingModal('${user_id}', '${user_name}')" 
                    style="background: none; border: none; color: aliceblue; cursor: pointer;">
                    <i class="fa-solid fa-chart-line"></i>
                  </button>
                </div>
              </div>
              <div class="editor-container" id="dynamic-editor-${user_id}">
                <div class="loading-state">
                  <div class="loading-spinner"></div>
                  <span>Initializing editor...</span>
                </div>
              </div>
            </div>
          `;

      wrapper.appendChild(col);

      // Create new Monaco editor
      setTimeout(() => {
        const container = document.getElementById(`dynamic-editor-${user_id}`);
        const loadingState = container.querySelector(".loading-state");

        try {
          const newEditor = monaco.editor.create(container, {
            ...editorConfig,
            value: content || "",
          });

          editorsMap[user_id] = newEditor;
          loadingState.style.display = "none";

          // Update user count (static + dynamic editors)
          userCountEl.textContent =
            Object.keys(staticEditorsMap).length +
            Object.keys(editorsMap).length;
        } catch (error) {
          console.error("Failed to create dynamic editor:", error);
          loadingState.innerHTML = `
                <i class="fas fa-exclamation-triangle" style="color: #ff4757; font-size: 1.5rem;"></i>
                <span style="color: #ff4757;">Failed to load editor</span>
              `;
        }
      }, 500);
    } else {
      // Apply changes to existing dynamic editor
      const model = editorsMap[user_id].getModel();
      if (model) {
        model.setValue(content || "");
      }
    }
  };

  socket.onclose = () => {
    console.warn("WebSocket connection closed.");
    updateConnectionStatus("disconnected", "Disconnected");
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    updateConnectionStatus("disconnected", "Error");
  };
});

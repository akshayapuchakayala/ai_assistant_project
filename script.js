const promptLibrary = JSON.parse(document.getElementById("promptLibraryData").textContent);

const COLOR_VARS = {
  blue: { accent: "--blue", tint: "--blue-tint" },
  teal: { accent: "--teal", tint: "--teal-tint" },
  magenta: { accent: "--magenta", tint: "--magenta-tint" },
  amber: { accent: "--amber", tint: "--amber-tint" },
};

let state = {
  function: null,
  style: null,
  lastResponse: null,
};

const tabsEl = document.getElementById("functionTabs");
const styleCardsEl = document.getElementById("styleCards");
const inputEl = document.getElementById("userInput");
const generateBtn = document.getElementById("generateBtn");
const errorHint = document.getElementById("errorHint");
const promptInspector = document.getElementById("promptInspector");
const responseBox = document.getElementById("responseBox");
const feedbackRow = document.getElementById("feedbackRow");
const feedbackConfirm = document.getElementById("feedbackConfirm");
const dashboardGrid = document.getElementById("dashboardGrid");

function setAccent(colorName) {
  const vars = COLOR_VARS[colorName] || COLOR_VARS.blue;
  const root = document.documentElement;
  root.style.setProperty("--accent", `var(${vars.accent})`);
  root.style.setProperty("--accent-tint", `var(${vars.tint})`);
}

function selectFunction(key) {
  state.function = key;
  state.style = promptLibrary[key].styles[0].id;
  setAccent(promptLibrary[key].color);

  [...tabsEl.children].forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.function === key);
  });

  inputEl.value = "";
  inputEl.placeholder = promptLibrary[key].placeholder;
  renderStyleCards();
  resetOutput();
}

function renderStyleCards() {
  const fn = promptLibrary[state.function];
  styleCardsEl.innerHTML = "";
  fn.styles.forEach((style) => {
    const card = document.createElement("button");
    card.className = "style-card" + (style.id === state.style ? " selected" : "");
    card.innerHTML = `<strong>${style.name}</strong><span>${style.description}</span>`;
    card.addEventListener("click", () => {
      state.style = style.id;
      renderStyleCards();
    });
    styleCardsEl.appendChild(card);
  });
}

function resetOutput() {
  errorHint.textContent = "";
  promptInspector.textContent = 'Pick a style and click "Generate response" to see the exact prompt here.';
  responseBox.innerHTML = '<p class="placeholder-text">The assistant\'s answer will appear here.</p>';
  feedbackRow.hidden = true;
  feedbackConfirm.textContent = "";
  [...feedbackRow.querySelectorAll(".feedback-btn")].forEach((b) => b.classList.remove("chosen"));
}

tabsEl.addEventListener("click", (e) => {
  const btn = e.target.closest(".tab");
  if (btn) selectFunction(btn.dataset.function);
});

generateBtn.addEventListener("click", async () => {
  const text = inputEl.value.trim();
  errorHint.textContent = "";
  if (!text) {
    errorHint.textContent = "Please enter some input text first.";
    return;
  }

  generateBtn.disabled = true;
  generateBtn.textContent = "Generating...";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ function: state.function, style: state.style, input: text }),
    });
    const data = await res.json();

    if (!res.ok) {
      errorHint.textContent = data.error || "Something went wrong.";
      return;
    }

    promptInspector.textContent = data.prompt_used;
    responseBox.textContent = data.response;
    state.lastResponse = { ...state, input: text, response: data.response };

    feedbackRow.hidden = false;
    feedbackConfirm.textContent = "";
    [...feedbackRow.querySelectorAll(".feedback-btn")].forEach((b) => b.classList.remove("chosen"));
  } catch (err) {
    errorHint.textContent = "Network error: " + err.message;
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Generate response →";
  }
});

feedbackRow.addEventListener("click", async (e) => {
  const btn = e.target.closest(".feedback-btn");
  if (!btn || !state.lastResponse) return;

  [...feedbackRow.querySelectorAll(".feedback-btn")].forEach((b) => b.classList.remove("chosen"));
  btn.classList.add("chosen");

  const helpful = btn.dataset.helpful === "true";
  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        function: state.lastResponse.function,
        style: state.lastResponse.style,
        input: state.lastResponse.input,
        response: state.lastResponse.response,
        helpful,
      }),
    });
    const data = await res.json();
    feedbackConfirm.textContent = "Thanks — feedback recorded.";
    renderDashboard(data.stats);
  } catch (err) {
    feedbackConfirm.textContent = "Couldn't save feedback.";
  }
});

async function loadDashboard() {
  try {
    const res = await fetch("/api/feedback/stats");
    const stats = await res.json();
    renderDashboard(stats);
  } catch (err) {
    dashboardGrid.innerHTML = '<p class="placeholder-text">Feedback stats unavailable.</p>';
  }
}

function renderDashboard(stats) {
  dashboardGrid.innerHTML = "";
  Object.entries(promptLibrary).forEach(([key, fn]) => {
    const s = stats[key] || { total: 0, helpful: 0, rate: null };
    const vars = COLOR_VARS[fn.color] || COLOR_VARS.blue;
    const card = document.createElement("div");
    card.className = "dash-card";
    const rate = s.rate === null ? 0 : s.rate;
    const meta = s.total === 0 ? "No feedback yet" : `${s.helpful}/${s.total} helpful (${s.rate}%)`;
    card.innerHTML = `
      <h3>${fn.label}</h3>
      <div class="dash-bar-track"><div class="dash-bar-fill" style="width:${rate}%; background: var(${vars.accent})"></div></div>
      <div class="dash-meta">${meta}</div>
    `;
    dashboardGrid.appendChild(card);
  });
}

// init
const firstKey = Object.keys(promptLibrary)[0];
selectFunction(firstKey);
loadDashboard();

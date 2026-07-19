// Minimal chat client: POST to /api/chat and render both sides.

// --- Tiny self-contained Markdown renderer (no deps, no build step) --------
// The concierge replies in Markdown (headings, tables, code, lists). We escape
// first, then convert the handful of constructs it actually emits to HTML.

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Inline formatting on already-escaped text: code, links, bold, italic, URLs.
function renderInline(text) {
  const codes = [];
  text = text.replace(/`([^`]+)`/g, (_, c) => `%%%${codes.push(c) - 1}%%%`);
  text = text.replace(
    /\[([^\]]+)\]\((https?:[^)\s]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener">$1</a>'
  );
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>");
  text = text.replace(
    /(^|[\s(])((?:https?:\/\/)[^\s)]+)/g,
    '$1<a href="$2" target="_blank" rel="noopener">$2</a>'
  );
  return text.replace(/%%%(\d+)%%%/g, (_, i) => `<code>${codes[i]}</code>`);
}

const isTableSep = (l) =>
  /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(l);
const isSpecial = (l, next) =>
  /^\s*```/.test(l) ||
  /^#{1,6}\s+/.test(l) ||
  /^\s*[-*]\s+/.test(l) ||
  /^\s*\d+\.\s+/.test(l) ||
  /^\s*---+\s*$/.test(l) ||
  (l.includes("|") && next !== undefined && isTableSep(next));

function renderMarkdown(md) {
  const lines = escapeHtml(md).replace(/\r\n/g, "\n").split("\n");
  const parseRow = (l) =>
    l.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map((c) => c.trim());
  let html = "";
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (/^\s*```/.test(line)) {
      const buf = [];
      i++;
      while (i < lines.length && !/^\s*```\s*$/.test(lines[i])) buf.push(lines[i++]);
      i++;
      html += `<pre><code>${buf.join("\n")}</code></pre>`;
    } else if (line.includes("|") && isTableSep(lines[i + 1] ?? "")) {
      const headers = parseRow(line);
      i += 2;
      let body = "";
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        body += "<tr>" + parseRow(lines[i++]).map((c) => `<td>${renderInline(c)}</td>`).join("") + "</tr>";
      }
      html +=
        "<div class='table-wrap'><table><thead><tr>" +
        headers.map((h) => `<th>${renderInline(h)}</th>`).join("") +
        `</tr></thead><tbody>${body}</tbody></table></div>`;
    } else if (/^(#{1,6})\s+(.*)$/.test(line)) {
      const [, hashes, rest] = line.match(/^(#{1,6})\s+(.*)$/);
      const n = hashes.length;
      html += `<h${n}>${renderInline(rest)}</h${n}>`;
      i++;
    } else if (/^\s*---+\s*$/.test(line)) {
      html += "<hr>";
      i++;
    } else if (/^\s*[-*]\s+/.test(line)) {
      let items = "";
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i]))
        items += `<li>${renderInline(lines[i++].replace(/^\s*[-*]\s+/, ""))}</li>`;
      html += `<ul>${items}</ul>`;
    } else if (/^\s*\d+\.\s+/.test(line)) {
      let items = "";
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i]))
        items += `<li>${renderInline(lines[i++].replace(/^\s*\d+\.\s+/, ""))}</li>`;
      html += `<ol>${items}</ol>`;
    } else if (!line.trim()) {
      i++;
    } else {
      const para = [];
      while (i < lines.length && lines[i].trim() && !isSpecial(lines[i], lines[i + 1]))
        para.push(lines[i++]);
      html += `<p>${para.map(renderInline).join("<br>")}</p>`;
    }
  }
  return html;
}

const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("composer");
const inputEl = document.getElementById("input");
const sendEl = document.getElementById("send");

// One conversation id per page load.
const conversationId = crypto.randomUUID();

/** Append a message bubble and scroll into view. Returns the element. */
function addMessage(text, role) {
  const el = document.createElement("div");
  el.className = `msg msg--${role}`;
  el.textContent = text;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

async function sendMessage(text) {
  addMessage(text, "user");

  const pending = addMessage("", "assistant");
  pending.classList.add("msg--pending");
  const progress = document.createElement("div");
  progress.className = "progress";
  pending.appendChild(progress);
  setBusy(true);

  // Show a live progress line (status/tool). Marks the last row as active.
  const addProgress = (label) => {
    progress.querySelectorAll(".progress__item").forEach((el) =>
      el.classList.remove("progress__item--active")
    );
    const row = document.createElement("div");
    row.className = "progress__item progress__item--active";
    row.textContent = label;
    progress.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  };

  const finish = (event) => {
    pending.classList.remove("msg--pending");
    progress.remove();
    if (event.type === "done") {
      pending.classList.add("md");
      pending.innerHTML = renderMarkdown(event.reply);
    } else {
      pending.classList.add("msg--error");
      pending.textContent = event.message;
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;
  };

  try {
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, conversation_id: conversationId }),
    });
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finished = false;

    while (!finished) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sep;
      while ((sep = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);
        const dataLine = frame.split("\n").find((l) => l.startsWith("data:"));
        if (!dataLine) continue;

        const event = JSON.parse(dataLine.slice(5).trim());
        if (event.type === "status" || event.type === "tool") {
          addProgress(event.summary);
        } else if (event.type === "done" || event.type === "error") {
          finish(event);
          finished = true;
        }
      }
    }
  } catch (err) {
    pending.remove();
    addMessage(`Error: ${err.message}`, "error");
  } finally {
    setBusy(false);
  }
}

function setBusy(busy) {
  inputEl.disabled = busy;
  sendEl.disabled = busy;
  if (!busy) inputEl.focus();
}

formEl.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = "";
  sendMessage(text);
});

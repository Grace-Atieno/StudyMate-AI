// Change this if your backend runs elsewhere (and add the page's origin to ALLOWED_ORIGINS).
const API_URL = 'http://127.0.0.1:5000';
const MAX_BYTES = 5 * 1024 * 1024;

const form = document.getElementById('uploadForm');
const btn = document.getElementById('submitBtn');
const statusEl = document.getElementById('status');
const results = document.getElementById('results');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const file = document.getElementById('noteUpload').files[0];
  if (!file) return setStatus('Please select a file first.', true);
  if (file.size > MAX_BYTES) return setStatus('That file is over 5 MB.', true);

  const body = new FormData();
  body.append('file', file);
  btn.disabled = true;
  results.hidden = true;
  setStatus('Reading your notes… this can take a few seconds.');

  try {
    const res = await fetch(`${API_URL}/upload`, { method: 'POST', body });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Request failed.');
    render(data);
    setStatus('');
  } catch (err) {
    setStatus(err instanceof TypeError ? 'Could not reach the server. Is the backend running?' : err.message, true);
  } finally {
    btn.disabled = false;
  }
});

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.className = isError ? 'error' : '';
}

// All content is inserted with textContent, never innerHTML, so AI output can't inject markup.
function render({ summary, quiz }) {
  document.getElementById('summary').textContent = summary;
  const quizEl = document.getElementById('quiz');
  const scoreEl = document.getElementById('score');
  quizEl.replaceChildren();
  scoreEl.textContent = '';
  let answered = 0, correct = 0;

  quiz.forEach((q, i) => {
    const fs = document.createElement('fieldset');
    fs.className = 'card';
    const legend = document.createElement('legend');
    legend.textContent = `${i + 1}. ${q.question}`;
    fs.append(legend);
    const feedback = document.createElement('p');
    feedback.setAttribute('role', 'status');

    q.options.forEach((opt, j) => {
      const label = document.createElement('label');
      label.className = 'option';
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = `q${i}`;
      input.addEventListener('change', () => {
        if (fs.dataset.done) return;
        fs.dataset.done = '1';
        fs.querySelectorAll('input').forEach((el) => (el.disabled = true));
        answered++;
        const ok = j === q.answer;
        if (ok) correct++;
        feedback.textContent = ok ? '✅ Correct!' : `❌ Not quite. Answer: ${q.options[q.answer]}`;
        if (answered === quiz.length) scoreEl.textContent = `Score: ${correct} / ${quiz.length}`;
      });
      label.append(input, ' ', opt);
      fs.append(label);
    });
    fs.append(feedback);
    quizEl.append(fs);
  });
  results.hidden = false;
}

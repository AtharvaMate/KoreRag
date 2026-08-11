const API = '';
let token = localStorage.getItem('token');
let username = localStorage.getItem('username');
let tenant = localStorage.getItem('tenant');

function api(path, opts = {}) {
    const headers = { ...opts.headers };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (!(opts.body instanceof FormData)) headers['Content-Type'] = 'application/json';
    return fetch(API + path, { ...opts, headers });
}

function $(id) { return document.getElementById(id); }

function switchAuthTab(tab) {
    document.querySelectorAll('.auth-toggle-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    $('login-form').classList.toggle('hidden', tab !== 'login');
    $('register-form').classList.toggle('hidden', tab !== 'register');
    $('auth-error').textContent = '';
}

async function loadTenants() {
    const res = await api('/api/auth/tenants');
    const tenants = await res.json();
    const sel = $('reg-tenant');
    sel.innerHTML = tenants.map(t => `<option value="${t.slug}">${t.name}</option>`).join('');
}

async function handleLogin(e) {
    e.preventDefault();
    const res = await api('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username: $('login-user').value, password: $('login-pass').value }),
    });
    if (!res.ok) { $('auth-error').textContent = (await res.json()).detail; return; }
    const data = await res.json();
    setAuth(data);
}

async function handleRegister(e) {
    e.preventDefault();
    const res = await api('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username: $('reg-user').value, password: $('reg-pass').value, tenant: $('reg-tenant').value }),
    });
    if (!res.ok) { $('auth-error').textContent = (await res.json()).detail; return; }
    const data = await res.json();
    setAuth(data);
}

function setAuth(data) {
    token = data.token; username = data.username; tenant = data.tenant;
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('tenant', tenant);
    showApp();
}

function logout() {
    token = username = tenant = null;
    localStorage.clear();
    location.reload();
}

function showApp() {
    $('auth-screen').classList.add('hidden');
    $('app-screen').classList.remove('hidden');
    $('sb-tenant').textContent = tenant;
    $('sb-username').textContent = username;
    $('sb-avatar').textContent = username[0].toUpperCase();
    loadHistory();
    loadDocuments();
}

function switchTab(tab) {
    document.querySelectorAll('.sb-tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    $('panel-history').classList.toggle('hidden', tab !== 'history');
    $('panel-docs').classList.toggle('hidden', tab !== 'docs');
}

function toggleSidebar() {
    $('sidebar').classList.toggle('collapsed');
}

async function loadHistory() {
    const res = await api('/api/chat/history');
    if (!res.ok) return;
    const items = await res.json();
    const el = $('history-list');
    $('history-empty').classList.toggle('hidden', items.length > 0);
    el.innerHTML = items.map(m => {
        const d = new Date(m.created_at);
        const t = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        return `<div class="history-item" onclick="showHistoryItem('${esc(m.question)}','${esc(m.answer)}')">
            <div class="history-item-q">${esc(m.question)}</div>
            <div class="history-item-t">${t}</div>
        </div>`;
    }).join('');
}

function showHistoryItem(q, a) {
    clearMessages();
    addMessage('user', q);
    addMessage('assistant', a);
}

async function loadDocuments() {
    const res = await api('/api/documents');
    if (!res.ok) return;
    const docs = await res.json();
    const el = $('doc-list');
    $('doc-empty').classList.toggle('hidden', docs.length > 0);
    el.innerHTML = docs.map(d => `<div class="doc-item">
        <span class="doc-name">${esc(d.filename)}</span>
        <span class="doc-status ${d.status}">${d.status}</span>
        <button class="btn-del" onclick="deleteDoc(${d.id})" title="Delete">✕</button>
    </div>`).join('');
}

$('file-input').addEventListener('change', async function () {
    if (!this.files.length) return;
    const form = new FormData();
    form.append('file', this.files[0]);
    const btn = document.querySelector('.btn-upload');
    btn.textContent = 'Uploading…';
    btn.disabled = true;
    const res = await api('/api/documents/upload', { method: 'POST', body: form });
    btn.textContent = '+ Upload .md';
    btn.disabled = false;
    this.value = '';
    if (!res.ok) { alert((await res.json()).detail); return; }
    loadDocuments();
});

async function deleteDoc(id) {
    await api(`/api/documents/${id}`, { method: 'DELETE' });
    loadDocuments();
}

function clearMessages() {
    const el = $('messages');
    el.innerHTML = '';
    $('empty-state')?.remove();
}

function addMessage(role, text) {
    const el = $('messages');
    const es = $('empty-state');
    if (es) es.remove();
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.innerHTML = `<div class="msg-head"><span class="msg-sender">${role === 'user' ? 'You' : 'Assistant'}</span><span class="msg-time">${now}</span></div><div class="msg-body">${role === 'assistant' ? md(text) : esc(text)}</div>`;
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
}

function showTyping() {
    const el = $('messages');
    const div = document.createElement('div');
    div.className = 'typing';
    div.id = 'typing';
    div.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
}

function hideTyping() {
    $('typing')?.remove();
}

async function handleSend(e) {
    e.preventDefault();
    const input = $('chat-input');
    const q = input.value.trim();
    if (!q) return;
    input.value = '';
    $('btn-send').disabled = true;
    addMessage('user', q);
    showTyping();
    try {
        const res = await api('/api/chat', { method: 'POST', body: JSON.stringify({ question: q }) });
        hideTyping();
        if (!res.ok) { addMessage('assistant', 'Error: ' + (await res.json()).detail); return; }
        const data = await res.json();
        addMessage('assistant', data.answer);
        loadHistory();
    } catch (err) {
        hideTyping();
        addMessage('assistant', 'Connection error.');
    } finally {
        $('btn-send').disabled = false;
        input.focus();
    }
}

function md(text) {
    let s = text.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    s = s.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\[(\d+)\]/g, '<span class="cite">[$1]</span>');
    s = s.replace(/\n/g, '<br>');
    return s;
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

(async function init() {
    await loadTenants();
    if (token) {
        try {
            const res = await api('/api/auth/me');
            if (res.ok) { showApp(); return; }
        } catch (e) {}
        localStorage.clear();
        token = null;
    }
})();

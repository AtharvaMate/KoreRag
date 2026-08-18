let token = localStorage.getItem('token');
let username = localStorage.getItem('username');
let isAdmin = localStorage.getItem('is_admin') === 'true';
let currentTenantFilter = '';  
let uploadTargetKbId = null;
let fileQueue = [];

function api(path, opts = {}) {
    const headers = { ...opts.headers };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (!(opts.body instanceof FormData)) headers['Content-Type'] = 'application/json';
    return fetch(path, { ...opts, headers });
}

function $(id) { return document.getElementById(id); }

function showToast(message, type = 'info') {
    const container = $('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all .3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

async function handleAdminLogin(e) {
    e.preventDefault();
    const btn = $('login-btn');
    btn.disabled = true;
    btn.textContent = 'Signing in…';

    try {
        const res = await api('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                username: $('login-user').value,
                password: $('login-pass').value,
            }),
        });

        if (!res.ok) {
            const err = await res.json();
            $('login-error').textContent = err.detail || 'Login failed';
            return;
        }

        const data = await res.json();
        if (!data.is_admin) {
            $('login-error').textContent = 'This account does not have admin access';
            return;
        }

        token = data.token;
        username = data.username;
        isAdmin = true;
        localStorage.setItem('token', token);
        localStorage.setItem('username', username);
        localStorage.setItem('is_admin', 'true');
        localStorage.setItem('tenant', data.tenant);

        showAdminPanel();
    } catch (err) {
        $('login-error').textContent = 'Connection error';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign in';
    }
}

function adminLogout() {
    localStorage.clear();
    location.reload();
}

async function showAdminPanel() {
    $('admin-login').classList.add('hidden');
    $('admin-panel').classList.remove('hidden');
    $('topbar-user').textContent = username;
    await loadTenants();
    await loadKnowledgeBases();
}

let allTenants = [];

async function loadTenants() {
    const res = await api('/api/admin/tenants');
    if (!res.ok) { showToast('Failed to load tenants', 'error'); return; }
    allTenants = await res.json();
    renderTenantList();
    renderTenantDropdowns();
}

function renderTenantList() {
    const el = $('tenant-list');
    const empty = $('tenant-empty');

    if (allTenants.length === 0) {
        el.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    el.innerHTML = allTenants.map(t => {
        const d = new Date(t.created_at);
        const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        return `<div class="tenant-row">
            <div class="tenant-info">
                <div class="tenant-icon">${t.name[0].toUpperCase()}</div>
                <div class="tenant-details">
                    <div class="tenant-name-label">${esc(t.name)}</div>
                    <div class="tenant-slug-label">${esc(t.slug)}</div>
                </div>
            </div>
            <div class="tenant-row-actions">
                <span class="tenant-date">${dateStr}</span>
                <button class="btn-del-tenant" onclick="deleteTenant(${t.id}, '${esc(t.name)}')" title="Delete tenant">Delete</button>
            </div>
        </div>`;
    }).join('');
}

function renderTenantDropdowns() {
    const sel = $('tenant-select');
    sel.innerHTML = `<option value="">All Tenants</option>` +
        allTenants.map(t => `<option value="${t.slug}" ${t.slug === currentTenantFilter ? 'selected' : ''}>${t.name}</option>`).join('');

    const kbTenantSel = $('kb-tenant');
    kbTenantSel.innerHTML = allTenants.map(t => `<option value="${t.slug}">${t.name}</option>`).join('');
}

function onTenantSwitch() {
    currentTenantFilter = $('tenant-select').value;
    loadKnowledgeBases();
}

function openCreateTenantModal() {
    $('tenant-name').value = '';
    $('tenant-slug').value = '';
    $('modal-create-tenant').classList.remove('hidden');
    $('tenant-name').focus();
}

async function handleCreateTenant(e) {
    e.preventDefault();
    const name = $('tenant-name').value.trim();
    const slug = $('tenant-slug').value.trim().toLowerCase();

    const res = await api('/api/admin/tenants', {
        method: 'POST',
        body: JSON.stringify({ name, slug }),
    });

    if (!res.ok) {
        const err = await res.json();
        showToast(err.detail || 'Failed to create tenant', 'error');
        return;
    }

    hideModal('modal-create-tenant');
    showToast(`Tenant "${name}" created`, 'success');
    await loadTenants();
}

async function deleteTenant(id, name) {
    if (!confirm(`Delete tenant "${name}"? This cannot be undone.`)) return;

    const res = await api(`/api/admin/tenants/${id}`, { method: 'DELETE' });
    if (!res.ok) {
        const err = await res.json();
        showToast(err.detail || 'Failed to delete tenant', 'error');
        return;
    }

    showToast(`Tenant "${name}" deleted`, 'success');
    await loadTenants();
    await loadKnowledgeBases();
}

let allKBs = [];

async function loadKnowledgeBases() {
    let url = '/api/admin/knowledge-bases';
    if (currentTenantFilter) url += `?tenant_slug=${currentTenantFilter}`;

    const res = await api(url);
    if (!res.ok) { showToast('Failed to load knowledge bases', 'error'); return; }
    allKBs = await res.json();
    renderKBGrid();
}

function renderKBGrid() {
    const grid = $('kb-grid');
    const empty = $('kb-empty');

    if (allKBs.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    grid.innerHTML = allKBs.map(kb => {
        const d = new Date(kb.created_at);
        const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        return `<div class="kb-card">
            <div class="kb-card-head">
                <div class="kb-card-name">${esc(kb.name)}</div>
                <div class="kb-card-actions">
                    <button class="kb-btn danger" onclick="deleteKB(${kb.id}, '${esc(kb.name)}')" title="Delete KB">🗑</button>
                </div>
            </div>
            <div class="kb-card-meta">
                <div class="kb-meta-item">
                    <span class="kb-meta-icon">📄</span>
                    <span class="kb-meta-value">${kb.document_count}</span> docs
                </div>
                <div class="kb-meta-item">
                    <span class="kb-meta-icon">🏢</span>
                    <span class="kb-meta-value">${esc(kb.tenant_name)}</span>
                </div>
                <div class="kb-meta-item">
                    <span class="kb-meta-icon">📅</span> ${dateStr}
                </div>
            </div>
            <div class="kb-card-footer">
                <button class="kb-btn-sm primary" onclick="openUploadModal(${kb.id}, '${esc(kb.name)}')">📤 Upload .md</button>
                <button class="kb-btn-sm" onclick="viewKBDocuments(${kb.id}, '${esc(kb.name)}')">View docs</button>
            </div>
        </div>`;
    }).join('');
}

function openCreateKBModal() {
    $('kb-name').value = '';
    renderTenantDropdowns();
    $('modal-create-kb').classList.remove('hidden');
    $('kb-name').focus();
}

async function handleCreateKB(e) {
    e.preventDefault();
    const name = $('kb-name').value.trim();
    const tenantSlug = $('kb-tenant').value;

    const res = await api('/api/admin/knowledge-bases', {
        method: 'POST',
        body: JSON.stringify({ name, tenant_slug: tenantSlug }),
    });

    if (!res.ok) {
        const err = await res.json();
        showToast(err.detail || 'Failed to create KB', 'error');
        return;
    }

    hideModal('modal-create-kb');
    showToast(`Knowledge base "${name}" created`, 'success');
    await loadKnowledgeBases();
}

async function deleteKB(id, name) {
    if (!confirm(`Delete knowledge base "${name}" and all its documents? This cannot be undone.`)) return;

    const res = await api(`/api/admin/knowledge-bases/${id}`, { method: 'DELETE' });
    if (!res.ok) {
        const err = await res.json();
        showToast(err.detail || 'Failed to delete KB', 'error');
        return;
    }

    showToast(`Knowledge base "${name}" deleted`, 'success');
    await loadKnowledgeBases();
}

async function viewKBDocuments(kbId, kbName) {
    $('kb-detail-title').textContent = kbName;
    $('modal-kb-detail').classList.remove('hidden');
    $('kb-detail-docs').innerHTML = '<div style="text-align:center;padding:20px;color:var(--t4)">Loading…</div>';
    $('kb-detail-empty').classList.add('hidden');

    const res = await api(`/api/admin/knowledge-bases/${kbId}/documents`);
    if (!res.ok) {
        $('kb-detail-docs').innerHTML = '<div style="text-align:center;padding:20px;color:var(--red)">Failed to load documents</div>';
        return;
    }

    const docs = await res.json();
    if (docs.length === 0) {
        $('kb-detail-docs').innerHTML = '';
        $('kb-detail-empty').classList.remove('hidden');
        return;
    }

    $('kb-detail-docs').innerHTML = docs.map(d => {
        const dt = new Date(d.uploaded_at);
        const dateStr = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        return `<div class="kb-doc-row">
            <span class="kb-doc-name">📄 ${esc(d.filename)}</span>
            <span class="kb-doc-status ${d.status}">${d.status}</span>
            <span class="kb-doc-date">${dateStr}</span>
        </div>`;
    }).join('');
}


function openUploadModal(kbId, kbName) {
    uploadTargetKbId = kbId;
    $('upload-kb-label').textContent = `→ ${kbName}`;
    clearQueue();
    $('upload-results').classList.add('hidden');
    $('upload-results').innerHTML = '';
    $('modal-upload').classList.remove('hidden');
}

function clearQueue() {
    fileQueue = [];
    $('file-queue').classList.add('hidden');
    $('upload-actions').classList.add('hidden');
    $('queue-list').innerHTML = '';
    $('file-picker').value = '';
}

function addFiles(files) {
    let rejected = 0;
    for (const file of files) {
        if (!file.name.toLowerCase().endsWith('.md')) {
            rejected++;
            continue;
        }
        if (fileQueue.some(f => f.name === file.name)) continue;
        fileQueue.push(file);
    }
    if (rejected > 0) {
        showToast(`${rejected} file(s) rejected — only .md files are allowed`, 'error');
    }
    renderQueue();
}

function removeFromQueue(index) {
    fileQueue.splice(index, 1);
    renderQueue();
}

function renderQueue() {
    if (fileQueue.length === 0) {
        $('file-queue').classList.add('hidden');
        $('upload-actions').classList.add('hidden');
        return;
    }

    $('file-queue').classList.remove('hidden');
    $('upload-actions').classList.remove('hidden');
    $('queue-count').textContent = `${fileQueue.length} file${fileQueue.length !== 1 ? 's' : ''} selected`;

    $('queue-list').innerHTML = fileQueue.map((f, i) => {
        const sizeKB = (f.size / 1024).toFixed(1);
        return `<div class="queue-item" id="queue-item-${i}">
            <span class="queue-item-name">📄 ${esc(f.name)}</span>
            <span class="queue-item-size">${sizeKB} KB</span>
            <button class="queue-item-remove" onclick="removeFromQueue(${i})">✕</button>
        </div>`;
    }).join('');
}

async function handleUpload() {
    if (fileQueue.length === 0) return;
    if (!uploadTargetKbId) return;

    const btn = $('btn-upload');
    btn.disabled = true;
    btn.textContent = 'Uploading…';

    try {
        if (fileQueue.length === 1) {
            const formData = new FormData();
            formData.append('file', fileQueue[0]);

            const res = await api(`/api/admin/knowledge-bases/${uploadTargetKbId}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                showToast(err.detail || 'Upload failed', 'error');
                return;
            }

            const data = await res.json();
            showUploadResults({
                total: 1,
                success: 1,
                failed: 0,
                files: [data],
            });
            showToast('File uploaded and indexed successfully', 'success');
        } else {
            const formData = new FormData();
            for (const file of fileQueue) {
                formData.append('files', file);
            }

            const res = await api(`/api/admin/knowledge-bases/${uploadTargetKbId}/bulk-upload`, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                showToast(err.detail || 'Bulk upload failed', 'error');
                return;
            }

            const data = await res.json();
            showUploadResults(data);

            if (data.failed === 0) {
                showToast(`${data.success} file(s) uploaded successfully`, 'success');
            } else {
                showToast(`${data.success} uploaded, ${data.failed} failed`, 'error');
            }
        }

        fileQueue = [];
        $('file-queue').classList.add('hidden');
        $('upload-actions').classList.add('hidden');
        await loadKnowledgeBases();
    } catch (err) {
        showToast('Connection error during upload', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Upload & Index';
    }
}

function showUploadResults(data) {
    const el = $('upload-results');
    el.classList.remove('hidden');
    el.innerHTML = `
        <div class="result-summary">✅ ${data.success} uploaded · ${data.failed > 0 ? `❌ ${data.failed} failed · ` : ''}${data.total} total</div>
        <div class="result-detail">${data.files.map(f =>
            `${f.status === 'ready' ? '✅' : '❌'} ${esc(f.filename)} ${f.chunks ? `(${f.chunks} chunks)` : ''} ${f.error ? `— ${esc(f.error)}` : ''}`
        ).join('<br>')}</div>`;
}

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = $('drop-zone');
    if (!dropZone) return;

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            addFiles(e.dataTransfer.files);
        }
    });

    $('file-picker').addEventListener('change', function () {
        if (this.files.length) addFiles(this.files);
        this.value = '';
    });
});

function hideModal(id) {
    $(id).classList.add('hidden');
}

function closeModal(e, id) {
    if (e.target === $(id)) hideModal(id);
}

function switchSection(name) {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.section === name));
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    $(`section-${name}`).classList.remove('hidden');
}

function esc(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

// ── Auto-slug for tenant name ────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const nameInput = $('tenant-name');
    const slugInput = $('tenant-slug');
    if (nameInput && slugInput) {
        nameInput.addEventListener('input', () => {
            slugInput.value = nameInput.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        });
    }
});

// ── Init ─────────────────────────────────────────────────────
(async function init() {
    if (token && isAdmin) {
        try {
            const res = await api('/api/auth/me');
            if (res.ok) {
                const data = await res.json();
                if (data.is_admin) {
                    username = data.username;
                    showAdminPanel();
                    return;
                }
            }
        } catch (e) {}
    }
    // Show login
    $('admin-login').classList.remove('hidden');
    $('admin-panel').classList.add('hidden');
})();

/* ═══════════════════════════════════════════════════════════════════════════
   SECURALYS - Frontend Application
   Dashboard for Connected Container Management
   ═══════════════════════════════════════════════════════════════════════════ */

const API_BASE = 'http://127.0.0.1:8000/api';

// ─── State ───────────────────────────────────────────────────────────────────
let currentPage = 'dashboard';
let state = {
    ouvriers: [],
    outils: [],
    emprunts: [],
    historique: [],
    modeNuit: false,
    arduinoConnected: false
};

// ─── Initialization ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initClock();
    initModeNuit();
    initFilters();
    loadDashboard();
    
    // Auto-refresh every 5 seconds
    setInterval(loadDashboard, 5000);
});

// ─── Navigation ──────────────────────────────────────────────────────────────
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            navigateTo(page);
        });
    });
}

function navigateTo(page) {
    // Update active link
    document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    // Update active page
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');
    
    // Update page title
    const titles = {
        dashboard: 'Tableau de bord',
        ouvriers: 'Gestion des ouvriers',
        outils: 'Gestion des outils',
        historique: 'Historique',
        parametres: 'Paramètres'
    };
    document.getElementById('page-title').textContent = titles[page] || page;
    currentPage = page;
    
    // Load page data
    switch(page) {
        case 'dashboard': loadDashboard(); break;
        case 'ouvriers': loadOuvriers(); break;
        case 'outils': loadOutils(); break;
        case 'historique': loadHistorique(); break;
        case 'parametres': loadParametres(); break;
    }
}

// ─── Clock ───────────────────────────────────────────────────────────────────
function initClock() {
    updateClock();
    setInterval(updateClock, 1000);
}

function updateClock() {
    const now = new Date();
    document.getElementById('current-time').textContent = 
        now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    document.getElementById('current-date').textContent = 
        now.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
}

// ─── Mode Nuit ───────────────────────────────────────────────────────────────
function initModeNuit() {
    const btn = document.getElementById('mode-nuit-btn');
    btn.addEventListener('click', () => {
        state.modeNuit = !state.modeNuit;
        btn.classList.toggle('active', state.modeNuit);
        
        if (state.modeNuit) {
            showToast('Mode nuit activé — Surveillance renforcée', 'warning');
        } else {
            showToast('Mode nuit désactivé', 'success');
        }
    });
}

// ─── Filters ─────────────────────────────────────────────────────────────────
function initFilters() {
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            loadOutils(tab.dataset.filter);
        });
    });
}

// ─── API Calls ───────────────────────────────────────────────────────────────
async function api(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur serveur');
        }
        
        if (response.status === 204) return null;
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ─── Dashboard ───────────────────────────────────────────────────────────────
async function loadDashboard() {
    try {
        const [dashboard, emprunts] = await Promise.all([
            api('/dashboard'),
            api('/emprunts/')
        ]);
        
        // Update stats
        animateValue('stat-total-outils', dashboard.total_outils);
        animateValue('stat-disponibles', dashboard.outils_disponibles);
        animateValue('stat-empruntes', dashboard.outils_empruntes);
        animateValue('stat-ouvriers', dashboard.total_ouvriers);
        
        // Update emprunts table
        state.emprunts = emprunts;
        renderEmprunts(emprunts);
        document.getElementById('emprunts-count').textContent = emprunts.length;
        
        // Check for alerts
        checkAlertes(emprunts);
        
    } catch (error) {
        showToast('Erreur de chargement du dashboard', 'error');
    }
}

function animateValue(elementId, value) {
    const el = document.getElementById(elementId);
    const current = parseInt(el.textContent) || 0;
    
    if (current !== value) {
        el.textContent = value;
        el.style.transform = 'scale(1.1)';
        setTimeout(() => el.style.transform = 'scale(1)', 150);
    }
}

function renderEmprunts(emprunts) {
    const tbody = document.getElementById('emprunts-table');
    
    if (emprunts.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5">
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                        <span>Tous les outils sont disponibles</span>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = emprunts.map(e => {
        const duree = calculateDuree(e.heure_sortie);
        return `
            <tr>
                <td><strong>${e.outil_nom}</strong></td>
                <td>${e.ouvrier_nom}</td>
                <td>${formatTime(e.heure_sortie)}</td>
                <td><span class="badge badge-warning">${duree}</span></td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="retourOutil(${e.id})">
                        Retour
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function calculateDuree(heureDebut) {
    const start = new Date(heureDebut);
    const now = new Date();
    const diffMinutes = Math.floor((now - start) / 60000);
    
    if (diffMinutes < 60) return `${diffMinutes}min`;
    const hours = Math.floor(diffMinutes / 60);
    const mins = diffMinutes % 60;
    return `${hours}h${mins.toString().padStart(2, '0')}`;
}

function formatTime(datetime) {
    return new Date(datetime).toLocaleTimeString('fr-FR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function checkAlertes(emprunts) {
    const panel = document.getElementById('alertes-panel');
    const content = document.getElementById('alertes-content');
    
    // Check for long emprunts (> 8 hours)
    const longEmprunts = emprunts.filter(e => {
        const start = new Date(e.heure_sortie);
        const now = new Date();
        const hours = (now - start) / 3600000;
        return hours > 8;
    });
    
    if (longEmprunts.length > 0) {
        panel.style.display = 'block';
        content.innerHTML = longEmprunts.map(e => `
            <div class="alert-item">
                <strong>${e.outil_nom}</strong> 
                emprunté par <strong>${e.ouvrier_nom}</strong> depuis plus de 8h
            </div>
        `).join('');
    } else {
        panel.style.display = 'none';
    }
}

async function retourOutil(empruntId) {
    try {
        await api(`/emprunts/${empruntId}/retour`, { method: 'PUT' });
        showToast('Outil retourné avec succès', 'success');
        loadDashboard();
    } catch (error) {
        showToast('Erreur lors du retour', 'error');
    }
}

// ─── Ouvriers ────────────────────────────────────────────────────────────────
async function loadOuvriers() {
    try {
        const ouvriers = await api('/ouvriers/');
        state.ouvriers = ouvriers;
        renderOuvriers(ouvriers);
    } catch (error) {
        showToast('Erreur de chargement des ouvriers', 'error');
    }
}

function renderOuvriers(ouvriers) {
    const tbody = document.getElementById('ouvriers-table');
    
    if (ouvriers.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5">
                    <div class="empty-state">
                        <span>Aucun ouvrier enregistré</span>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = ouvriers.map(o => `
        <tr>
            <td><strong>${o.prenom} ${o.nom}</strong></td>
            <td><code style="background: var(--brand-10); padding: 4px 8px; border-radius: 4px; font-size: 12px;">${o.badge_rfid}</code></td>
            <td><span class="badge badge-brand">${o.role}</span></td>
            <td>${o.actif 
                ? '<span class="badge badge-success">Actif</span>' 
                : '<span class="badge badge-warning">Inactif</span>'
            }</td>
            <td>
                <button class="btn btn-small btn-secondary" onclick="editOuvrier(${o.id})">Modifier</button>
                <button class="btn btn-small btn-danger" onclick="deleteOuvrier(${o.id})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');
}

async function deleteOuvrier(id) {
    if (!confirm('Supprimer cet ouvrier ?')) return;
    
    try {
        await api(`/ouvriers/${id}`, { method: 'DELETE' });
        showToast('Ouvrier supprimé', 'success');
        loadOuvriers();
    } catch (error) {
        showToast('Erreur lors de la suppression', 'error');
    }
}

// ─── Outils ──────────────────────────────────────────────────────────────────
let activeDispoFilter = 'all';
let activeCategorieFilter = 'all';

async function loadOutils(filter = null) {
    // Déterminer quel filtre est mis à jour
    const dispoFilters = ['all', 'disponible', 'emprunte'];
    if (filter !== null) {
        if (filter === 'all-cat') {
            activeCategorieFilter = 'all';
        } else if (dispoFilters.includes(filter)) {
            activeDispoFilter = filter;
        } else {
            activeCategorieFilter = filter;
        }
    }

    try {
        let endpoint = '/outils/';
        if (activeDispoFilter === 'disponible') endpoint += '?disponible=true';
        if (activeDispoFilter === 'emprunte') endpoint += '?disponible=false';

        const outils = await api(endpoint);
        state.outils = outils;

        // Appliquer le filtre catégorie côté client
        const filtered = activeCategorieFilter === 'all'
            ? outils
            : outils.filter(o => (o.categorie || '').toLowerCase() === activeCategorieFilter);

        renderOutils(filtered);

        // Mettre à jour les boutons dispo
        document.querySelectorAll('.filter-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === activeDispoFilter);
        });

        // Mettre à jour les boutons catégorie
        document.querySelectorAll('.filter-cat').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.cat === activeCategorieFilter);
        });
    } catch (error) {
        showToast('Erreur de chargement des outils', 'error');
    }
}

function renderOutils(outils) {
    const grid = document.getElementById('outils-grid');
    
    if (outils.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 60px;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:48px;height:48px;color:var(--text-muted);">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                </svg>
                <p style="color: var(--text-muted); margin-top: 16px;">Aucun outil trouvé</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = outils.map(o => `
        <div class="tool-card ${o.est_disponible ? '' : 'borrowed'}">
            <div class="tool-header">
                <span class="tool-name">${o.nom}</span>
                ${o.est_disponible 
                    ? '<span class="tool-status available">Disponible</span>' 
                    : '<span class="tool-status borrowed">Emprunté</span>'
                }
            </div>
            <div class="tool-tag">${o.tag_rfid}</div>
            <div class="tool-footer">
                <span class="tool-category">${o.categorie || 'Non catégorisé'}</span>
                ${!o.est_disponible ? `<span class="tool-borrower">En cours d'utilisation</span>` : ''}
            </div>
            <div class="tool-actions">
                <button class="btn btn-small btn-secondary" onclick="editOutil(${o.id})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                    Modifier
                </button>
            </div>
        </div>
    `).join('');
}

function editOutil(id) {
    const outil = state.outils.find(o => o.id === id);
    if (!outil) return;
    openModal('outil', id);
    setTimeout(() => {
        document.querySelector('[name="nom"]').value = outil.nom || '';
        document.querySelector('[name="tag_rfid"]').value = outil.tag_rfid || '';
        document.querySelector('[name="categorie"]').value = outil.categorie || 'électroportatif';
        document.querySelector('[name="description"]').value = outil.description || '';
    }, 50);
}

async function deleteOutil(id, nom) {
    if (!confirm(`Supprimer l'outil "${nom}" ? Cette action est irréversible.`)) return;
    try {
        await api(`/outils/${id}`, { method: 'DELETE' });
        showToast(`Outil "${nom}" supprimé`, 'success');
        closeModal();
        loadOutils();
    } catch (error) {
        showToast(error.message || 'Erreur lors de la suppression', 'error');
    }
}

// ─── Historique ──────────────────────────────────────────────────────────────
async function loadHistorique() {
    try {
        const historique = await api('/historique');
        state.historique = historique;
        renderHistorique(historique);
    } catch (error) {
        showToast('Erreur de chargement de l\'historique', 'error');
    }
}

function renderHistorique(historique) {
    const tbody = document.getElementById('historique-table');
    
    if (historique.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="4">
                    <div class="empty-state">
                        <span>Aucun historique d'utilisation</span>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = historique.map(h => `
        <tr>
            <td>${new Date(h.heure_sortie).toLocaleDateString('fr-FR')}</td>
            <td><strong>${h.outil_nom}</strong></td>
            <td>${h.ouvrier_nom}</td>
            <td><span class="badge badge-success">${formatDuration(h.duree_minutes)}</span></td>
        </tr>
    `).join('');
}

function formatDuration(minutes) {
    if (!minutes) return '< 1 min';
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h${mins.toString().padStart(2, '0')}`;
}

function exportCSV() {
    if (state.historique.length === 0) {
        showToast('Aucune donnée à exporter', 'warning');
        return;
    }
    
    const headers = ['Date', 'Outil', 'Ouvrier', 'Durée (min)'];
    const rows = state.historique.map(h => [
        new Date(h.heure_sortie).toLocaleDateString('fr-FR'),
        h.outil_nom,
        h.ouvrier_nom,
        h.duree_minutes
    ]);
    
    const csv = [headers, ...rows].map(r => r.join(';')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `securalys_historique_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    
    showToast('Export CSV téléchargé', 'success');
}

// ─── Modal ───────────────────────────────────────────────────────────────────
function openModal(type, editId = null) {
    const overlay = document.getElementById('modal-backdrop');
    const title = document.getElementById('modal-title');
    const fields = document.getElementById('modal-fields');
    const form = document.getElementById('modal-form');
    
    overlay.classList.add('active');
    
    if (type === 'ouvrier') {
        title.textContent = editId ? 'Modifier l\'ouvrier' : 'Ajouter un ouvrier';
        fields.innerHTML = `
            <div class="form-group">
                <label class="form-label">Prénom</label>
                <input type="text" class="form-input" name="prenom" required placeholder="Jean">
            </div>
            <div class="form-group">
                <label class="form-label">Nom</label>
                <input type="text" class="form-input" name="nom" required placeholder="Dupont">
            </div>
            <div class="form-group">
                <label class="form-label">Badge RFID</label>
                <input type="text" class="form-input" name="badge_rfid" required placeholder="BADGE005">
            </div>
            <div class="form-group">
                <label class="form-label">Rôle</label>
                <select class="form-select" name="role">
                    <option value="ouvrier">Ouvrier</option>
                    <option value="chef">Chef d'équipe</option>
                    <option value="conduc">Conducteur de travaux</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Email (optionnel)</label>
                <input type="email" class="form-input" name="email" placeholder="email@example.com">
            </div>
        `;
        
        form.onsubmit = (e) => submitOuvrier(e, editId);
        
    } else if (type === 'outil') {
        const outilData = editId ? state.outils.find(o => o.id === editId) : null;
        title.textContent = editId ? 'Modifier l\'outil' : 'Ajouter un outil';
        fields.innerHTML = `
            <div class="form-group">
                <label class="form-label">Nom de l'outil</label>
                <input type="text" class="form-input" name="nom" required placeholder="Perceuse Makita">
            </div>
            <div class="form-group">
                <label class="form-label">Tag RFID</label>
                <input type="text" class="form-input" name="tag_rfid" required placeholder="OUTIL009">
            </div>
            <div class="form-group">
                <label class="form-label">Catégorie</label>
                <select class="form-select" name="categorie">
                    <option value="électroportatif">Électroportatif</option>
                    <option value="manuel">Manuel</option>
                    <option value="mesure">Mesure</option>
                    <option value="sécurité">Sécurité</option>
                    <option value="autre">Autre</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Description (optionnel)</label>
                <input type="text" class="form-input" name="description" placeholder="Détails supplémentaires">
            </div>
        `;

        // Footer : bouton Supprimer visible uniquement en mode édition
        const modalFooter = overlay.querySelector('.modal-footer');
        if (editId && outilData) {
            modalFooter.innerHTML = `
                <button type="button" class="btn btn-danger" onclick="deleteOutil(${editId}, '${outilData.nom}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;margin-right:6px;vertical-align:middle;">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                    Supprimer
                </button>
                <div style="display:flex;gap:8px;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">Annuler</button>
                    <button type="submit" class="btn btn-primary">Enregistrer</button>
                </div>
            `;
        } else {
            modalFooter.innerHTML = `
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Annuler</button>
                <button type="submit" class="btn btn-primary">Confirmer</button>
            `;
        }

        form.onsubmit = (e) => submitOutil(e, editId);
    }
}

function closeModal() {
    document.getElementById('modal-backdrop').classList.remove('active');
}

async function submitOuvrier(e, editId = null) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    try {
        if (editId) {
            await api(`/ouvriers/${editId}`, { method: 'PUT', body: JSON.stringify(data) });
            showToast('Ouvrier modifié', 'success');
        } else {
            await api('/ouvriers/', { method: 'POST', body: JSON.stringify(data) });
            showToast('Ouvrier ajouté', 'success');
        }
        closeModal();
        loadOuvriers();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function submitOutil(e, editId = null) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    try {
        if (editId) {
            await api(`/outils/${editId}`, { method: 'PUT', body: JSON.stringify(data) });
            showToast('Outil modifié', 'success');
        } else {
            await api('/outils/', { method: 'POST', body: JSON.stringify(data) });
            showToast('Outil ajouté', 'success');
        }
        closeModal();
        loadOutils();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function editOuvrier(id) {
    // Load ouvrier data and open modal
    const ouvrier = state.ouvriers.find(o => o.id === id);
    if (!ouvrier) return;
    
    openModal('ouvrier', id);
    
    // Fill form with existing data
    setTimeout(() => {
        document.querySelector('[name="prenom"]').value = ouvrier.prenom;
        document.querySelector('[name="nom"]').value = ouvrier.nom;
        document.querySelector('[name="badge_rfid"]').value = ouvrier.badge_rfid;
        document.querySelector('[name="role"]').value = ouvrier.role;
        if (ouvrier.email) document.querySelector('[name="email"]').value = ouvrier.email;
    }, 50);
}

// ─── Toast Notifications ─────────────────────────────────────────────────────
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ─── Emprunt Modal ───────────────────────────────────────────────────────────
async function openEmpruntModal() {
    const backdrop = document.getElementById('emprunt-modal-backdrop');
    const ouvrierSelect = document.getElementById('emprunt-ouvrier');
    const outilSelect = document.getElementById('emprunt-outil');
    
    // Charger les ouvriers
    try {
        const ouvriers = await api('/ouvriers/');
        ouvrierSelect.innerHTML = '<option value="">-- Sélectionner un ouvrier --</option>' +
            ouvriers.filter(o => o.actif).map(o => 
                `<option value="${o.id}">${o.prenom} ${o.nom} (${o.role})</option>`
            ).join('');
    } catch (error) {
        showToast('Erreur chargement ouvriers', 'error');
    }
    
    // Charger les outils disponibles
    try {
        const outils = await api('/outils/');
        const disponibles = outils.filter(o => o.est_disponible);
        
        if (disponibles.length === 0) {
            outilSelect.innerHTML = '<option value="">Aucun outil disponible</option>';
        } else {
            outilSelect.innerHTML = '<option value="">-- Sélectionner un outil --</option>' +
                disponibles.map(o => 
                    `<option value="${o.id}">${o.nom} - ${o.categorie}</option>`
                ).join('');
        }
    } catch (error) {
        showToast('Erreur chargement outils', 'error');
    }
    
    backdrop.classList.add('active');
}

function closeEmpruntModal() {
    document.getElementById('emprunt-modal-backdrop').classList.remove('active');
    document.getElementById('emprunt-form').reset();
}

async function submitEmprunt(e) {
    e.preventDefault();
    
    const ouvrierId = document.getElementById('emprunt-ouvrier').value;
    const outilId = document.getElementById('emprunt-outil').value;
    
    if (!ouvrierId || !outilId) {
        showToast('Veuillez sélectionner un ouvrier et un outil', 'warning');
        return;
    }
    
    try {
        await api('/emprunts/', {
            method: 'POST',
            body: JSON.stringify({
                ouvrier_id: parseInt(ouvrierId),
                outil_id: parseInt(outilId)
            })
        });
        
        showToast('Emprunt enregistré avec succès', 'success');
        closeEmpruntModal();
        loadDashboard();
    } catch (error) {
        showToast(error.message || 'Erreur lors de la création', 'error');
    }
}

// ─── Close modal on outside click ────────────────────────────────────────────
document.getElementById('modal-backdrop').addEventListener('click', (e) => {
    if (e.target.id === 'modal-backdrop') closeModal();
});

document.getElementById('emprunt-modal-backdrop').addEventListener('click', (e) => {
    if (e.target.id === 'emprunt-modal-backdrop') closeEmpruntModal();
});

// ─── Keyboard shortcuts ──────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
        closeEmpruntModal();
    }
});

// ═══════════════════════════════════════════════════════════════════════════════
//  SETTINGS PAGE FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

async function loadParametres() {
    // Populate simulation dropdowns
    await populateSimulationDropdowns();
    // Load current notification config
    await loadNotificationConfig();
    // Check Arduino status
    await checkArduinoStatus();
}

async function populateSimulationDropdowns() {
    try {
        const [ouvriersRes, outilsRes] = await Promise.all([
            fetch(`${API_BASE}/ouvriers`),
            fetch(`${API_BASE}/outils`)
        ]);
        
        const ouvriers = await ouvriersRes.json();
        const outils = await outilsRes.json();
        
        const simBadgeSelect = document.getElementById('sim-badge');
        const simOutilSelect = document.getElementById('sim-outil');
        
        if (simBadgeSelect) {
            simBadgeSelect.innerHTML = '<option value="">Sélectionner un ouvrier...</option>' +
                ouvriers.map(o => `<option value="${o.badge_rfid}">${o.prenom} ${o.nom} (${o.badge_rfid})</option>`).join('');
        }
        
        if (simOutilSelect) {
            simOutilSelect.innerHTML = '<option value="">Sélectionner un outil...</option>' +
                outils.map(o => `<option value="${o.tag_rfid}">${o.nom} (${o.tag_rfid})</option>`).join('');
        }
    } catch (error) {
        console.error('Erreur chargement dropdowns simulation:', error);
    }
}

async function loadNotificationConfig() {
    try {
        const res = await fetch(`${API_BASE}/notifications/config`);
        if (res.ok) {
            const config = await res.json();
            const emailInput = document.getElementById('notif-email');
            const heureInput = document.getElementById('notif-heure');
            
            if (emailInput && config.email_responsable) {
                emailInput.value = config.email_responsable;
            }
            if (heureInput && config.heure_fin_journee) {
                heureInput.value = config.heure_fin_journee;
            }
        }
    } catch (error) {
        console.error('Erreur chargement config notifications:', error);
    }
}

async function checkArduinoStatus() {
    try {
        const res = await fetch(`${API_BASE}/status`);
        if (res.ok) {
            const status = await res.json();
            const statusIndicator = document.querySelector('.settings-card .status-indicator');
            if (statusIndicator) {
                statusIndicator.className = `status-indicator status-${status.arduino_connected ? 'connected' : 'disconnected'}`;
                statusIndicator.nextElementSibling.textContent = status.arduino_connected ? 'Connecté' : 'Déconnecté';
            }
        }
    } catch (error) {
        console.error('Erreur vérification statut Arduino:', error);
    }
}

async function connectArduino() {
    const myMacPort = "/dev/tty.usbmodem13201"; // Votre port ici
    try {
        const res = await fetch(`${API_BASE}/rfid/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port: myMacPort }) // On envoie le bon port au backend
        });
        const data = await res.json();
        
        if (res.ok) {
            showToast('Arduino connecté avec succès', 'success');
            await checkArduinoStatus();
        } else {
            showToast(data.detail || 'Erreur de connexion', 'error');
        }
    } catch (error) {
        showToast('Erreur de connexion Arduino', 'error');
    }
}

async function disconnectArduino() {
    try {
        const res = await fetch(`${API_BASE}/rfid/disconnect`, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok) {
            showToast('Arduino déconnecté', 'info');
            await checkArduinoStatus();
        } else {
            showToast(data.detail || 'Erreur de déconnexion', 'error');
        }
    } catch (error) {
        showToast('Erreur de déconnexion Arduino', 'error');
    }
}

async function saveNotifConfig() {
    const email = document.getElementById('notif-email')?.value;
    const heure = document.getElementById('notif-heure')?.value;
    
    if (!email || !heure) {
        showToast('Veuillez remplir tous les champs', 'warning');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/notifications/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email_responsable: email,
                heure_fin_journee: heure
            })
        });
        
        if (res.ok) {
            showToast('Configuration enregistrée', 'success');
        } else {
            const data = await res.json();
            showToast(data.detail || 'Erreur de sauvegarde', 'error');
        }
    } catch (error) {
        showToast('Erreur de sauvegarde', 'error');
    }
}

async function testNotifications() {
    try {
        showToast('Envoi de notification de test...', 'info');
        
        const res = await fetch(`${API_BASE}/notifications/test`, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok) {
            showToast('Notification de test envoyée', 'success');
        } else {
            showToast(data.detail || 'Erreur envoi notification', 'error');
        }
    } catch (error) {
        showToast('Erreur envoi notification', 'error');
    }
}

async function simulateBadge() {
    const select = document.getElementById('sim-badge');
    const uid = select?.value;
    
    if (!uid) {
        showToast('Sélectionnez un ouvrier', 'warning');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/rfid/simulate/badge/${uid}`, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok) {
            showToast(`Badge ${uid} simulé - ${data.action}`, 'success');
            // Refresh dashboard if on dashboard page
            if (currentPage === 'dashboard') {
                loadDashboard();
            }
        } else {
            showToast(data.detail || 'Erreur simulation badge', 'error');
        }
    } catch (error) {
        showToast('Erreur simulation badge', 'error');
    }
}

async function simulateOutil() {
    const select = document.getElementById('sim-outil');
    const uid = select?.value;
    
    if (!uid) {
        showToast('Sélectionnez un outil', 'warning');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/rfid/simulate/outil/${uid}`, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok) {
            showToast(`Outil ${uid} simulé - ${data.result}`, 'success');
            // Refresh dashboard if on dashboard page
            if (currentPage === 'dashboard') {
                loadDashboard();
            }
        } else {
            showToast(data.detail || 'Erreur simulation outil', 'error');
        }
    } catch (error) {
        showToast('Erreur simulation outil', 'error');
    }
}
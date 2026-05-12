// Tabs
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
    loadData(tabId);
}

// Modals
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// API Fetch Helpers
const API = {
    get: async (url) => {
        const res = await fetch(url);
        return res.json();
    },
    post: async (url, data) => {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    }
}

// Data Loaders
async function loadData(tab) {
    if(tab === 'dashboard') loadCirurgias();
    else if(tab === 'pacientes') loadPacientes();
    else if(tab === 'medicos') loadMedicos();
    else if(tab === 'hospitais') loadHospitais();
    else if(tab === 'tipos') loadTipos();
}

async function loadCirurgias() {
    const data = await API.get('/api/cirurgias');
    const tbody = document.getElementById('cirurgias-tbody');
    tbody.innerHTML = data.map(c => `
        <tr>
            <td>#${c.id}</td>
            <td>${c.paciente ? c.paciente.nome : '-'}</td>
            <td>${c.medico ? c.medico.nome : '-'}</td>
            <td>${c.hospital ? c.hospital.nome : '-'}</td>
            <td>${c.dataHora ? new Date(c.dataHora).toLocaleString() : '-'}</td>
            <td><span class="badge status-${c.status ? c.status.toLowerCase() : ''}">${c.status || 'AGENDADA'}</span></td>
        </tr>
    `).join('');
    
    // Preload select options for modal
    loadSelects();
}

async function loadSelects() {
    const pacs = await API.get('/api/pacientes');
    const meds = await API.get('/api/medicos');
    const hosps = await API.get('/api/hospitals');
    const tipos = await API.get('/api/tipocirurgias');
    
    document.getElementById('cir-paciente').innerHTML = pacs.map(p => `<option value="${p.id}">${p.nome}</option>`).join('');
    document.getElementById('cir-medico').innerHTML = meds.map(m => `<option value="${m.id}">${m.nome}</option>`).join('');
    document.getElementById('cir-hospital').innerHTML = hosps.map(h => `<option value="${h.id}">${h.nome}</option>`).join('');
    document.getElementById('cir-tipo').innerHTML = tipos.map(t => `<option value="${t.id}">${t.nome}</option>`).join('');
}

async function loadPacientes() {
    const data = await API.get('/api/pacientes');
    document.getElementById('pacientes-tbody').innerHTML = data.map(i => `<tr><td>#${i.id}</td><td>${i.nome}</td><td>${i.cpf}</td></tr>`).join('');
}
async function loadMedicos() {
    const data = await API.get('/api/medicos');
    document.getElementById('medicos-tbody').innerHTML = data.map(i => `<tr><td>#${i.id}</td><td>${i.nome}</td><td>${i.crm}</td></tr>`).join('');
}
async function loadHospitais() {
    const data = await API.get('/api/hospitals');
    document.getElementById('hospitais-tbody').innerHTML = data.map(i => `<tr><td>#${i.id}</td><td>${i.nome}</td><td>${i.endereco}</td></tr>`).join('');
}
async function loadTipos() {
    const data = await API.get('/api/tipocirurgias');
    document.getElementById('tipos-tbody').innerHTML = data.map(i => `<tr><td>#${i.id}</td><td>${i.nome}</td><td>${i.descricao}</td></tr>`).join('');
}

// Form Savers
async function savePaciente(e) {
    e.preventDefault();
    await API.post('/api/pacientes', { nome: document.getElementById('pac-nome').value, cpf: document.getElementById('pac-cpf').value });
    closeModal('pacienteModal');
    e.target.reset();
    loadPacientes();
}

async function saveMedico(e) {
    e.preventDefault();
    await API.post('/api/medicos', { nome: document.getElementById('med-nome').value, crm: document.getElementById('med-crm').value });
    closeModal('medicoModal');
    e.target.reset();
    loadMedicos();
}

async function saveHospital(e) {
    e.preventDefault();
    await API.post('/api/hospitals', { nome: document.getElementById('hosp-nome').value, endereco: document.getElementById('hosp-end').value });
    closeModal('hospitalModal');
    e.target.reset();
    loadHospitais();
}

async function saveTipo(e) {
    e.preventDefault();
    await API.post('/api/tipocirurgias', { nome: document.getElementById('tipo-nome').value, descricao: document.getElementById('tipo-desc').value });
    closeModal('tipoModal');
    e.target.reset();
    loadTipos();
}

async function saveCirurgia(e) {
    e.preventDefault();
    // Reconstructing relations for Spring Data REST / JPA mapping
    const cirurgia = {
        paciente: { id: document.getElementById('cir-paciente').value },
        medico: { id: document.getElementById('cir-medico').value },
        hospital: { id: document.getElementById('cir-hospital').value },
        tipoCirurgia: { id: document.getElementById('cir-tipo').value },
        dataHora: document.getElementById('cir-data').value,
        status: 'AGENDADA'
    };
    await API.post('/api/cirurgias', cirurgia);
    closeModal('cirurgiaModal');
    e.target.reset();
    loadCirurgias();
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadCirurgias();
});

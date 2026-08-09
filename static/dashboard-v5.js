const dashboardRoot = document.getElementById('dashboard-root');

dashboardRoot.innerHTML = `
<div class="dashboard-shell">
  <div id="dashboard-content">
    <header class="dash-heading">
      <div><span class="dash-kicker">Resumo financeiro</span><h1>Visão geral do mês</h1></div>
      <span class="dash-period" id="dash-period">Mês atual</span>
    </header>
    <section class="kpi-grid">
      <article class="kpi-card"><span class="kpi-label">Renda total</span><strong class="kpi-value" id="renda-val">R$ 0,00</strong><span class="kpi-caption">Base mensal cadastrada</span></article>
      <article class="kpi-card"><span class="kpi-label">Gastos realizados</span><strong class="kpi-value" id="gasto-val">R$ 0,00</strong><span class="kpi-caption">Despesas pagas no período</span></article>
      <article class="kpi-card balance"><span class="kpi-label">Saldo projetado</span><strong class="kpi-value" id="saldo-val">R$ 0,00</strong><span class="kpi-caption">Após gastos e pendências</span></article>
      <article class="kpi-card burn"><span class="kpi-label">Renda comprometida</span><strong class="kpi-value" id="burn-val">0%</strong><span class="kpi-caption">Gastos realizados e pendências</span></article>
    </section>
    <section class="dashboard-grid">
      <article class="dash-card">
        <div class="dash-card-header"><h2>Composição do caixa</h2><p class="dash-card-subtitle">Realizado, pendente e disponível</p></div>
        <div class="chart-wrap cashflow-wrap"><canvas id="chartFluxoCaixa"></canvas></div>
      </article>
      <article class="dash-card">
        <div class="dash-card-header"><h2>Gastos por categoria</h2><p class="dash-card-subtitle">Onde seu dinheiro foi utilizado</p></div>
        <div class="chart-wrap"><canvas id="chartCategories"></canvas></div>
      </article>
      <article class="dash-card rule-card">
        <div class="dash-card-header"><h2>Regra 50/30/20</h2><p class="dash-card-subtitle">Valores reais comparados ao recomendado sobre sua renda</p></div>
        <div class="rule-grid" id="rule-grid"></div>
      </article>
    </section>
  </div>
</div>`;

let cashflowChart;
let categoriesChart;
let lastShowState = null;
const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
const money = (value) => currency.format(Number(value) || 0);

function renderRule(data) {
    const rule = data.regra_50_30_20 || {};
    const renda = Number(data.renda) || 0;
    const definitions = [
        { name: 'Necessidades', target: 50, color: '#38bdf8' },
        { name: 'Desejos', target: 30, color: '#a78bfa' },
        { name: 'Futuro', target: 20, color: '#34d399' }
    ];
    document.getElementById('rule-grid').innerHTML = definitions.map((item) => {
        const value = Number(rule[item.name]) || 0;
        const ideal = renda * item.target / 100;
        const usage = ideal ? value / ideal * 100 : 0;
        const status = usage > 100 ? `${Math.round(usage - 100)}% acima do recomendado` : `${Math.round(usage)}% do limite recomendado`;
        return `<div class="rule-item">
          <div class="rule-topline"><span class="rule-name">${item.name}</span><span class="rule-target">Meta ${item.target}% · ${money(ideal)}</span></div>
          <strong class="rule-value">${money(value)}</strong>
          <div class="progress-track"><div class="progress-value" style="--progress-color:${item.color};width:${Math.min(100, usage)}%"></div></div>
          <span class="rule-status">${status}</span>
        </div>`;
    }).join('');
}

function renderCashflow(data) {
    const summary = data.resumo_fluxo || {};
    const values = [
        Number(summary['Gastos Efetuados']) || 0,
        Number(summary['Gastos Pendentes']) || 0,
        Math.max(0, Number(summary['Saldo Livre']) || 0)
    ];
    if (values.every((value) => value === 0)) values[2] = .01;
    if (cashflowChart) {
        cashflowChart.data.datasets[0].data = values;
        cashflowChart.update();
        return;
    }
    cashflowChart = new Chart(document.getElementById('chartFluxoCaixa'), {
        type: 'doughnut',
        data: { labels: ['Realizados', 'Pendentes', 'Saldo livre'], datasets: [{ data: values, backgroundColor: ['#fb7185', '#fbbf24', '#2dd4bf'], borderColor: '#101d30', borderWidth: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: {
            legend: { position: 'bottom', labels: { color: '#a8b6c8', padding: 16, usePointStyle: true } },
            tooltip: { callbacks: { label: (context) => ` ${money(context.raw)}` } }
        }}
    });
}

function renderCategories(data) {
    const categories = data.categorias || [];
    const labels = categories.map((item) => item.categoria);
    const values = categories.map((item) => Number(item.total) || 0);
    if (categoriesChart) {
        categoriesChart.data.labels = labels;
        categoriesChart.data.datasets[0].data = values;
        categoriesChart.update();
        return;
    }
    categoriesChart = new Chart(document.getElementById('chartCategories'), {
        type: 'bar',
        data: { labels, datasets: [{ data: values, backgroundColor: '#6366f1', hoverBackgroundColor: '#818cf8', borderRadius: 7, borderSkipped: false, maxBarThickness: 52 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: labels.length > 4 ? 'y' : 'x',
            scales: {
                x: { beginAtZero: true, ticks: { color: '#8292a8' }, grid: { color: 'rgba(148,163,184,.06)' }, border: { display: false } },
                y: { beginAtZero: true, ticks: { color: '#a8b6c8' }, grid: { display: false }, border: { display: false } }
            },
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => ` ${money(context.raw)}` } } }
        }
    });
}

function controlVisibility(show) {
    const standalone = document.body.classList.contains('dashboard-only-layout');
    const shouldShow = show || standalone;
    if (shouldShow === lastShowState) return;
    lastShowState = shouldShow;
    if (standalone) return;
    const dash = document.getElementById('dashboard-pane');
    const chat = document.getElementById('chat-pane');
    const resizer = document.getElementById('drag-resizer');
    const button = document.getElementById('btn-open-dash');
    if (!dash || !chat) return;
    dash.style.display = shouldShow ? 'block' : 'none';
    resizer.style.display = shouldShow ? 'block' : 'none';
    chat.style.flex = shouldShow ? '0 0 43%' : '1';
    if (button) button.style.display = shouldShow ? 'none' : (window.isChainlitLoaded ? 'block' : 'none');
}

async function updateDashboard() {
    try {
        const response = await fetch('/api/dashboard_data', { cache: 'no-store' });
        if (!response.ok) {
            if (response.status === 401) window.location.href = '/';
            return;
        }
        const data = await response.json();
        document.getElementById('renda-val').textContent = money(data.renda);
        document.getElementById('gasto-val').textContent = money(data.total_gasto);
        document.getElementById('saldo-val').textContent = money(data.saldo_livre);
        document.getElementById('burn-val').textContent = `${Number(data.burn_rate || 0).toFixed(1).replace('.', ',')}%`;
        document.getElementById('dash-period').textContent = new Date().toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
        renderCashflow(data);
        renderCategories(data);
        renderRule(data);
        controlVisibility(data.show_dashboard);
    } catch (error) {
        console.error('Não foi possível atualizar o dashboard.', error);
    }
}

updateDashboard();
window.setInterval(updateDashboard, 3000);

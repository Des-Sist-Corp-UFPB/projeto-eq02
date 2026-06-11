const renderDashboardHtml = () => `
    <div id="welcome-msg" style="display:flex; justify-content:center; align-items:center; height:100%; text-align:center; flex-direction:column; color:#94a3b8;">
        <h2>Bem-vindo ao FinancIA's!</h2>
        <p>Converse com o agente na lateral. <br>Seus gráficos aparecerão aqui quando você solicitar resumos, visualizar gastos ou simular investimentos.</p>
    </div>
    
    <!-- TELA 1: FLUXO DE CAIXA -->
    <div id="dash-content-fluxo" style="display:none; width: 100%;">
        <div class="dash-header">
            <h1>Visão Geral do Mês</h1>
            <div class="kpi-row">
                <div class="kpi-card">
                    <h3>Renda Total</h3>
                    <p id="renda-val">R$ 0,00</p>
                </div>
                <div class="kpi-card">
                    <h3>Total Gasto (Mês)</h3>
                    <p id="gasto-val">R$ 0,00</p>
                </div>
                <div class="kpi-card highlight">
                    <h3>Saldo Livre Projetado</h3>
                    <p id="saldo-val">R$ 0,00</p>
                </div>
            </div>
        </div>
        <div class="charts-row">
            <div class="chart-box">
                <h3>Composição do Fluxo de Caixa</h3>
                <canvas id="chartFluxoCaixa"></canvas>
            </div>
            <div class="chart-box">
                <h3>Gastos por Categoria</h3>
                <canvas id="chartCategories"></canvas>
            </div>
        </div>
    </div>

    <!-- TELA 2: INVESTIMENTOS -->
    <div id="dash-content-investimentos" style="display:none; width: 100%;">
        <div class="dash-header">
            <h1>Simulação de Investimentos</h1>
            <div class="kpi-row">
                <div class="kpi-card">
                    <h3>Meses Simulados</h3>
                    <p id="sim-meses">0</p>
                </div>
                <div class="kpi-card highlight">
                    <h3>Total Investido (Bolso)</h3>
                    <p id="sim-investido">R$ 0,00</p>
                </div>
                <div class="kpi-card highlight" style="background-color: rgba(52, 211, 153, 0.1); border-color: rgba(52, 211, 153, 0.3);">
                    <h3>Montante Final (Juros)</h3>
                    <p id="sim-montante" style="color: #34d399;">R$ 0,00</p>
                </div>
            </div>
        </div>
        <div class="charts-row">
            <div class="chart-box" style="width: 100%; display: none;" id="boxChartInvestimentos">
                <h3>Evolução do Patrimônio (Juros Compostos)</h3>
                <canvas id="chartInvestimentos" style="max-height: 400px;"></canvas>
            </div>
            <div class="chart-box" style="width: 100%; display: none;" id="boxChartComparacao">
                <h3 id="titleChartComparacao">Comparação de Sugestões</h3>
                <canvas id="chartComparacao" style="max-height: 400px;"></canvas>
            </div>
        </div>
    </div>
`;

document.getElementById('dashboard-root').innerHTML = renderDashboardHtml();

let chartFluxoInstance = null;
let chartCategoriesInstance = null;
let chartInvestimentosInstance = null;
let chartComparacaoInstance = null;

const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

async function fetchAndUpdateDashboard() {
    try {
        const res = await fetch('/api/dashboard_data');
        if (!res.ok) {
            if(res.status === 401) window.location.href = '/';
            return;
        }
        const data = await res.json();
        
        const isDashboardOnly = document.body.classList.contains('dashboard-only-layout');
        const shouldShow = data.show_dashboard || isDashboardOnly;
        
        if (shouldShow) {
            document.body.classList.add('show-dashboard');
            document.getElementById('welcome-msg').style.display = 'none';
            
            if (data.view === 'investimentos') {
                document.getElementById('dash-content-fluxo').style.display = 'none';
                document.getElementById('dash-content-investimentos').style.display = 'block';
                
                if (data.tool_name === 'sugerir_investimentos' && data.sim_data && data.sim_data.chart_type === 'bar_comparison') {
                    document.getElementById('boxChartInvestimentos').style.display = 'none';
                    document.getElementById('boxChartComparacao').style.display = 'block';
                    
                    document.getElementById('sim-meses').innerText = data.sim_data.meses;
                    document.getElementById('sim-investido').innerText = formatCurrency(data.sim_data.valor_investido_puro);
                    
                    let max_val = Math.max(...data.sim_data.valores);
                    document.getElementById('sim-montante').innerText = formatCurrency(max_val);
                    
                    document.getElementById('titleChartComparacao').innerText = data.sim_data.titulo;
                    updateChartComparacao(data.sim_data);
                    
                } else if (data.sim_data && data.sim_data.montante && data.sim_data.montante.length > 0) {
                    document.getElementById('boxChartComparacao').style.display = 'none';
                    document.getElementById('boxChartInvestimentos').style.display = 'block';
                    
                    let ult = data.sim_data.montante.length - 1;
                    document.getElementById('sim-meses').innerText = data.sim_data.meses.length;
                    document.getElementById('sim-investido').innerText = formatCurrency(data.sim_data.investido[ult]);
                    document.getElementById('sim-montante').innerText = formatCurrency(data.sim_data.montante[ult]);
                    updateChartInvestimentos(data.sim_data);
                }
            } else {
                document.getElementById('dash-content-investimentos').style.display = 'none';
                document.getElementById('dash-content-fluxo').style.display = 'block';
                
                document.getElementById('renda-val').innerText = formatCurrency(data.renda);
                document.getElementById('gasto-val').innerText = formatCurrency(data.total_gasto);
                document.getElementById('saldo-val').innerText = formatCurrency(data.saldo_livre);
                
                const saldoEl = document.getElementById('saldo-val');
                if (data.saldo_livre < 0) {
                    saldoEl.style.color = '#ef4444'; 
                } else {
                    saldoEl.style.color = '#38bdf8'; 
                }
                
                updateChartsFluxo(data);
            }
        } else {
            document.body.classList.remove('show-dashboard');
            document.getElementById('welcome-msg').style.display = 'flex';
            document.getElementById('dash-content-fluxo').style.display = 'none';
            document.getElementById('dash-content-investimentos').style.display = 'none';
        }
    } catch (e) {
        console.error('Erro ao atualizar dashboard', e);
    }
}

function updateChartsFluxo(data) {
    const ctxFluxo = document.getElementById('chartFluxoCaixa').getContext('2d');
    
    let valGasto = data.resumo_fluxo['Gastos Efetuados'];
    let valPendente = data.resumo_fluxo['Gastos Pendentes'];
    let valSobra = data.resumo_fluxo['Saldo Livre'];
    
    if (valGasto === 0 && valPendente === 0 && valSobra <= 0) {
        valSobra = 0.01; 
    }

    const dataFluxo = [valGasto, valPendente, Math.max(0, valSobra)];
    
    if (chartFluxoInstance) {
        chartFluxoInstance.data.datasets[0].data = dataFluxo;
        chartFluxoInstance.update();
    } else {
        chartFluxoInstance = new Chart(ctxFluxo, {
            type: 'doughnut',
            data: {
                labels: ['Gastos Efetuados', 'Contas Pendentes', 'Saldo Livre'],
                datasets: [{
                    data: dataFluxo,
                    backgroundColor: ['#ef4444', '#f59e0b', '#34d399'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                plugins: { 
                    legend: { labels: { color: '#e2e8f0' }, position: 'bottom' },
                    tooltip: { callbacks: { label: function(context) { return " R$ " + context.raw.toFixed(2).replace('.', ','); } } }
                }
            }
        });
    }

    const ctxCat = document.getElementById('chartCategories').getContext('2d');
    const labels = data.categorias.map(c => c.categoria);
    const values = data.categorias.map(c => c.total);
    
    if (chartCategoriesInstance) {
        chartCategoriesInstance.data.labels = labels;
        chartCategoriesInstance.data.datasets[0].data = values;
        chartCategoriesInstance.update();
    } else {
        chartCategoriesInstance = new Chart(ctxCat, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Gasto no Mês',
                    data: values,
                    backgroundColor: '#818cf8',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
}

function updateChartInvestimentos(simData) {
    const ctxInv = document.getElementById('chartInvestimentos').getContext('2d');
    
    if (chartInvestimentosInstance) {
        chartInvestimentosInstance.data.labels = simData.meses.map(m => "Mês " + m);
        chartInvestimentosInstance.data.datasets[0].data = simData.montante;
        chartInvestimentosInstance.data.datasets[1].data = simData.investido;
        chartInvestimentosInstance.update();
    } else {
        chartInvestimentosInstance = new Chart(ctxInv, {
            type: 'line',
            data: {
                labels: simData.meses.map(m => "Mês " + m),
                datasets: [
                    {
                        label: 'Montante com Juros',
                        data: simData.montante,
                        borderColor: '#34d399',
                        backgroundColor: 'rgba(52, 211, 153, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Total Investido (Sem Juros)',
                        data: simData.investido,
                        borderColor: '#94a3b8',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        fill: false,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        ticks: { color: '#94a3b8' }, 
                        grid: { color: 'rgba(255,255,255,0.05)' } 
                    },
                    x: { 
                        ticks: { color: '#94a3b8', maxTicksLimit: 12 }, 
                        grid: { display: false } 
                    }
                },
                plugins: { legend: { labels: { color: '#e2e8f0' } } }
            }
        });
    }
}

function updateChartComparacao(simData) {
    const ctxComp = document.getElementById('chartComparacao').getContext('2d');
    
    if (chartComparacaoInstance) {
        chartComparacaoInstance.data.labels = simData.labels;
        chartComparacaoInstance.data.datasets[0].data = simData.valores;
        chartComparacaoInstance.update();
    } else {
        chartComparacaoInstance = new Chart(ctxComp, {
            type: 'bar',
            data: {
                labels: simData.labels,
                datasets: [{
                    label: 'Montante Projetado',
                    data: simData.valores,
                    backgroundColor: '#38bdf8',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        ticks: { color: '#94a3b8' }, 
                        grid: { color: 'rgba(255,255,255,0.05)' } 
                    },
                    x: { 
                        ticks: { color: '#94a3b8' }, 
                        grid: { display: false } 
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
}

// Primeira chamada imediata
fetchAndUpdateDashboard();

// Magia do Polling: Atualiza silenciosamente a cada 3 segundos
setInterval(fetchAndUpdateDashboard, 3000);

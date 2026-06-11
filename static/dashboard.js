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
                <div style="position: relative; height: 250px; width: 100%; display: flex; justify-content: center;">
                    <canvas id="chartFluxoCaixa"></canvas>
                </div>
            </div>
            <div class="chart-box" style="display: flex; flex-direction: column;">
                <h3>Gastos por Categoria</h3>
                <div style="position: relative; flex: 1; min-height: 250px; width: 100%;">
                    <canvas id="chartCategories"></canvas>
                </div>
            </div>
            <div class="chart-box" style="flex: 1 1 100%; display: flex; flex-direction: column;">
                <h3>Histórico de Saldo Mensal</h3>
                <div style="position: relative; flex: 1; min-height: 250px; width: 100%;">
                    <canvas id="chartHistorico"></canvas>
                </div>
            </div>
        </div>
    </div>

`;

document.getElementById('dashboard-root').innerHTML = renderDashboardHtml();

let chartFluxoInstance = null;
let chartCategoriesInstance = null;
let chartHistoricoInstance = null;

const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

let lastShowState = null;

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
        
        // --- 1. SEMPRE ATUALIZA E MOSTRA OS DADOS DE FLUXO DE CAIXA ---
        document.getElementById('welcome-msg').style.display = 'none';
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

        // --- 2. CONTROLE DE VISIBILIDADE DO PAINEL APENAS NAS TRANSIÇÕES ---
        if (shouldShow !== lastShowState) {
            lastShowState = shouldShow;
            
            if (!isDashboardOnly) {
                const dashPane = document.getElementById('dashboard-pane');
                const chatPane = document.getElementById('chat-pane');
                const resizer = document.getElementById('drag-resizer');
                const btnOpenDash = document.getElementById('btn-open-dash');
                
                if (dashPane && chatPane) {
                    if (shouldShow) {
                        // AUTO-ABRIR O PAINEL
                        dashPane.style.display = 'block';
                        resizer.style.display = 'block';
                        if (btnOpenDash) btnOpenDash.style.display = 'none';
                        chatPane.style.flex = '0 0 45%';
                        dashPane.style.flex = '1';
                    } else {
                        // AUTO-FECHAR O PAINEL
                        dashPane.style.display = 'none';
                        resizer.style.display = 'none';
                        chatPane.style.flex = '1';
                    }
                }
            }
        }
        
        // Mantém a avaliação do botão Abrir Dashboard contínua caso a variável de carregamento mude
        if (!shouldShow && !isDashboardOnly) {
            const btnOpenDash = document.getElementById('btn-open-dash');
            if (btnOpenDash) {
                btnOpenDash.style.display = window.isChainlitLoaded ? 'block' : 'none';
            }
        }

    } catch (e) {
        console.error('Erro ao atualizar dashboard', e);
    }
}

function updateChartsFluxo(data) {
    const ctxFluxo = document.getElementById('chartFluxoCaixa').getContext('2d');
    
    let valGasto = 0, valPendente = 0, valSobra = 0;
    if (data.resumo_fluxo) {
        valGasto = data.resumo_fluxo['Gastos Efetuados'] || 0;
        valPendente = data.resumo_fluxo['Gastos Pendentes'] || 0;
        valSobra = data.resumo_fluxo['Saldo Livre'] || 0;
    } else if (data.regra_50_30_20) {
        valGasto = data.regra_50_30_20['Necessidades (50%)'] || 0;
        valPendente = data.regra_50_30_20['Desejos (30%)'] || 0;
        valSobra = data.regra_50_30_20['Investimentos (20%)'] || 0;
    }
    
    if (valGasto === 0 && valPendente === 0 && valSobra <= 0) {
        valSobra = 0.01; 
    }

    const dataFluxo = [valGasto, valPendente, Math.max(0, valSobra)];
    
    if (chartFluxoInstance) {
        chartFluxoInstance.data.datasets[0].data = dataFluxo;
        chartFluxoInstance.update();
    } else {
        // Doughnut com bordas vívidas e transparência
        chartFluxoInstance = new Chart(ctxFluxo, {
            type: 'doughnut',
            data: {
                labels: ['Gastos Efetuados', 'Contas Pendentes', 'Saldo Livre'],
                datasets: [{
                    data: dataFluxo,
                    backgroundColor: ['rgba(244, 63, 94, 0.8)', 'rgba(251, 191, 36, 0.8)', 'rgba(45, 212, 191, 0.8)'],
                    borderColor: ['#f43f5e', '#fbbf24', '#2dd4bf'],
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                cutout: '65%',
                plugins: { 
                    legend: { labels: { color: '#e2e8f0', padding: 20 }, position: 'bottom' },
                    tooltip: { 
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#38bdf8',
                        padding: 12,
                        callbacks: { label: function(context) { return " R$ " + context.raw.toFixed(2).replace('.', ','); } } 
                    }
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
        // Criação de Gradiente para as Barras
        const gradientBar = ctxCat.createLinearGradient(0, 0, 0, 400);
        gradientBar.addColorStop(0, '#8b5cf6'); // Roxo brilhante
        gradientBar.addColorStop(1, '#3b82f6'); // Azul brilhante

        chartCategoriesInstance = new Chart(ctxCat, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Gasto no Mês',
                    data: values,
                    backgroundColor: gradientBar,
                    borderRadius: 8,
                    borderWidth: 0,
                    hoverBackgroundColor: '#c084fc'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        ticks: { color: '#94a3b8' }, 
                        grid: { color: 'rgba(255,255,255,0.02)' },
                        border: { display: false }
                    },
                    x: { 
                        ticks: { color: '#94a3b8' }, 
                        grid: { display: false },
                        border: { display: false }
                    }
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', titleColor: '#38bdf8', padding: 12 }
                }
            }
        });
    }

    // Gráfico de Linha (Histórico Fake/Mockado para estética)
    // Simulando 6 meses do saldo
    const ctxHist = document.getElementById('chartHistorico').getContext('2d');
    if (!chartHistoricoInstance) {
        const histGradient = ctxHist.createLinearGradient(0, 0, 0, 400);
        histGradient.addColorStop(0, 'rgba(139, 92, 246, 0.4)'); // Roxo transparente no topo
        histGradient.addColorStop(1, 'rgba(139, 92, 246, 0.0)'); // Transparente em baixo

        // Pegando o saldo atual como base para o mock
        let baseSaldo = valSobra;
        let mockData = [
            baseSaldo * 0.5, 
            baseSaldo * 0.7, 
            baseSaldo * 0.4, 
            baseSaldo * 0.9, 
            baseSaldo * 0.8, 
            baseSaldo
        ];

        chartHistoricoInstance = new Chart(ctxHist, {
            type: 'line',
            data: {
                labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Atual'],
                datasets: [{
                    label: 'Evolução do Saldo Livre',
                    data: mockData,
                    borderColor: '#a855f7', // Roxo Neon
                    borderWidth: 3,
                    backgroundColor: histGradient,
                    fill: true,
                    tension: 0.4, // Curvas suaves
                    pointBackgroundColor: '#0b0f19',
                    pointBorderColor: '#c084fc',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        ticks: { color: '#94a3b8' }, 
                        grid: { color: 'rgba(255,255,255,0.02)' },
                        border: { display: false }
                    },
                    x: { 
                        ticks: { color: '#94a3b8' }, 
                        grid: { display: false },
                        border: { display: false }
                    }
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', titleColor: '#a855f7', padding: 12 }
                }
            }
        });
    } else {
        // Apenas atualiza o último ponto do gráfico falso
        let len = chartHistoricoInstance.data.datasets[0].data.length;
        chartHistoricoInstance.data.datasets[0].data[len-1] = valSobra;
        chartHistoricoInstance.update();
    }
}



// Primeira chamada imediata
fetchAndUpdateDashboard();

// Magia do Polling: Atualiza silenciosamente a cada 3 segundos
setInterval(fetchAndUpdateDashboard, 3000);

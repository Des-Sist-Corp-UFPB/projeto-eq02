const renderDashboardHtml = () => `
    <div id="welcome-msg" style="display:flex; justify-content:center; align-items:center; height:100%; text-align:center; flex-direction:column; color:#94a3b8;">
        <h2>Bem-vindo ao FinancIA's!</h2>
        <p>Converse com o agente na lateral. <br>Seus gráficos aparecerão aqui quando você solicitar resumos, visualizar gastos ou cadastrar contas.</p>
    </div>
    <div id="dash-content" style="display:none;">
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
                <h3>Distribuição 50/30/20</h3>
                <canvas id="chart503020"></canvas>
            </div>
            <div class="chart-box">
                <h3>Gastos por Categoria</h3>
                <canvas id="chartCategories"></canvas>
            </div>
        </div>
    </div>
`;

document.getElementById('dashboard-root').innerHTML = renderDashboardHtml();

let chart503020Instance = null;
let chartCategoriesInstance = null;

const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

async function fetchAndUpdateDashboard() {
    try {
        const res = await fetch('/api/dashboard_data');
        if (!res.ok) {
            // Se der 401, significa que perdeu o cookie de login
            if(res.status === 401) window.location.href = '/';
            return;
        }
        const data = await res.json();
        
        // Verifica se a página é a dashboard_only, nesse caso sempre mostra
        const isDashboardOnly = document.body.classList.contains('dashboard-only-layout');
        const shouldShow = data.show_dashboard || isDashboardOnly;
        
        if (shouldShow) {
            document.getElementById('welcome-msg').style.display = 'none';
            document.getElementById('dash-content').style.display = 'block';
        } else {
            document.getElementById('welcome-msg').style.display = 'flex';
            document.getElementById('dash-content').style.display = 'none';
        }
        
        // Atualiza KPIs
        document.getElementById('renda-val').innerText = formatCurrency(data.renda);
        document.getElementById('gasto-val').innerText = formatCurrency(data.total_gasto);
        document.getElementById('saldo-val').innerText = formatCurrency(data.saldo_livre);
        
        // Modifica a cor do saldo livre se for negativo
        const saldoEl = document.getElementById('saldo-val');
        if (data.saldo_livre < 0) {
            saldoEl.style.color = '#ef4444'; // Vermelho
        } else {
            saldoEl.style.color = '#38bdf8'; // Azul normal
        }
        
        updateCharts(data);
    } catch (e) {
        console.error('Erro ao atualizar dashboard', e);
    }
}

function updateCharts(data) {
    const ctx503020 = document.getElementById('chart503020').getContext('2d');
    
    // Tratamento para evitar gráfico vazio se não tiver gasto
    let valNec = data.regra_50_30_20.Necessidades;
    let valDes = data.regra_50_30_20.Desejos;
    let valFut = data.regra_50_30_20.Futuro;
    
    // Se não há gastos definidos para a regra ainda, mostramos algo vazio ou zerado
    if (valNec === 0 && valDes === 0 && valFut === 0) {
        valFut = 0.01; // Truque para o Chart.js desenhar um anel cinza
    }

    const data503020 = [valNec, valDes, valFut];
    
    if (chart503020Instance) {
        chart503020Instance.data.datasets[0].data = data503020;
        chart503020Instance.update();
    } else {
        chart503020Instance = new Chart(ctx503020, {
            type: 'doughnut',
            data: {
                labels: ['Necessidades (50%)', 'Desejos (30%)', 'Futuro (20%)'],
                datasets: [{
                    data: data503020,
                    backgroundColor: ['#38bdf8', '#f472b6', '#34d399'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                plugins: { 
                    legend: { labels: { color: '#e2e8f0' }, position: 'bottom' } 
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
                    label: 'Gasto no Mês (R$)',
                    data: values,
                    backgroundColor: '#818cf8',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
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

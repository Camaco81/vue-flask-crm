<template>
  <div class="analytics-container">
    <h1 class="page-title">Analíticas de Vendedor</h1> <BackButton /> 
    <p class="subtitle">Aquí tienes un resumen del rendimiento de tus ventas.</p>
    
    <div v-if="loading" class="loading-state">
      Cargando analíticas...
    </div>

    <div v-if="error" class="error-state">
      {{ error }}
    </div>

    <div v-if="!loading && !error" class="metrics-grid">
      <div class="metric-card gradient-1">
        <h2 class="metric-value">{{ formatNumber(analytics.total_customers) }}</h2>
        <p class="metric-label">Clientes Totales</p>
      </div>
      <div class="metric-card gradient-2">
        <h2 class="metric-value">{{ formatNumber(analytics.total_products) }}</h2>
        <p class="metric-label">Productos</p>
      </div>
      <div class="metric-card gradient-3">
        <h2 class="metric-value">{{ formatNumber(analytics.total_today_sales) }}</h2>
        <p class="metric-label">Ventas Hoy</p>
      </div>
      <div class="metric-card gradient-4">
        <h2 class="metric-value">${{ formatNumber(analytics.total_revenue) }}</h2>
        <p class="metric-label">Ingresos Totales</p>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../../axios';
import BackButton from './BackButton.vue';

export default {
    name: 'AnalyticsComponent',
    data() {
        return {
            analytics: {
                total_customers: 0,
                total_products: 0,
                total_today_sales: 0, // <-- Renombrado para consistencia
                total_revenue: 0,
            },
            loading: false,
            error: null,
        };
    },
    components: {
        BackButton
    },
    async mounted() {
        await this.fetchAnalyticsData(); // <-- Renombrado para ser más explícito
    },
    methods: {
        async fetchAnalyticsData() { // <-- Renombrada la función
            this.loading = true;
            this.error = null;
            
            try {
                // Ejecutar todas las peticiones en paralelo para optimizar la carga
                const [customersRes, productsRes, salesRes] = await Promise.all([
                    apiClient.get('/api/customers'),
                    apiClient.get('/api/products'),
                    apiClient.get('/api/sales') // Endpoint consolidado de ventas
                ]);

                const sales = salesRes.data;

                // --- 1. Clientes y Productos ---
                this.analytics.total_customers = customersRes.data.length;
                this.analytics.total_products = productsRes.data.length;

                // --- 2. Ventas e Ingresos (Calculados a partir de /api/sales) ---
                
                // Cálculo de Ventas Hoy
                const today = new Date().toISOString().split('T')[0];
                const salesToday = sales.filter(sale => 
                    sale.sale_date && String(sale.sale_date).startsWith(today)
                );
                this.analytics.total_today_sales = salesToday.length;

                // Cálculo de Ingresos Totales
                const totalRevenue = sales.reduce((sum, sale) => {
                    const amount = parseFloat(sale.total_amount) || 0;
                    return sum + amount;
                }, 0);

                this.analytics.total_revenue = totalRevenue; 

            } catch (error) {
                console.error("Error al obtener analíticas:", error);
                // Mensaje de error más útil
                this.error = "No se pudieron cargar las analíticas. Verifica tu conexión y el servidor backend."; 
            } finally {
                this.loading = false;
            }
        },
        formatNumber(value) {
            // Formatea un número para que sea legible (ej: 1,234.56)
            // Asegura que los números de moneda tengan 2 decimales.
            const options = value % 1 !== 0 ? { minimumFractionDigits: 2, maximumFractionDigits: 2 } : { maximumFractionDigits: 0 };
            return new Intl.NumberFormat('es-ES', options).format(value);
        }
    },
};
</script>

<style scoped>
.analytics-container {
  padding: 2rem;
  font-family: 'Inter', sans-serif;
  background-color: #f0f4f8;
  min-height: 100vh;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.125rem;
  color: #718096;
  margin-bottom: 2rem;
}

.loading-state, .error-state {
  text-align: center;
  font-size: 1.125rem;
  color: #718096;
  padding: 2rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.metric-card {
  background-color: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  text-align: center;
  color: white;
}

.metric-card.gradient-1 {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.metric-card.gradient-2 {
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
}

.metric-card.gradient-3 {
  background: linear-gradient(135deg, #84fab0, #8fd3f4);
}

.metric-card.gradient-4 {
  background: linear-gradient(135deg, #a18cd1, #fbc2eb);
}

.metric-value {
  font-size: 3rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.metric-label {
  font-size: 1rem;
  font-weight: 500;
  opacity: 0.8;
  margin: 0;
}
</style>
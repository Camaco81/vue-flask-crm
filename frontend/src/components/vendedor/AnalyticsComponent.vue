<template>
  <div class="analytics-container">
    <h1 class="page-title">Dashboard</h1>
    <BackButton /> <p class="subtitle">Aquí tienes un resumen de tu panel de control</p>
    
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
        <h2 class="metric-value">{{ formatNumber(analytics.total_today_orders) }}</h2>
        <p class="metric-label">Pedidos Hoy</p>
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
        total_today_orders: 0,
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
    await this.fetchAnalytics();
  },
  methods: {
    async fetchAnalytics() {
      this.loading = true;
      this.error = null;
      try {
        const response = await apiClient.get('/api/analytics');
        this.analytics = response.data;
      } catch (error) {
        console.error("Error al obtener analíticas:", error);
        this.error = "No se pudo cargar las analíticas. Asegúrate de que el backend está corriendo.";
      } finally {
        this.loading = false;
      }
    },
    formatNumber(value) {
      // Formatea un número para que sea legible (ej: 1,234.56)
      return new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 }).format(value);
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
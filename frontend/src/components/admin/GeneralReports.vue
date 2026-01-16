<template>
  <div class="admin-general-reports">
    <div class="reports-header">
      <button @click="goBack" class="back-btn">
        <i class="fas fa-arrow-left"></i> Volver
      </button>
      <div class="header-content">
        <h1><i class="fas fa-chart-line"></i> Reportes Generales de Ventas</h1>
        <p class="subtitle">Monitoreo completo del rendimiento del negocio (Tenant)</p>
      </div>
    </div>

    <div class="filters-section">
      <div class="filter-group">
        <label for="date-filter"><i class="fas fa-calendar-alt"></i> Filtrar por fecha:</label>
        <select id="date-filter" v-model="dateFilter" @change="applyDateFilter">
          <option value="all">Todas las fechas</option>
          <option value="today">Hoy</option>
          <option value="yesterday">Ayer</option>
          <option value="week">Esta semana</option>
          <option value="month">Este mes</option>
          <option value="year">Este año</option>
        </select>
      </div>
      <div v-if="dateFilter !== 'all'" class="filter-summary">
        <span class="filter-badge">
          <i class="fas fa-filter"></i> {{ getDateFilterLabel() }}
        </span>
      </div>
    </div>

    <div v-if="isLoading" class="loading-container">
      <div class="spinner"></div>
      <p>Cargando reportes...</p>
    </div>
    
    <div v-if="error" class="error-alert">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
    </div>

    <div v-if="!isLoading && !error" class="reports-content">
      
      <div v-if="allOrders.length > 0" class="summary-cards">
        <div class="summary-card">
          <div class="card-icon total-orders">
            <i class="fas fa-shopping-cart"></i>
          </div>
          <h3>{{ filteredOrders.length }}</h3>
          <p>Órdenes Totales</p>
        </div>
        
        <div class="summary-card">
          <div class="card-icon total-revenue">
            <i class="fas fa-dollar-sign"></i>
          </div>
          <h3>${{ formatNumber(totalGlobalSalesAmount) }}</h3>
          <p>Ingresos Totales</p>
        </div>
        
        <div class="summary-card">
          <div class="card-icon top-seller">
            <i class="fas fa-crown"></i>
          </div>
          <h3>{{ topSeller.name || 'Sin ventas' }}</h3>
          <p>Mejor Vendedor</p>
          <small v-if="topSeller.sales > 0">${{ formatNumber(topSeller.sales) }}</small>
        </div>
      </div>

      <div v-if="allOrders.length > 0" class="chart-section">
        <h3><i class="fas fa-trophy"></i> Ranking de Vendedores</h3>
        <div class="chart-container">
          <canvas ref="topSellersChart"></canvas>
        </div>
      </div>

      <div v-if="allOrders.length > 0" class="sales-summary">
        <h3><i class="fas fa-users"></i> Desempeño por Vendedor</h3>
        <div class="sellers-grid">
          <div v-for="(sales, seller) in salesBySeller" :key="seller" class="seller-card">
            <div class="seller-avatar">
              {{ getInitials(seller) }}
            </div>
            <div class="seller-info">
              <h4>{{ seller }}</h4>
              <p class="seller-revenue">${{ formatNumber(sales) }}</p>
              <p class="seller-orders">
                {{ getSellerOrdersCount(seller) }} órdenes
              </p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredOrders.length > 0" class="orders-section">
        <div class="section-header">
          <h3><i class="fas fa-list-alt"></i> Detalle de Órdenes ({{ filteredOrders.length }})</h3>
        </div>
        
        <div class="orders-grid">
          <div v-for="order in filteredOrders" :key="order.id" class="order-card">
            <div class="order-header">
              <span class="order-id">#{{ order.id.substring(0,8) }}</span>
              <span :class="['order-status', getStatusClass(order.status)]">
                {{ order.status }}
              </span>
            </div>
            
            <div class="order-body">
              <div class="order-info">
                <h4>{{ order.customer_name }}</h4>
                <p class="order-seller">
                  <i class="fas fa-id-badge"></i> 
                  <strong>Vendedor:</strong> {{ order.seller_name || order.seller_email || 'Personal del Sistema' }}
                </p>
                <p class="order-date">
                  <i class="fas fa-calendar"></i> {{ formatDate(order.sale_date) }}
                </p>
              </div>
              <div class="order-amount">
                <h3>${{ formatNumber(order.total_amount_usd) }}</h3>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="allOrders.length === 0" class="no-data-message">
        <i class="fas fa-chart-pie"></i>
        <h3>Aún no hay órdenes registradas</h3>
        <p>No se han registrado ventas en el sistema para este negocio.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js';
import axios from '../../axios.js';

Chart.register(...registerables);

export default {
  name: 'AdminGeneralReports',
  data() {
    return {
      allOrders: [],
      filteredOrders: [],
      isLoading: false,
      error: '',
      dateFilter: 'all',
      topSellersChart: null
    };
  },
  computed: {
    totalGlobalSalesAmount() {
      return this.filteredOrders.reduce((sum, order) => 
        sum + parseFloat(order.total_amount_usd || 0), 0
      );
    },
    salesBySeller() {
      const sales = {};
      this.filteredOrders.forEach(order => {
        // Priorizamos el nombre real del vendedor enviado por el backend
        const sellerKey = order.seller_name || order.seller_email || 'Personal del Sistema';
        if (!sales[sellerKey]) {
          sales[sellerKey] = 0;
        }
        sales[sellerKey] += parseFloat(order.total_amount_usd || 0);
      });
      return sales;
    },
    topSeller() {
      let top = { name: '', sales: 0 };
      Object.entries(this.salesBySeller).forEach(([name, sales]) => {
        if (sales > top.sales) {
          top = { name, sales };
        }
      });
      return top;
    }
  },
  methods: {
    goBack() {
      this.$router.go(-1);
    },
    async fetchAllOrders() {
      this.isLoading = true;
      this.error = '';
      try {
        const response = await axios.get('/api/sales');
        this.allOrders = response.data;
        this.filteredOrders = [...this.allOrders];
        this.$nextTick(() => {
          this.renderTopSellersChart();
        });
      } catch (error) {
        this.error = 'No se pudieron cargar los reportes. Verifica tus permisos.';
      } finally {
        this.isLoading = false;
      }
    },
    applyDateFilter() {
      const now = new Date();
      let startDate = new Date();

      if (this.dateFilter === 'all') {
        this.filteredOrders = [...this.allOrders];
        this.renderTopSellersChart();
        return;
      }

      switch (this.dateFilter) {
        case 'today': {
          startDate.setHours(0, 0, 0, 0);
          break;
        }
        case 'yesterday': {
          startDate.setDate(now.getDate() - 1);
          startDate.setHours(0, 0, 0, 0);
          const yesterdayEnd = new Date(startDate);
          yesterdayEnd.setHours(23, 59, 59, 999);
          this.filteredOrders = this.allOrders.filter(order => {
            const d = new Date(order.sale_date);
            return d >= startDate && d <= yesterdayEnd;
          });
          this.renderTopSellersChart();
          return;
        }
        case 'week': {
          startDate.setDate(now.getDate() - 7);
          break;
        }
        case 'month': {
          startDate.setMonth(now.getMonth() - 1);
          break;
        }
        case 'year': {
          startDate.setFullYear(now.getFullYear() - 1);
          break;
        }
      }

      this.filteredOrders = this.allOrders.filter(order => {
        const orderDate = new Date(order.sale_date);
        return orderDate >= startDate && orderDate <= now;
      });
      this.renderTopSellersChart();
    },
    renderTopSellersChart() {
      if (this.topSellersChart) this.topSellersChart.destroy();
      const ctx = this.$refs.topSellersChart?.getContext('2d');
      if (!ctx || this.filteredOrders.length === 0) return;

      const sellersData = Object.entries(this.salesBySeller)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

      this.topSellersChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: sellersData.map(([name]) => name.split(' ')[0]), 
          datasets: [{
            label: 'Ingresos ($)',
            data: sellersData.map(([, sales]) => sales),
            backgroundColor: 'rgba(102, 126, 234, 0.8)',
            borderColor: '#667eea',
            borderWidth: 1,
            borderRadius: 5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } }
        }
      });
    },
    getDateFilterLabel() {
      const labels = { today: 'Hoy', yesterday: 'Ayer', week: 'Esta semana', month: 'Este mes', year: 'Este año' };
      return labels[this.dateFilter] || 'Filtrado';
    },
    formatNumber(val) {
      return parseFloat(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    formatDate(date) {
      return new Date(date).toLocaleDateString();
    },
    getInitials(name) {
      if (!name || name === 'Personal del Sistema') return 'PS';
      return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
    },
    getSellerOrdersCount(sellerName) {
      return this.filteredOrders.filter(order => (order.seller_name || order.seller_email || 'Personal del Sistema') === sellerName).length;
    },
    getStatusClass(status) {
      const s = status.toLowerCase();
      if (s.includes('completado') || s.includes('pagado')) return 'status-completed';
      if (s.includes('pendiente') || s.includes('espera')) return 'status-pending';
      return 'status-cancelled';
    }
  },
  async mounted() {
    await this.fetchAllOrders();
  }
};
</script>

<style scoped>
.admin-general-reports {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Header mejorado */
.reports-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.back-btn {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  color: #495057;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
  transform: translateX(-3px);
}

.header-content h1 {
  color: white;
  margin: 0 0 5px 0;
  font-size: 1.8rem;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-content h1 i {
  color: #667eea;
}

.subtitle {
  color: #dbe4f1;
  margin: 0;
  font-size: 0.95rem;
}

/* Filtros */
.filters-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 25px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.filter-group label {
  font-weight: 600;
  color: #4a5568;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group select {
  padding: 10px 15px;
  border: 1px solid #cbd5e0;
  border-radius: 8px;
  background: white;
  color: #4a5568;
  font-size: 0.95rem;
  cursor: pointer;
  min-width: 200px;
  transition: border-color 0.3s;
}

.filter-group select:focus {
  outline: none;
  border-color: #667eea;
}

.filter-summary {
  margin-top: 10px;
}

.filter-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #e8f4ff;
  color: #667eea;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}

/* Estados */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-alert {
  background: #fed7d7;
  border: 1px solid #fc8181;
  border-radius: 8px;
  padding: 15px;
  margin: 20px 0;
  display: flex;
  align-items: center;
  gap: 15px;
  color: #c53030;
}

.error-alert i {
  font-size: 1.2rem;
}

/* Tarjetas de resumen */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.summary-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  font-size: 1.5rem;
  color: white;
}

.total-orders {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.total-revenue {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.top-seller {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.summary-card h3 {
  font-size: 1.8rem;
  margin: 0 0 8px 0;
  color: #2d3748;
}

.summary-card p {
  margin: 0 0 5px 0;
  color: #718096;
  font-weight: 500;
}

.summary-card small {
  color: #a0aec0;
  font-size: 0.9rem;
}

/* Gráfico */
.chart-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.chart-section h3 {
  margin: 0 0 20px 0;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chart-section h3 i {
  color: #f59e0b;
}

.chart-container {
  position: relative;
  height: 300px;
  width: 100%;
}

/* Vendedores grid */
.sales-summary {
  background: white;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.sales-summary h3 {
  margin: 0 0 20px 0;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 10px;
}

.sellers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.seller-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.seller-card:hover {
  background: white;
  border-color: #cbd5e0;
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
}

.seller-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.seller-info h4 {
  margin: 0 0 5px 0;
  color: #2d3748;
  font-size: 1rem;
}

.seller-revenue {
  margin: 0 0 3px 0;
  color: #667eea;
  font-weight: 600;
  font-size: 1.1rem;
}

.seller-orders {
  margin: 0;
  color: #718096;
  font-size: 0.9rem;
}

/* Órdenes */
.orders-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.section-header {
  margin-bottom: 25px;
}

.section-header h3 {
  margin: 0;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 10px;
}

.orders-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.order-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  background: white;
  transition: all 0.3s ease;
}

.order-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.order-header {
  padding: 15px;
  background: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-id {
  font-weight: 600;
  color: #4a5568;
}

.order-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-cancelled {
  background: #fee2e2;
  color: #991b1b;
}

.status-unknown {
  background: #e5e7eb;
  color: #374151;
}

.order-body {
  padding: 20px;
}

.order-info h4 {
  margin: 0 0 10px 0;
  color: #2d3748;
}

.order-seller, .order-date, .order-time {
  margin: 0 0 8px 0;
  color: #718096;
  display: flex;
  align-items: center;
  gap: 8px;
}

.order-seller i, .order-date i, .order-time i {
  color: #a0aec0;
  width: 16px;
}

.order-amount {
  margin-top: 15px;
  padding: 15px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 8px;
  text-align: center;
}

.order-amount h3 {
  margin: 0;
  font-size: 1.5rem;
}

.order-items {
  padding: 15px;
  border-top: 1px solid #e2e8f0;
}

.items-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.item-tag {
  background: #e8f4ff;
  color: #667eea;
  padding: 4px 10px;
  border-radius: 15px;
  font-size: 0.85rem;
  font-weight: 500;
}

.item-tag.more {
  background: #f1f5f9;
  color: #64748b;
}

/* Sin datos */
.no-data-message {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.no-data-message i {
  font-size: 3rem;
  color: #cbd5e0;
  margin-bottom: 20px;
}

.no-data-message h3 {
  margin: 0 0 10px 0;
  color: #4a5568;
}

.no-data-message p {
  margin: 0;
  color: #a0aec0;
}

/* Responsive */
@media (max-width: 768px) {
  .admin-general-reports {
    padding: 0 15px;
  }
  
  .reports-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .filter-group {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .summary-cards {
    grid-template-columns: 1fr;
  }
  
  .sellers-grid {
    grid-template-columns: 1fr;
  }
  
  .orders-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    height: 250px;
  }
}
</style>
<template>
  <div class="admin-general-reports">
    <h1>Reportes Generales de Ventas</h1>
    <p>Aquí se muestra un resumen de todas las ventas del sistema, incluyendo quién las realizó.</p>

    <div v-if="isLoading" class="loading-message">Cargando reportes de ventas...</div>
    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="!isLoading && !error && allOrders.length === 0" class="no-data-message">
      Aún no hay órdenes registradas en el sistema.
    </div>

    <div v-if="allOrders.length > 0" class="sales-summary">
      <h3>Resumen Global</h3>
      <p>Total de Órdenes: <strong>{{ allOrders.length }}</strong></p>
      <p>Monto Total Vendido en el Sistema: <strong>${{ totalGlobalSalesAmount.toFixed(2) }}</strong></p>
      
      <h4>Ventas por Consultor/Vendedor:</h4>
      <ul class="sales-by-seller-list">
        <li v-for="(sales, seller) in salesBySeller" :key="seller">
          <strong>{{ seller === 'null' ? 'Vendedor Desconocido' : seller }}:</strong> ${{ sales.toFixed(2) }}
        </li>
      </ul>
    </div>

    <div v-if="allOrders.length > 0" class="orders-list">
      <h2>Detalle de Todas las Órdenes</h2>
      <div v-for="order in allOrders" :key="order.id" class="order-card">
        <h3>Orden #{{ order.id }} - Cliente: {{ order.customer_name }}</h3>
        <p><strong>Vendedor/Consultor:</strong> {{ order.seller_email || 'N/A' }} (ID: {{ order.seller_id || 'N/A' }})</p>
        <p><strong>Fecha:</strong> {{ formatDateTime(order.order_date) }}</p>
        <p><strong>Estado:</strong> <span :class="getStatusClass(order.status)">{{ order.status }}</span></p>
        <p><strong>Monto Total:</strong> ${{ order.total_amount.toFixed(2) }}</p>
        
        <div class="order-items">
          <h4>Productos:</h4>
          <ul>
            <li v-for="(item, index) in order.items" :key="index">
              {{ item.product_name }} (x{{ item.quantity }}) - ${{ item.price.toFixed(2) }} c/u
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '../../axios.js'; // Ajusta la ruta a tu instancia de Axios

export default {
  name: 'AdminGeneralReports', // Renombrado para mayor claridad
  data() {
    return {
      allOrders: [],
      isLoading: false,
      error: ''
    };
  },
  computed: {
    totalGlobalSalesAmount() {
      return this.allOrders.reduce((sum, order) => sum + parseFloat(order.total_amount), 0);
    },
    salesBySeller() {
      const sales = {};
      this.allOrders.forEach(order => {
        const seller = order.seller_email || 'null'; // Agrupa por email del vendedor
        if (!sales[seller]) {
          sales[seller] = 0;
        }
        sales[seller] += parseFloat(order.total_amount);
      });
      return sales;
    }
  },
  async created() {
    await this.fetchAllOrders();
  },
  methods: {
    async fetchAllOrders() {
      this.isLoading = true;
      this.error = '';
      try {
        // Un administrador consume /api/orders para ver todas las ventas
        const response = await axios.get('/api/orders'); 
        this.allOrders = response.data;
      } catch (error) {
        console.error('Error al obtener todos los reportes de ventas:', error);
        this.error = error.response?.data?.msg || 'Error al cargar los reportes generales de ventas.';
      } finally {
        this.isLoading = false;
      }
    },
    formatDateTime(dateTimeString) {
      const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      // Asegúrate de que dateTimeString sea válido para Date
      if (!dateTimeString) return 'Fecha desconocida';
      try {
        return new Date(dateTimeString).toLocaleDateString('es-ES', options);
      } catch {
        return 'Fecha inválida';
      }
    },
    getStatusClass(status) {
      return {
        'status-pendiente': status === 'pendiente',
        'status-completado': status === 'completado',
        'status-cancelado': status === 'cancelado',
      };
    }
  }
}
</script>

<style scoped>
.admin-general-reports {
  padding: 20px;
  max-width: 1000px; /* Ancho un poco mayor para más datos */
  margin: 30px auto;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  color: #333;
}

h1 {
  text-align: center;
  color: #007bff;
  margin-bottom: 25px;
}

h2, h3, h4 {
  color: #444;
  margin-bottom: 15px;
}

.loading-message, .error-message, .no-data-message {
  text-align: center;
  padding: 15px;
  border-radius: 5px;
  margin-top: 20px;
}

.loading-message {
  background-color: #e0f7fa;
  color: #007bff;
}

.error-message {
  background-color: #ffe0e0;
  color: #dc3545;
  border: 1px solid #dc3545;
}

.no-data-message {
  background-color: #f0f0f0;
  color: #666;
}

.sales-summary {
  background-color: #f8f9fa;
  border: 1px solid #e2e6ea;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  text-align: center;
}

.sales-summary p {
  font-size: 1.1em;
  margin: 5px 0;
}

.sales-summary strong {
  color: #007bff;
}

.sales-by-seller-list {
  list-style: none;
  padding: 0;
  margin-top: 15px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 15px;
}

.sales-by-seller-list li {
  background-color: #e9ecef;
  padding: 10px 15px;
  border-radius: 5px;
  font-size: 0.95em;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.orders-list {
  margin-top: 30px;
}

.order-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background-color: #fdfdfd;
  box-shadow: 0 1px 5px rgba(0,0,0,0.05);
}

.order-card h3 {
  color: #007bff;
  margin-top: 0;
  margin-bottom: 10px;
}

.order-card p {
  margin-bottom: 5px;
  font-size: 0.95em;
}

.order-items {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px dashed #eee;
}

.order-items h4 {
  color: #555;
  margin-bottom: 8px;
}

.order-items ul {
  list-style-type: disc;
  padding-left: 20px;
  margin-top: 0;
}

.order-items li {
  margin-bottom: 3px;
  font-size: 0.9em;
}

.status-pendiente {
  color: #ffc107; 
  font-weight: bold;
}

.status-completado {
  color: #28a745; 
  font-weight: bold;
}

.status-cancelado {
  color: #dc3545; 
  font-weight: bold;
}
</style>
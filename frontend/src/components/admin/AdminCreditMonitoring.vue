<template>
  <div class="credit-monitoring-container">
    <div class="header-controls">
     <button @click="goBack" class="btn-back">
        ← Regresar
      </button>
    </div> 
    <h1 class="page-title">
      <i class="fas fa-hand-holding-usd"></i>
      Monitoreo de Créditos Pendientes
    </h1>
    
    <p class="page-subtitle">
      Control y seguimiento de cuentas por cobrar. Total de créditos pendientes: 
      <span class="total-pending-amount">${{ totalPendingBalance.toFixed(2) }}</span>
    </p>

    <div class="card credit-list-card">
      <div class="card-header">
        <div class="card-title">
          <h3>Deudas Activas ({{ pendingCredits.length }})</h3>
        </div>
        <div class="card-actions">
          <button @click="fetchCredits" class="refresh-btn" :disabled="loading">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            <span>{{ loading ? 'Actualizando...' : 'Actualizar Lista' }}</span>
          </button>
        </div>
      </div>
      
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Cargando créditos...
      </div>
      
      <div v-else-if="error" class="error-state">
        <i class="fas fa-exclamation-triangle"></i> Error al cargar: {{ error }}
      </div>

      <div v-else-if="pendingCredits.length === 0" class="empty-state">
        <i class="fas fa-check-circle"></i> ¡No hay créditos pendientes por cobrar!
      </div>
      
      <ul v-else class="credit-list">
        <li 
          v-for="credit in pendingCredits" 
          :key="credit.sale_id" 
          :class="['credit-item', getMoraClass(credit.dias_en_mora)]"
        >
          <div class="credit-info-main">
            <div class="customer-info">
              <i class="fas fa-user-circle"></i>
              <strong class="customer-name">{{ credit.customer_name }} (C.I: {{ credit.customer_cedula }})</strong>
              <span class="sale-id">ID Venta: #{{ credit.sale_id.substring(0, 8) }}</span>
            </div>
            
            <div class="balance-info">
              <span class="balance-label">Saldo Pendiente:</span>
              <span class="balance-amount">${{ credit.balance_due_usd.toFixed(2) }}</span>
            </div>
          </div>
          
          <div class="credit-details">
            <div class="detail-item">
              <i class="fas fa-calendar-alt"></i>
              <span>Vence: {{ formatDate(credit.fecha_vencimiento) }}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-calendar-times"></i>
              <span 
                :class="getMoraTextColor(credit.dias_en_mora)"
              >
                Mora: {{ formatMoraDays(credit.dias_en_mora) }}
              </span>
            </div>
            <div class="detail-item">
              <i class="fas fa-user-shield"></i>
              <span>Aprobado por: {{ credit.admin_approver_email }}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-handshake"></i>
              <span>Vendido por: {{ credit.seller_email }}</span>
            </div>
          </div>
          
          <div class="credit-actions">
            <button 
              @click="openPaymentModal(credit)" 
              class="action-btn pay-btn" 
              title="Registrar Pago de Crédito"
            >
              <i class="fas fa-money-check-alt"></i>
              Pagar
            </button>
            <button 
              @click="viewSaleDetails(credit.sale_id)" 
              class="action-btn detail-btn" 
              title="Ver Detalles de la Venta"
            >
              <i class="fas fa-eye"></i>
            </button>
          </div>
        </li>
      </ul>
      </div>

    <transition name="fade">
      <div v-if="showPaymentModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>Registrar Pago</h3>
            <button class="close-btn" @click="showPaymentModal = false">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-content">
            <p>Registrando pago para el cliente **{{ selectedCredit.customer_name }}** (Saldo: ${{ selectedCredit.balance_due_usd.toFixed(2) }}).</p>
            <p>Aquí irá el formulario para ingresar pagos en USD/VES.</p>
            <button class="submit-btn" @click="handlePaymentSubmit">Simular Pago</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import apiClient from '../../axios';
// Importa cualquier librería de fecha que uses (p. ej., moment o date-fns)
// Si no tienes ninguna, usaremos las funciones nativas de JS Date.

export default {
  name: 'AdminCreditMonitoring',
  data() {
    return {
      pendingCredits: [],
      loading: false,
      error: null,
      showPaymentModal: false,
      selectedCredit: null,
    };
  },
  computed: {
    totalPendingBalance() {
      return this.pendingCredits.reduce((sum, credit) => sum + credit.balance_due_usd, 0);
    },
  },
  methods: {
    // 1. Fetch de datos
    goBack() {
      this.$router.go(-1);
    },

    async fetchCredits() {
      this.loading = true;
      this.error = null;
      try {
        // Llama al nuevo endpoint creado en sale_routes.py
        const response = await apiClient.get('/api/sales/credits/pending');
        this.pendingCredits = response.data;
      } catch (err) {
        this.error = err.response?.data?.msg || 'No se pudo conectar al servidor para obtener créditos.';
        console.error("Error fetching pending credits:", err);
      } finally {
        this.loading = false;
      }
    },

    // 2. Funciones de UI/UX
    formatDate(dateStr) {
      if (!dateStr) return 'N/A';
      return new Date(dateStr).toLocaleDateString();
    },
    
    formatMoraDays(days) {
      if (days > 0) {
        return `${days} DÍAS EN MORA`;
      }
      if (days === 0) {
        return 'Vence Hoy';
      }
      return 'Al día';
    },

    // 3. Clases dinámicas para resaltar el estado de mora
    getMoraClass(days) {
      if (days > 30) return 'mora-high'; // Más de un mes
      if (days > 7) return 'mora-medium'; // Más de una semana
      if (days > 0) return 'mora-low'; // En mora (1-7 días)
      return 'mora-ok'; // Al día o vence hoy
    },
    
    getMoraTextColor(days) {
        if (days > 0) return 'text-danger';
        if (days === 0) return 'text-warning';
        return 'text-success';
    },

    // 4. Acciones
    openPaymentModal(credit) {
      this.selectedCredit = credit;
      this.showPaymentModal = true;
    },
    
    handlePaymentSubmit() {
      alert(`Simulación: Se enviaría el pago para la venta ${this.selectedCredit.sale_id.substring(0, 8)}`);
      // Lógica real: Aquí llamarías al endpoint de registro de pago de la venta
      this.showPaymentModal = false;
      this.fetchCredits(); // Recargar la lista después de un pago
    },
    
    viewSaleDetails(saleId) {
        // Lógica de navegación. Asumiendo que tienes una ruta para ver detalles de la venta
        alert(`Navegar a /admin/sales/${saleId} para ver los detalles completos.`);
        // Ejemplo real con Vue Router: this.$router.push({ name: 'SaleDetail', params: { id: saleId } });
    }
  },
  mounted() {
    this.fetchCredits();
  },
};
</script>

<style scoped>
/* Estilos Globales del Contenedor */
.credit-monitoring-container {
  padding: 30px;
  background-color: #f7f9fc;
  min-height: 100vh;
}

.page-title {
  color: #3f51b5;
  margin-bottom: 5px;
  font-size: 28px;
}

.page-subtitle {
  color: #607d8b;
  font-size: 16px;
  margin-bottom: 20px;
}

.total-pending-amount {
  font-weight: bold;
  color: #d32f2f; /* Rojo para alertar sobre la deuda total */
  font-size: 18px;
}

/* Card */
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  margin-bottom: 25px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eceff1;
}

.card-title h3 {
  margin: 0;
  color: #455a64;
  font-size: 20px;
}

.refresh-btn {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #388e3c;
  transform: translateY(-1px);
}

.refresh-btn i {
  margin-right: 5px;
}

/* Listado de Créditos */
.credit-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.credit-item {
  display: grid;
  grid-template-columns: 2fr 3fr 1fr; /* Info principal | Detalles | Acciones */
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.3s, border-left 0.3s;
}

.credit-item:hover {
  background-color: #f5f5f5;
}

/* Indicadores de Mora */
.credit-item.mora-ok {
  border-left: 6px solid #4caf50; /* Verde: Al día */
}
.credit-item.mora-low {
  border-left: 6px solid #ff9800; /* Naranja: Poca mora */
}
.credit-item.mora-medium {
  border-left: 6px solid #ff5722; /* Rojo: Mora media */
}
.credit-item.mora-high {
  border-left: 6px solid #d32f2f; /* Rojo Oscuro: Mora alta */
  animation: pulse-danger 1s infinite alternate;
}

/* Estilos de la Información */
.credit-info-main {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.customer-info i {
    color: #3f51b5;
    margin-right: 5px;
}

.customer-name {
  color: #333;
  font-size: 16px;
  display: block;
}

.sale-id {
  font-size: 12px;
  color: #777;
}

.balance-info {
  margin-top: 8px;
}

.balance-label {
  font-size: 12px;
  color: #777;
  display: block;
}

.balance-amount {
  font-size: 20px;
  font-weight: bold;
  color: #d32f2f;
}

.credit-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  font-size: 14px;
  color: #555;
}

.detail-item i {
  margin-right: 5px;
  color: #9e9e9e;
}

/* Clases de Color para Mora */
.text-danger { color: #d32f2f; font-weight: bold; }
.text-warning { color: #ff9800; font-weight: bold; }
.text-success { color: #4caf50; }

/* Acciones */
.credit-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.action-btn {
  background: none;
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.pay-btn {
  color: #2e7d32;
  border-color: #a5d6a7;
}

.pay-btn:hover {
  background-color: #e8f5e9;
}

.detail-btn {
  color: #3f51b5;
  border-color: #c5cae9;
}

.detail-btn:hover {
  background-color: #e8eaf6;
}

/* Estados Vacío/Error/Cargando */
.loading-state, .error-state, .empty-state {
    text-align: center;
    padding: 40px;
    font-size: 18px;
    color: #9e9e9e;
}
.loading-state i { color: #3f51b5; }
.error-state i { color: #d32f2f; }
.empty-state i { color: #4caf50; }

/* Animación de Peligro */
@keyframes pulse-danger {
  0% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.4); }
  100% { box-shadow: 0 0 0 8px rgba(211, 47, 47, 0); }
}

/* Responsive */
@media (max-width: 900px) {
  .credit-item {
    grid-template-columns: 1fr; 
    gap: 15px;
    padding: 15px;
    border-left-width: 4px;
  }
  
  .credit-details {
    grid-template-columns: 1fr;
  }

  .credit-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 600px) {
    .page-title {
        font-size: 24px;
    }
    .total-pending-amount {
        display: block;
        margin-top: 5px;
    }
    .card-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
    .credit-actions {
        flex-wrap: wrap;
    }
}

/* Estilos de Modal (reutilizados del componente anterior si existen) */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: white;
  border-radius: 10px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 450px;
}

.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-content {
  padding: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.submit-btn {
    padding: 10px 20px;
    background-color: #3f51b5;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 15px;
}
</style>
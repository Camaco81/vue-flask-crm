<template>
  <div class="credit-monitoring-container">
    <!-- Header con botón Volver mejorado -->
    <div class="header-controls">
      <button @click="goBack" class="back-btn" title="Regresar">
        <i class="fas fa-arrow-left"></i>
      </button>
      <div class="header-text">
        <h1 class="page-title">
          <i class="fas fa-hand-holding-usd"></i>
          Monitoreo de Créditos Pendientes
        </h1>
        <p class="page-subtitle">
          Control de cuentas por cobrar. Deuda global:
          <span class="total-pending-amount">${{ formatNumber(totalPendingBalance) }}</span>
        </p>
      </div>
    </div>

    <div class="card credit-list-card">
      <div class="card-header">
        <div class="card-title">
          <h3><i class="fas fa-list"></i> Deudas Activas ({{ pendingCredits.length }})</h3>
        </div>
        <div class="card-actions">
          <button @click="fetchCredits" class="refresh-btn" :disabled="loading">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            <span>{{ loading ? 'Sincronizando...' : 'Actualizar' }}</span>
          </button>
        </div>
      </div>

      <!-- Estados de Carga/Error/Vacío -->
      <div v-if="loading" class="state-container loading-state">
        <div class="spinner"></div>
        <p>Consultando cartera de créditos...</p>
      </div>
      
      <div v-else-if="error" class="state-container error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <p>{{ error }}</p>
      </div>

      <div v-else-if="pendingCredits.length === 0" class="state-container empty-state">
        <i class="fas fa-check-circle"></i>
        <p>¡Felicidades! No hay créditos pendientes por cobrar.</p>
      </div>

      <!-- Listado de Créditos -->
      <ul v-else class="credit-list">
        <li v-for="credit in pendingCredits" :key="credit.sale_id" :class="['credit-item', getMoraClass(credit.dias_en_mora)]">
          
          <!-- Información Principal Cliente -->
          <div class="credit-info-main">
            <div class="customer-info">
              <div class="avatar-sm">
                <i class="fas fa-user"></i>
              </div>
              <div class="customer-text">
                <strong class="customer-name">{{ credit.customer_name }}</strong>
                <span class="customer-doc">C.I: {{ credit.customer_cedula || 'N/A' }}</span>
                <span class="sale-id">ID Venta: #{{ credit.sale_id.substring(0, 8) }}</span>
              </div>
            </div>
          </div>

          <!-- Detalles de Mora y Fechas -->
          <div class="credit-details">
            <div class="detail-row">
              <div class="detail-item">
                <i class="fas fa-calendar-alt"></i>
                <span>Vence: <strong>{{ formatDate(credit.fecha_vencimiento) }}</strong></span>
              </div>
              <div class="detail-item">
                <i class="fas fa-clock"></i>
                <span :class="getMoraTextColor(credit.dias_en_mora)">
                  {{ formatMoraDays(credit.dias_en_mora) }}
                </span>
              </div>
            </div>
            <div class="detail-row trace-info">
              <div class="detail-item" :title="'Vendedor: ' + credit.seller_email">
                <i class="fas fa-user-tie"></i>
                <span>Venta: {{ credit.seller_name || credit.seller_email.split('@')[0] }}</span>
              </div>
              <div class="detail-item" :title="'Aprobador: ' + credit.admin_approver_email">
                <i class="fas fa-user-shield"></i>
                <span>Autorizó: {{ credit.admin_approver_email.split('@')[0] }}</span>
              </div>
            </div>
          </div>

          <!-- Saldo y Botón de Acción -->
          <div class="credit-actions-container">
            <div class="balance-block">
              <span class="balance-label">SALDO PENDIENTE</span>
              <span class="balance-amount">${{ formatNumber(credit.balance_due_usd) }}</span>
            </div>
            <button @click="openPaymentModal(credit)" class="pay-action-btn">
              <i class="fas fa-dollar-sign"></i>
              <span>Pagar</span>
            </button>
          </div>

        </li>
      </ul>
    </div>

    <!-- Modal de Pago (Con transiciones) -->
    <transition name="fade">
      <div v-if="showPaymentModal && selectedCredit" class="modal-overlay" @click.self="showPaymentModal = false">
        <div class="modal-container">
          <div class="modal-header">
            <h3>Registrar Pago de Crédito</h3>
            <button @click="showPaymentModal = false" class="close-modal-btn">&times;</button>
          </div>
          <CreditPayment 
            :sale-id="selectedCredit.sale_id" 
            @payment-completed="handlePaymentCompleted" 
            @close-modal="showPaymentModal = false"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import apiClient from '../../axios';
import CreditPayment from '../vendedor/CreditPayment.vue';

export default {
  name: 'AdminCreditMonitoring',
  components: { CreditPayment },
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
      return this.pendingCredits.reduce((sum, credit) => sum + (parseFloat(credit.balance_due_usd) || 0), 0);
    },
  },
  methods: {
    goBack() {
      this.$router.go(-1);
    },
    async fetchCredits() {
      this.loading = true;
      this.error = null;
      try {
        const response = await apiClient.get('/api/sales/credits/pending');
        this.pendingCredits = response.data;
      } catch (err) {
        this.error = err.response?.data?.msg || 'Error al conectar con la base de datos de créditos.';
      } finally {
        this.loading = false;
      }
    },
    formatNumber(val) {
      return parseFloat(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    formatDate(dateStr) {
      if (!dateStr) return 'N/A';
      return new Date(dateStr).toLocaleDateString('es-VE', { 
        year: 'numeric', month: 'short', day: '2-digit' 
      });
    },
    formatMoraDays(days) {
      if (days > 0) return `${days} DÍAS EN MORA`;
      if (days === 0) return 'VENCE HOY';
      return 'AL DÍA';
    },
    getMoraClass(days) {
      if (days > 30) return 'mora-high';
      if (days > 7) return 'mora-medium';
      if (days > 0) return 'mora-low';
      return 'mora-ok';
    },
    getMoraTextColor(days) {
      if (days > 0) return 'text-danger';
      if (days === 0) return 'text-warning';
      return 'text-success';
    },
    openPaymentModal(credit) {
      this.selectedCredit = credit;
      this.showPaymentModal = true;
    },
    handlePaymentCompleted() {
      this.showPaymentModal = false;
      this.selectedCredit = null;
      this.fetchCredits();
      // Usar un Toast o componente de mensaje en lugar de alert si es posible
    }
  },
  mounted() {
    this.fetchCredits();
  },
};
</script>

<style scoped>
.credit-monitoring-container { padding: 25px; background-color: #f0f2f5; min-height: 100vh; font-family: 'Segoe UI', sans-serif; }

/* Header */
.header-controls { display: flex; align-items: flex-start; gap: 20px; margin-bottom: 30px; }
.back-btn { width: 42px; height: 42px; border-radius: 12px; background: white; border: none; box-shadow: 0 2px 8px rgba(0,0,0,0.1); cursor: pointer; transition: 0.3s; color: #444; }
.back-btn:hover { background: #3f51b5; color: white; transform: translateX(-4px); }
.page-title { margin: 0; color: #1a237e; font-size: 1.8rem; display: flex; align-items: center; gap: 10px; }
.page-subtitle { margin: 5px 0 0; color: #546e7a; }
.total-pending-amount { font-weight: 800; color: #c62828; font-size: 1.2rem; background: #ffebee; padding: 2px 8px; border-radius: 6px; }

/* Cards */
.card { background: white; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); overflow: hidden; }
.card-header { padding: 20px 25px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; background: #fafafa; }
.card-title h3 { margin: 0; color: #2c3e50; font-size: 1.1rem; }

.refresh-btn { display: flex; align-items: center; gap: 8px; background: #388e3c; color: white; border: none; padding: 10px 18px; border-radius: 10px; cursor: pointer; font-weight: 600; transition: 0.3s; }
.refresh-btn:hover:not(:disabled) { background: #2e7d32; box-shadow: 0 4px 12px rgba(56,142,60,0.3); }

/* Listado */
.credit-list { list-style: none; padding: 0; margin: 0; }
.credit-item { display: grid; grid-template-columns: 1.2fr 1.5fr 1fr; align-items: center; padding: 20px 25px; border-bottom: 1px solid #f1f1f1; transition: 0.2s; position: relative; }
.credit-item:hover { background-color: #fcfcfc; }

/* Clases de Mora */
.credit-item.mora-ok { border-left: 5px solid #4caf50; }
.credit-item.mora-low { border-left: 5px solid #ff9800; }
.credit-item.mora-medium { border-left: 5px solid #ff5722; }
.credit-item.mora-high { border-left: 5px solid #d32f2f; background: #fff5f5; }

/* Info Cliente */
.customer-info { display: flex; align-items: center; gap: 15px; }
.avatar-sm { width: 45px; height: 45px; background: #e8eaf6; color: #3f51b5; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.customer-text { display: flex; flex-direction: column; }
.customer-name { font-size: 1.05rem; color: #1a1a1a; font-weight: 700; }
.customer-doc { font-size: 0.85rem; color: #666; }
.sale-id { font-size: 0.75rem; color: #999; font-family: monospace; }

/* Detalles */
.credit-details { display: flex; flex-direction: column; gap: 8px; }
.detail-row { display: flex; gap: 20px; }
.detail-item { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; color: #444; }
.detail-item i { color: #94a3b8; width: 16px; }
.trace-info { border-top: 1px dashed #eee; padding-top: 5px; margin-top: 2px; }

/* Acciones y Saldo */
.credit-actions-container { display: flex; justify-content: flex-end; align-items: center; gap: 25px; }
.balance-block { text-align: right; }
.balance-label { display: block; font-size: 0.7rem; font-weight: 800; color: #999; letter-spacing: 0.5px; }
.balance-amount { font-size: 1.5rem; font-weight: 900; color: #d32f2f; }

.pay-action-btn { background: #3f51b5; color: white; border: none; padding: 12px 20px; border-radius: 12px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: 0.3s; }
.pay-action-btn:hover { background: #303f9f; box-shadow: 0 5px 15px rgba(63,81,181,0.4); transform: translateY(-2px); }

/* Estados */
.state-container { padding: 60px; text-align: center; color: #94a3b8; }
.state-container i { font-size: 3rem; margin-bottom: 15px; display: block; }
.loading-state .spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #3f51b5; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.modal-container { background: white; border-radius: 20px; width: 90%; max-width: 550px; box-shadow: 0 20px 50px rgba(0,0,0,0.3); }
.modal-header { padding: 20px 25px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; color: #1a237e; }
.close-modal-btn { background: none; border: none; font-size: 2rem; cursor: pointer; color: #999; }

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.text-danger { color: #d32f2f; font-weight: 800; }
.text-warning { color: #f57c00; font-weight: 800; }
.text-success { color: #388e3c; font-weight: 800; }

/* Responsive */
@media (max-width: 1100px) {
  .credit-item { grid-template-columns: 1.5fr 1fr; gap: 20px; }
  .credit-actions-container { grid-column: span 2; justify-content: space-between; border-top: 1px solid #eee; padding-top: 15px; }
}
@media (max-width: 600px) {
  .credit-item { grid-template-columns: 1fr; }
  .credit-actions-container { grid-column: span 1; }
  .detail-row { flex-direction: column; gap: 5px; }
}
</style>
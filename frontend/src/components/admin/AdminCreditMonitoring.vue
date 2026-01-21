<template>
  <div class="credit-monitoring-container">
    <!-- Header -->
    <div class="header-controls">
          <button class="back-btn" @click="$router.push('/dashboard')" title="Volver al Dashboard">
        <i class="fas fa-arrow-left">⬅️</i>
      </button>
      <div class="header-text">
        <h1 class="page-title">
          <i class="fas fa-shield-alt"></i>
          Panel de Control de Cartera
        </h1>
        <p class="page-subtitle">
          Deuda global en sistema:
          <span class="total-pending-amount">${{ formatNumber(totalPendingBalance) }}</span>
        </p>
      </div>
    </div>

    <div class="card credit-list-card">
      <div class="card-header">
        <div class="card-title">
          <h3><i class="fas fa-list"></i> Créditos Activos ({{ pendingCredits.length }})</h3>
        </div>
        <div class="card-actions">
          <div class="search-box">
            <i class="fas fa-search"></i>
            <input v-model="filterText" placeholder="Nombre, Cédula o Factura..." />
          </div>
          <button @click="fetchCredits" class="refresh-btn" :disabled="loading">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            <span>{{ loading ? 'Sincronizando...' : 'Actualizar' }}</span>
          </button>
        </div>
      </div>

      <!-- Estados -->
      <div v-if="loading" class="state-container loading-state">
        <div class="spinner"></div>
        <p>Cargando registros contables...</p>
      </div>
      
      <div v-else-if="error" class="state-container error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <p>{{ error }}</p>
      </div>

      <!-- Listado con Fix de Búsqueda -->
      <ul v-else class="credit-list">
        <li v-for="credit in filteredCredits" :key="credit.sale_id" :class="['credit-item', getMoraClass(credit.dias_en_mora)]">
          <div class="credit-info-main">
            <div class="customer-info">
              <div class="avatar-sm">
                <i class="fas fa-user-shield"></i>
              </div>
              <div class="customer-text">
                <strong class="customer-name">{{ credit.customer_name }}</strong>
                <!-- Fix: Asegurar que cedula sea visible -->
                <span class="customer-doc">C.I: {{ credit.cedula || 'Sin Cédula' }}</span>
                <span class="sale-id">FACT: #{{ String(credit.sale_id).substring(0, 8).toUpperCase() }}</span>
              </div>
            </div>
          </div>

          <div class="credit-details">
            <div class="detail-row">
              <div class="detail-item">
                <i class="fas fa-calendar-check"></i>
                <span>Vence: <strong>{{ formatDate(credit.fecha_vencimiento) }}</strong></span>
              </div>
              <div class="detail-item">
                <i class="fas fa-hourglass-half"></i>
                <span :class="getMoraTextColor(credit.dias_en_mora)">
                  {{ formatMoraDays(credit.dias_en_mora) }}
                </span>
              </div>
            </div>
          </div>

          <div class="credit-actions-container">
            <div class="balance-block">
              <span class="balance-label">SALDO PENDIENTE</span>
              <span class="balance-amount">${{ formatNumber(credit.balance_due_usd) }}</span>
            </div>
            <button @click="openPaymentModal(credit)" class="pay-action-btn">
              <i class="fas fa-cash-register"></i>
              <span>Gestionar</span>
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Modal de Procesamiento de Pago -->
    <transition name="fade">
      <div v-if="showPaymentModal && selectedCredit" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content animate-pop">
          <div class="modal-header">
            <div class="header-title">
              <div class="icon-circle admin">
                <i class="fas fa-file-invoice-dollar"></i>
              </div>
              <div>
                <h3>Registrar Abono / Liquidación</h3>
                <p>{{ selectedCredit.customer_name }} • C.I: {{ selectedCredit.cedula }}</p>
              </div>
            </div>
            <button @click="closeModal" class="close-btn">&times;</button>
          </div>

          <div class="modal-body">
            <div class="debt-banner admin-theme">
              <div class="banner-item">
                <span class="label">DEUDA TOTAL</span>
                <span class="amount">${{ formatNumber(selectedCredit.balance_due_usd) }}</span>
              </div>
              <div class="banner-divider"></div>
              <div class="banner-item">
                <span class="label">TASA BCV</span>
                <span class="amount">Bs. {{ formatNumber(bcvRate) }}</span>
              </div>
            </div>

            <div class="payment-form-grid">
              <div class="form-section">
                <div class="input-group">
                  <label><i class="fas fa-coins"></i> Moneda de Pago</label>
                  <select v-model="form.currency" @change="handleCurrencyChange">
                    <option value="USD">Dólares ($)</option>
                    <option value="VES">Bolívares (Bs)</option>
                  </select>
                </div>

                <div class="input-group">
                  <label>Monto en {{ form.currency }}</label>
                  <input type="number" v-model.number="form.amount" step="0.01" @input="validateAmount">
                </div>
              </div>

              <div v-if="form.currency === 'VES'" class="exchange-container animate-fade-in">
                <div class="input-group">
                  <label>Tasa de Cambio</label>
                  <input type="number" v-model.number="form.rate" step="0.01" @input="validateAmount">
                </div>
                <div class="conversion-info">
                  <span>Equivalente: <strong>${{ equivalentUSD }} USD</strong></span>
                </div>
              </div>
            </div>

            <div v-if="formError" class="error-msg">
              <i class="fas fa-info-circle"></i> {{ formError }}
            </div>

            <div class="payment-summary">
              <div class="summary-item">
                <span>Saldo Final:</span>
                <strong :class="{'text-success': newBalance <= 0.02}">
                  ${{ formatNumber(newBalance) }} USD
                </strong>
              </div>
              <button class="btn-confirm-payment" :disabled="!isFormValid || processing" @click="processPayment">
                <i v-if="processing" class="fas fa-circle-notch fa-spin"></i>
                <span v-else>{{ newBalance <= 0.02 ? 'LIQUIDAR CRÉDITO' : 'PROCESAR PAGO' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import apiClient from '../../axios';

export default {
  name: 'CreditPaymentAdmin',
  data() {
    return {
      pendingCredits: [],
      filterText: '',
      loading: false,
      processing: false,
      error: null,
      showPaymentModal: false,
      selectedCredit: null,
      formError: '',
      bcvRate: 1,
      form: { amount: 0, currency: 'USD', rate: 1 }
    };
  },
  computed: {
    filteredCredits() {
      const search = this.filterText.toLowerCase().trim();
      if (!search) return this.pendingCredits;
      return this.pendingCredits.filter(c => {
        // Fix: Convertir a String para evitar errores de .includes()
        const name = String(c.customer_name || '').toLowerCase();
        const saleId = String(c.sale_id || '').toLowerCase();
        const cedula = String(c.cedula || '').toLowerCase();
        return name.includes(search) || saleId.includes(search) || cedula.includes(search);
      });
    },
    totalPendingBalance() {
      return this.pendingCredits.reduce((s, c) => s + parseFloat(c.balance_due_usd || 0), 0);
    },
    equivalentUSD() {
      if (this.form.currency === 'USD') return parseFloat(this.form.amount || 0);
      return parseFloat((this.form.amount / (this.form.rate || 1)).toFixed(2));
    },
    newBalance() {
      if (!this.selectedCredit) return 0;
      const res = parseFloat(this.selectedCredit.balance_due_usd) - this.equivalentUSD;
      return res > 0 ? res : 0;
    },
    isFormValid() {
      return this.form.amount > 0 && this.form.rate > 0 && !this.formError;
    }
  },
  methods: {
    goBack() { this.$router.go(-1); },
    
    async fetchBcvRate() {
      try {
        const res = await apiClient.get('/api/exchange-rate');
        this.bcvRate = parseFloat(res.data.rate || res.data.usd || 1);
      } catch (err) { this.bcvRate = 36.5; }
    },

    async fetchCredits() {
      this.loading = true;
      try {
        await this.fetchBcvRate();
        const res = await apiClient.get('/api/sales/credits/pending');
        this.pendingCredits = res.data;
      } catch (err) {
        this.error = "No se pudieron cargar los créditos.";
      } finally { this.loading = false; }
    },

    openPaymentModal(credit) {
      this.selectedCredit = credit;
      this.form = {
        amount: parseFloat(credit.balance_due_usd),
        currency: 'USD',
        rate: this.bcvRate
      };
      this.formError = '';
      this.showPaymentModal = true;
    },

    handleCurrencyChange() {
      if (this.form.currency === 'VES') {
        this.form.amount = parseFloat((this.selectedCredit.balance_due_usd * this.bcvRate).toFixed(2));
        this.form.rate = this.bcvRate;
      } else {
        this.form.amount = parseFloat(this.selectedCredit.balance_due_usd);
        this.form.rate = 1;
      }
    },

    validateAmount() {
      const limit = parseFloat(this.selectedCredit.balance_due_usd);
      if (this.equivalentUSD > (limit + 0.05)) {
        this.formError = `El monto excede la deuda ($${limit})`;
      } else {
        this.formError = '';
      }
    },

    async processPayment() {
      if (!this.isFormValid) return;
      this.processing = true;
      this.formError = '';
      
      try {
        // DATA FIX: Intentamos capturar el ID de varias formas comunes en tu API
        const cId = this.selectedCredit.customer_id || 
                    this.selectedCredit.id_cliente || 
                    this.selectedCredit.cliente_id;

        if (!cId) {
          throw new Error("El cliente no tiene un ID válido asociado.");
        }

        const payload = {
          sale_id: this.selectedCredit.sale_id,
          customer_id: cId, 
          payment_amount: parseFloat(this.form.amount),
          payment_currency: this.form.currency,
          exchange_rate: parseFloat(this.form.rate),
          cancellation_code: 'ADMIN_DIRECT',
          admin_auth_code: 'BYPASSED'
        };

        await apiClient.post('/api/sales/pay-credit', payload);
        this.closeModal();
        await this.fetchCredits();
      } catch (err) {
        this.formError = err.response?.data?.msg || err.message || "Error en la transacción.";
      } finally { this.processing = false; }
    },

    closeModal() { this.showPaymentModal = false; this.selectedCredit = null; },
    formatNumber(v) { return parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('es-VE') : 'N/A'; },
    formatMoraDays(days) {
      const d = parseInt(days);
      return d > 0 ? `${d} DÍAS VENCIDO` : d === 0 ? 'VENCE HOY' : 'AL DÍA';
    },
    getMoraClass(days) {
      const d = parseInt(days);
      return d > 15 ? 'mora-high' : d > 0 ? 'mora-medium' : 'mora-ok';
    },
    getMoraTextColor(days) { return parseInt(days) > 0 ? 'text-danger' : 'text-success'; }
  },
  mounted() { this.fetchCredits(); }
};
</script>
<style scoped>
/* Estilos mantenidos y optimizados */
.back-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
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
.refresh-btn{
  margin-top: 5px;
  padding: 5px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  background: #023d7c;
  color: white;
}
.refresh-btn:hover{
  background: #007bff;
  transform: translateX(-3px);
}
.back-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
  transform: translateX(-3px);
}
.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateX(-3px);
}
.credit-monitoring-container { padding: 30px; background: #f0f2f5; min-height: 100vh; }
.header-controls { display: flex; align-items: center; gap: 20px; margin-bottom: 25px; }
.page-title { margin: 0; font-size: 1.8rem; color: #0f172a; display: flex; align-items: center; gap: 12px; }
.total-pending-amount { color: #e11d48; background: #fff1f2; padding: 4px 12px; border-radius: 99px; font-weight: 800; border: 1px solid #fecdd3; }

.card { background: white; border-radius: 20px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }
.card-header { padding: 20px 25px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }

.search-box { position: relative; display: flex; align-items: center; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 0 15px; width: 350px; }
.search-box i { color: #94a3b8; }
.search-box input { border: none; background: transparent; padding: 10px; font-size: 0.9rem; width: 100%; outline: none; }

.credit-list { list-style: none; padding: 0; margin: 0; }
.credit-item { display: grid; grid-template-columns: 1fr 1.2fr 1fr; padding: 20px 25px; border-bottom: 1px solid #f1f5f9; align-items: center; }
.credit-item.mora-high { background: #fffafa; border-left: 6px solid #ef4444; }
.credit-item.mora-medium { border-left: 6px solid #f59e0b; }
.credit-item.mora-ok { border-left: 6px solid #10b981; }

.customer-name { font-size: 1.1rem; color: #1e293b; display: block; }
.customer-doc { font-size: 0.85rem; color: #64748b; font-weight: 600; }
.sale-id { font-size: 0.75rem; color: #94a3b8; font-family: monospace; font-weight: bold; }

.balance-amount { font-size: 1.5rem; font-weight: 800; color: #1e293b; display: block; }
.pay-action-btn { background: #0f172a; color: white; border: none; padding: 12px 20px; border-radius: 12px; font-weight: 600; cursor: pointer; transition: 0.3s; }
.pay-action-btn:hover { background: #334155; transform: scale(1.02); }

.modal-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(4px); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal-content { background: white; width: 95%; max-width: 500px; border-radius: 24px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
.modal-header { background: #f8fafc; padding: 20px 25px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }

.debt-banner.admin-theme { background: #1e293b; color: white; margin: 20px; padding: 15px; border-radius: 16px; display: flex; justify-content: space-around; align-items: center; }
.mora-badge { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; }
.mora-badge.mora-high { background: #ef4444; color: white; }
.mora-badge.mora-medium { background: #f59e0b; color: white; }
.mora-badge.mora-ok { background: #10b981; color: white; }

.payment-form-grid { padding: 0 20px; display: flex; flex-direction: column; gap: 15px; }
.input-group label { display: block; font-size: 0.8rem; font-weight: 600; color: #64748b; margin-bottom: 5px; }
.input-group input, .input-group select { width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 10px; font-size: 1rem; }

.exchange-container { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 12px; }
.payment-summary { padding: 25px; background: #f8fafc; border-top: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 15px; }
.btn-confirm-payment { background: #10b981; color: white; border: none; padding: 15px; border-radius: 12px; font-weight: 700; cursor: pointer; }
.btn-confirm-payment:disabled { background: #cbd5e1; cursor: not-allowed; }

.text-danger { color: #ef4444; }
.text-success { color: #10b981; }
.error-msg { margin: 10px 20px; padding: 10px; background: #fef2f2; color: #dc2626; border-radius: 8px; font-size: 0.85rem; }

@media (max-width: 768px) {
  .credit-item { grid-template-columns: 1fr; gap: 15px; }
  .search-box { width: 100%; }
}
</style>
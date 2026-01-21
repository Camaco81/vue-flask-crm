<template>
  <div class="credit-payment-wrapper">
    <div v-if="selectedCustomer" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content animate-pop">
        
        <div class="modal-header">
          <div class="header-title">
            <div class="icon-circle">
              <i class="fas fa-file-invoice-dollar"></i>
            </div>
            <div>
              <h3>Gestión de Crédito (Vendedor)</h3>
              <p>{{ selectedCustomer.name }} • C.I: {{ selectedCustomer.cedula }}</p>
            </div>
          </div>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="debt-banner">
            <div class="banner-item">
              <span class="label">SALDO TOTAL</span>
              <span class="amount">${{ formatNumber(selectedCustomer.balance_total) }}</span>
            </div>
            <div class="banner-divider"></div>
            <div class="banner-item">
              <span class="label">TASA ACTUAL (BCV)</span>
              <span class="amount">Bs. {{ formatNumber(currentTasa) }}</span>
            </div>
          </div>

          <div v-for="sale in customerSales" :key="sale.id" class="payment-card">
            <div class="card-header">
              <span class="factura-id">FACTURA #{{ String(sale.id).substring(0, 8).toUpperCase() }}</span>
              <span class="date">{{ formatDate(sale.sale_date) }}</span>
            </div>

            <div class="card-body">
              <div class="info-grid">
                <div class="info-item">
                  <label>Total Venta</label>
                  <span>${{ formatNumber(sale.total_amount_usd) }}</span>
                </div>
                <div class="info-item">
                  <label>Saldo Pendiente</label>
                  <span class="highlight-red">${{ formatNumber(sale.balance_due_usd) }}</span>
                </div>
                <div class="info-item">
                  <label>Vencimiento</label>
                  <span :class="{ 'text-danger': isExpired(sale.fecha_vencimiento) }">
                    {{ formatDate(sale.fecha_vencimiento) }}
                  </span>
                </div>
              </div>

              <div class="payment-form">
                <div class="input-row">
                  <div class="input-group">
                    <label>Moneda de Pago</label>
                    <select v-model="paymentCurrencies[sale.id]" @change="handleCurrencyChange(sale)">
                      <option value="USD">Dólares ($)</option>
                      <option value="VES">Bolívares (Bs)</option>
                    </select>
                  </div>
                  <div class="input-group">
                    <label>Monto en {{ paymentCurrencies[sale.id] }}</label>
                    <input 
                      type="number" 
                      v-model.number="paymentAmounts[sale.id]" 
                      step="0.01"
                      @input="validatePaymentAmount(sale)"
                    >
                  </div>
                </div>

                <div v-if="paymentCurrencies[sale.id] === 'VES'" class="exchange-box animate-fade-in">
                  <div class="input-group">
                    <label>Tasa Aplicada</label>
                    <input type="number" v-model.number="exchangeRates[sale.id]" step="0.01" @input="validatePaymentAmount(sale)">
                  </div>
                  <div class="conversion-preview">
                    <i class="fas fa-exchange-alt"></i>
                    <span>Equivale a: <strong>${{ calculateEquivalentUSD(sale) }} USD</strong></span>
                  </div>
                </div>

                <div class="input-row codes">
                  <div class="input-group">
                    <label>Cód. Cliente (Cédula/Referencia)</label>
                    <input type="text" v-model="cancellationCodes[sale.id]" placeholder="Código para recibo">
                  </div>
                  <div v-if="userRole !== 'admin'" class="input-group">
                    <label>Cód. Autorización Gerencial</label>
                    <input type="password" v-model="admin_auth_code[sale.id]" placeholder="****">
                  </div>
                </div>

                <div class="payment-footer">
                  <div class="new-balance">
                    Nuevo Saldo: <strong>${{ formatNumber(calculateNewBalance(sale)) }} USD</strong>
                  </div>
                  <button 
                    @click="preparePayment(sale)"
                    :disabled="!isValidPayment(sale) || paymentProcessing"
                    class="btn-submit"
                    :class="{ 'btn-complete': calculateNewBalance(sale) < 0.02 }"
                  >
                    <i v-if="paymentProcessing" class="fas fa-spinner fa-spin"></i>
                    <span v-else>
                      {{ calculateNewBalance(sale) < 0.02 ? 'LIQUIDAR DEUDA' : 'REGISTRAR ABONO' }}
                    </span>
                  </button>
                  <p v-if="paymentErrors[sale.id]" class="error-text">{{ paymentErrors[sale.id] }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showConfirmation" class="modal-overlay z-top">
      <div class="confirmation-card animate-pop">
        <i class="fas fa-exclamation-circle warn-icon"></i>
        <h3>¿Confirmar transacción?</h3>
        <p>{{ confirmationMessage }}</p>
        <div class="confirm-btns">
          <button @click="confirmPayment" class="btn-confirm" :disabled="paymentProcessing">
            {{ paymentProcessing ? 'Procesando...' : 'Sí, registrar pago' }}
          </button>
          <button @click="showConfirmation = false" class="btn-cancel" :disabled="paymentProcessing">Revisar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../../axios';

export default {
  name: 'CreditPayment',
  data() {
    return {
      selectedCustomer: null,
      customerSales: [],
      paymentAmounts: {},
      paymentCurrencies: {},
      cancellationCodes: {},
      admin_auth_code: {},
      exchangeRates: {},
      paymentErrors: {},
      paymentProcessing: false,
      showConfirmation: false,
      confirmationMessage: '',
      pendingPaymentSale: null,
      currentTasa: 1,
      userRole: localStorage.getItem('user_role')
    };
  },
  methods: {
    async fetchCurrentRate() {
      try {
        const res = await apiClient.get('/api/exchange-rate');
        this.currentTasa = parseFloat(res.data.rate || res.data.usd || 36.5);
      } catch (err) {
        this.currentTasa = 36.5; 
      }
    },

    async openForCustomer(saleData) {
      await this.fetchCurrentRate();
      
      // Limpiamos reactividad previa para evitar conflictos
      const sale = JSON.parse(JSON.stringify(saleData));
      
      // NORMALIZACIÓN DEL ID DEL CLIENTE (Estrategia Admin)
      const customerId = sale.customer_id || sale.id_cliente || sale.cliente_id || (sale.customer && sale.customer.id);

      if (!customerId) {
        alert("⚠️ El registro no contiene un ID de cliente válido.");
        return;
      }

      this.selectedCustomer = {
        id: customerId,
        name: sale.customer_name || 'Cliente sin nombre',
        cedula: sale.cedula || 'N/A',
        balance_total: parseFloat(sale.balance_due_usd || 0)
      };

      this.customerSales = [sale];
      this.initFormForSale(sale);
    },

    initFormForSale(sale) {
      // Usamos $set si es Vue 2, o asignación directa si es Vue 3 para asegurar reactividad
      this.$set ? this.$set(this.paymentAmounts, sale.id, parseFloat(sale.balance_due_usd).toFixed(2)) 
                : this.paymentAmounts[sale.id] = parseFloat(sale.balance_due_usd).toFixed(2);
      
      this.$set ? this.$set(this.paymentCurrencies, sale.id, 'USD') : this.paymentCurrencies[sale.id] = 'USD';
      this.$set ? this.$set(this.exchangeRates, sale.id, this.currentTasa) : this.exchangeRates[sale.id] = this.currentTasa;
      this.$set ? this.$set(this.cancellationCodes, sale.id, '') : this.cancellationCodes[sale.id] = '';
      this.$set ? this.$set(this.admin_auth_code, sale.id, '') : this.admin_auth_code[sale.id] = '';
      this.$set ? this.$set(this.paymentErrors, sale.id, '') : this.paymentErrors[sale.id] = '';
    },

    calculateEquivalentUSD(sale) {
      const amount = parseFloat(this.paymentAmounts[sale.id]) || 0;
      const rate = parseFloat(this.exchangeRates[sale.id]) || 1;
      return (amount / rate).toFixed(2);
    },

    calculateNewBalance(sale) {
      const currentBalance = parseFloat(sale.balance_due_usd);
      const paidUSD = this.paymentCurrencies[sale.id] === 'USD' 
        ? (parseFloat(this.paymentAmounts[sale.id]) || 0)
        : parseFloat(this.calculateEquivalentUSD(sale));
      const res = currentBalance - paidUSD;
      return res > 0.01 ? res : 0; // Margen de 1 centavo para liquidación
    },

    validatePaymentAmount(sale) {
      const balance = parseFloat(sale.balance_due_usd);
      const paymentUSD = this.paymentCurrencies[sale.id] === 'USD' 
        ? (parseFloat(this.paymentAmounts[sale.id]) || 0)
        : parseFloat(this.calculateEquivalentUSD(sale));
      
      if (paymentUSD > (balance + 0.05)) {
        this.paymentErrors[sale.id] = `Monto excede la deuda ($${this.formatNumber(balance)})`;
      } else {
        this.paymentErrors[sale.id] = '';
      }
    },

    isValidPayment(sale) {
      const amount = parseFloat(this.paymentAmounts[sale.id]) || 0;
      const hasClientCode = !!this.cancellationCodes[sale.id]?.trim();
      const hasAdminAuth = this.userRole === 'admin' || !!this.admin_auth_code[sale.id]?.trim();
      
      return amount > 0 && hasClientCode && hasAdminAuth && !this.paymentErrors[sale.id];
    },

    preparePayment(sale) {
      const amount = this.paymentAmounts[sale.id];
      const curr = this.paymentCurrencies[sale.id];
      this.confirmationMessage = `¿Registrar pago de ${amount} ${curr} para la factura #${String(sale.id).substring(0,8)}?`;
      this.pendingPaymentSale = sale;
      this.showConfirmation = true;
    },
    async confirmPayment() {
  this.paymentProcessing = true;
  const sale = this.pendingPaymentSale;
  
  // 1. Extraer y limpiar el código
  const codigoParaEnviar = String(this.admin_auth_code[sale.id] || '').trim();
  const montoPagado = parseFloat(this.paymentAmounts[sale.id]);

  console.log("DEBUG PAGO:", {
    rol: this.userRole,
    codigo: codigoParaEnviar,
    monto: montoPagado
  });

  try {
    const payload = {
      customer_id: this.selectedCustomer.id,
      sale_id: sale.id,
      payment_amount: montoPagado,
      payment_currency: this.paymentCurrencies[sale.id],
      exchange_rate: parseFloat(this.exchangeRates[sale.id]),
      cancellation_code: this.cancellationCodes[sale.id],
      admin_auth_code: this.userRole === 'admin' ? 'ADMIN_BYPASS' : codigoParaEnviar
    };

    console.log("Payload final a enviar:", payload);
    
    // 2. Ejecutar la petición al servidor
    const response = await apiClient.post('/api/sales/pay-credit', payload);

    // 3. EL CAMBIO CLAVE: Enviar los datos del éxito al componente padre
    // Pasamos el ID de la venta y el monto para que el padre actualice la tabla
    this.$emit('payment-success', {
      sale_id: sale.id,
      payment_amount: montoPagado,
      nuevo_saldo: response.data.nuevo_saldo // Opcional: usar el saldo exacto que devuelve el server
    });

    this.closeModal();
  } catch (e) {
    console.error("Error en pago:", e);
    alert(e.response?.data?.msg || "Error al procesar el pago");
  } finally {
    this.paymentProcessing = false;
    this.showConfirmation = false;
  }
},

    handleCurrencyChange(sale) {
      const debtUSD = parseFloat(sale.balance_due_usd);
      if (this.paymentCurrencies[sale.id] === 'VES') {
        this.paymentAmounts[sale.id] = (debtUSD * this.currentTasa).toFixed(2);
        this.exchangeRates[sale.id] = this.currentTasa;
      } else {
        this.paymentAmounts[sale.id] = debtUSD.toFixed(2);
        this.exchangeRates[sale.id] = 1;
      }
      this.validatePaymentAmount(sale);
    },

    closeModal() {
      this.selectedCustomer = null;
      this.customerSales = [];
      this.showConfirmation = false;
      this.pendingPaymentSale = null;
    },

    formatNumber(v) { 
      return parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); 
    },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('es-VE') : 'N/A'; },
    isExpired(d) { return d && new Date(d) < new Date(); }
  }
};
</script>

<style scoped>
/* Estética Moderna Estilo Ingeniería Informática */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(8px);
  display: flex; justify-content: center; align-items: center; z-index: 1000;
}

.z-top { z-index: 1100; }

.modal-content {
  background: #ffffff; width: 95%; max-width: 650px; border-radius: 20px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); overflow: hidden;
}

.animate-pop { animation: pop 0.3s ease-out; }
@keyframes pop { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }

.modal-header {
  padding: 24px; background: #f8fafc; border-bottom: 1px solid #f1f5f9;
  display: flex; justify-content: space-between; align-items: center;
}

.header-title { display: flex; align-items: center; gap: 15px; }
.icon-circle {
  width: 45px; height: 45px; background: #e0e7ff; color: #4f46e5;
  border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px;
}
.header-title h3 { margin: 0; font-size: 1.25rem; color: #1e293b; }
.header-title p { margin: 0; font-size: 0.85rem; color: #64748b; }

.close-btn { background: none; border: none; font-size: 24px; color: #94a3b8; cursor: pointer; }

.debt-banner {
  margin: 20px; background: #4f46e5; border-radius: 15px;
  display: flex; flex-direction: column; align-items: center; color: white;
}
.debt-banner .label { font-size: 0.7rem; letter-spacing: 1px; opacity: 0.9; }
.debt-banner .amount { font-size: 2rem; font-weight: 800; }

.payment-card { margin: 20px; border: 1px solid #e2e8f0; border-radius: 15px; overflow: hidden; }
.card-header { padding: 12px 20px; background: #f1f5f9; display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; color: #475569; }

.card-body { padding: 20px; }

.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 25px; }
.info-item { display: flex; flex-direction: column; }
.info-item label { font-size: 0.65rem; color: #94a3b8; font-weight: bold; margin-bottom: 4px; }
.info-item span { font-weight: 600; color: #334155; }
.highlight-red { color: #ef4444 !important; }

.payment-form { background: #f8fafc; padding: 20px; border-radius: 12px; }
.input-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }

.input-group label { display: block; font-size: 0.75rem; font-weight: 600; color: #475569; margin-bottom: 6px; }
.input-group input, .input-group select {
  width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.9rem;
  transition: border 0.2s;
}
.input-group input:focus { border-color: #4f46e5; outline: none; }

.exchange-box { 
  display: flex; align-items: center; gap: 20px; padding: 12px; 
  background: #fff; border-radius: 8px; margin-bottom: 15px; border: 1px dashed #cbd5e1;
}
.conversion-preview { font-size: 0.85rem; color: #475569; }

.payment-footer { margin-top: 20px; text-align: center; }
.new-balance { font-size: 0.9rem; margin-bottom: 15px; color: #64748b; }

.btn-submit {
  width: 100%; padding: 14px; background: #1e293b; color: white; border: none;
  border-radius: 10px; font-weight: 700; cursor: pointer; transition: 0.3s;
}
.btn-submit:hover:not(:disabled) { background: #334155; transform: translateY(-1px); }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-complete { background: #10b981; }
.btn-complete:hover { background: #059669; }

.error-text { color: #ef4444; font-size: 0.75rem; margin-top: 10px; }

/* Confirmation Card */
.confirmation-card {
  background: white; padding: 30px; border-radius: 20px; width: 350px; text-align: center;
}
.warn-icon { font-size: 3rem; color: #f59e0b; margin-bottom: 15px; }
.confirm-btns { display: flex; gap: 10px; margin-top: 25px; }
.btn-confirm { flex: 1; padding: 12px; background: #4f46e5; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
.btn-cancel { flex: 1; padding: 12px; background: #f1f5f9; color: #64748b; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
</style>
  <template>
    <div class="credit-payment-container">
      <h1 class="page-title">Gestión de Créditos y Pagos</h1>
      
      <div class="card search-card">
        <h2>Buscar Clientes con Crédito</h2>
        
        <div class="form-group">
          <label for="customer-search">Buscar por cédula o nombre:</label>
          <input
            type="text"
            id="customer-search"
            v-model="searchTerm"
            placeholder="Ingrese cédula o nombre del cliente..."
            @input="onSearchInput"
            @keyup.enter="searchCustomers"
          >
          <button @click="searchCustomers" class="search-btn" :disabled="loading">
            {{ loading ? 'Buscando...' : 'Buscar' }}
          </button>
        </div>

        <div v-if="loading" class="loading-state">Buscando clientes...</div>
        
        <div v-else-if="searchError" class="error-message">
          {{ searchError }}
        </div>
        
        <div v-else-if="customersWithCredit.length === 0 && searchPerformed" class="no-results">
          No se encontraron clientes con saldo pendiente.
        </div>

        <div v-else-if="customersWithCredit.length > 0" class="customers-list">
          <div v-for="customer in customersWithCredit" :key="customer.id" class="customer-card">
            <div class="customer-info">
              <h3>{{ customer.name }}</h3>
              <p><strong>Cédula:</strong> {{ customer.cedula }}</p>
              <p><strong>Saldo Pendiente:</strong> ${{ customer.saldo_pendiente.toFixed(2) }}</p>
              <p><strong>Ventas activas:</strong> {{ customer.ventas_credito_activas }}</p>
            </div>
            
            <button 
              @click="viewCustomerSales(customer)"
              class="view-sales-btn"
              :disabled="customer.ventas_credito_activas === 0"
            >
              {{ customer.ventas_credito_activas > 0 ? 'Ver Ventas y Pagar' : 'Sin ventas activas' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Modal para ver ventas y realizar pagos -->
      <div v-if="selectedCustomer" class="modal-overlay">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Ventas a Crédito - {{ selectedCustomer.name }}</h3>
            <button @click="closeModal" class="close-btn">&times;</button>
          </div>
          
          <div class="modal-body">
            <div class="customer-summary">
              <p><strong>Cliente:</strong> {{ selectedCustomer.name }} - {{ selectedCustomer.cedula }}</p>
              <p><strong>Saldo Total Pendiente:</strong> ${{ selectedCustomer.saldo_pendiente.toFixed(2) }}</p>
            </div>
            
            <div v-if="customerSalesLoading" class="loading-state">Cargando ventas...</div>
            
            <div v-else-if="customerSales.length === 0" class="no-results">
              No hay ventas a crédito pendientes para este cliente.
            </div>
            
            <div v-else class="sales-list">
              <div v-for="sale in customerSales" :key="sale.id" class="sale-item">
                  <div class="sale-info">
    <p><strong>Venta #{{ sale.id.substring(0, 8) }}</strong></p>
    <p>Fecha: {{ formatDate(sale.sale_date) }}</p>
    <p>Total: ${{ sale.total_amount_usd.toFixed(2) }}</p>
    <p>Saldo Pendiente: <strong class="balance-due">${{ sale.balance_due_usd.toFixed(2) }}</strong></p>
    <p v-if="sale.paid_amount_usd > 0">Abonado: ${{ sale.paid_amount_usd.toFixed(2) }}</p>
    <p>
      Estado: 
      <span :class="{
        'status-credito': sale.status === 'Crédito',
        'status-abonado': sale.status === 'Abonado',
        'status-pagado': sale.status === 'Pagado'
      }">
        {{ sale.status }}
      </span>
    </p>
    <p>Días Crédito: {{ sale.dias_credito }} días</p>
    <p>Vencimiento: {{ formatDate(sale.fecha_vencimiento) }}</p>
    <p v-if="sale.cancellation_code" class="cancellation-code">
      <small>Código requerido: {{ sale.cancellation_code }}</small>
    </p>
  </div>
                
                <div class="payment-section">
                  <h4>Realizar Pago</h4>
                  
                  <div class="form-group">
                    <label>Forma de Pago:</label>
                    <select v-model="paymentCurrencies[sale.id]" @change="resetPaymentAmount(sale)">
                      <option value="USD">Dólar (Efectivo/Transferencia)</option>
                      <option value="VES">Bolívares</option>
                    </select>
                  </div>
                  
                  <div class="form-group">
                    <label>Monto a Pagar:</label>
                    <input
                      type="number"
                      v-model="paymentAmounts[sale.id]"
                      :max="getMaxPaymentAmount(sale)"
                      :min="0.01"
                      step="0.01"
                      placeholder="0.00"
                      @input="validatePaymentAmount(sale)"
                    >
                    <small v-if="paymentCurrencies[sale.id] === 'USD'">
                      Máximo: ${{ sale.balance_due_usd.toFixed(2) }}
                    </small>
                    <small v-else>
                      Máximo: ${{ sale.balance_due_usd.toFixed(2) }} (equivalente en Bs)
                    </small>
                  </div>
                  
                  <div class="form-group" v-if="paymentCurrencies[sale.id] === 'VES'">
                    <label>Tasa de Cambio:</label>
                    <input
                      type="number"
                      v-model="exchangeRates[sale.id]"
                      step="0.01"
                      placeholder="Tasa de cambio Bs/$"
                      @input="validatePaymentAmount(sale)"
                    >
                    <small>Ingrese la tasa de cambio actual</small>
                  </div>
                  
                  <div class="form-group">
                    <label>Código de Cancelación del cliente:</label>
                    <input
                      type="text"
                      v-model="cancellationCodes[sale.id]"
                      placeholder="Ingrese código de cancelación"
                      required
                      :class="{ 'error-border': paymentErrors[sale.id] && !cancellationCodes[sale.id] }"
                    >
                    <small>Requerido para autorizar el pago</small>
                  </div>

                  <div class="form-group">
                    <label>Código de Cancelación del admin:</label>
                    <input
                      type="text"
                      v-model="admin_auth_code[sale.id]"
                      placeholder="Ingrese código de cancelación"
                      required
                    >
                    <small>Requerido para autorizar el pago</small>
                  </div>
                  
                  <div class="payment-summary" v-if="paymentAmounts[sale.id] > 0">
                    <p><strong>Resumen:</strong></p>
                    <p v-if="paymentCurrencies[sale.id] === 'USD'">
                      Pagando: ${{ paymentAmounts[sale.id] }} USD
                    </p>
                    <p v-else>
                      Pagando: Bs {{ paymentAmounts[sale.id] }} (Tasa: {{ exchangeRates[sale.id] || '0' }} Bs/$)
                    </p>
                    <p>Nuevo saldo: ${{ calculateNewBalance(sale).toFixed(2) }} USD</p>
                  </div>
                  
                  <button
                    @click="processPayment(sale)"
                    :disabled="!isValidPayment(sale) || paymentProcessing"
                    class="pay-btn"
                    :class="{ 
                      'disabled': !isValidPayment(sale) || paymentProcessing,
                      'success': calculateNewBalance(sale) === 0 
                    }"
                  >
                    {{ getPaymentButtonText(sale) }}
                  </button>

                  <div v-if="paymentErrors[sale.id]" class="error-message">
                    {{ paymentErrors[sale.id] }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal de confirmación -->
      <div v-if="showConfirmation" class="modal-overlay">
        <div class="modal-content confirmation-modal">
          <div class="modal-header">
            <h3>Confirmar Pago</h3>
          </div>
          <div class="modal-body">
            <p>{{ confirmationMessage }}</p>
            <div class="confirmation-buttons">
              <button @click="confirmPayment" class="confirm-btn">Confirmar</button>
              <button @click="cancelPayment" class="cancel-btn">Cancelar</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>

  <script>
  import axios from '../../axios';

  export default {
    name: 'CreditPayment',
    data() {
      return {
        searchTerm: '',
        customersWithCredit: [],
        selectedCustomer: null,
        customerSales: [],
        customerSalesLoading: false,
        loading: false,
        searchPerformed: false,
        searchError: '',
        paymentAmounts: {},
        paymentCurrencies: {},
        cancellationCodes: {},
        admin_auth_code:{},
        exchangeRates: {},
        paymentErrors: {},
        paymentProcessing: false,
        showConfirmation: false,
        confirmationMessage: '',
        pendingPaymentSale: null
      };
    },
    methods: {
      onSearchInput() {
        // Limpiar resultados anteriores cuando el usuario empiece a escribir
        if (this.searchTerm.length < 2) {
          this.customersWithCredit = [];
          this.searchPerformed = false;
          this.searchError = '';
        }
      },

      async searchCustomers() {
        if (this.searchTerm.length < 2) {
          this.searchError = 'Ingrese al menos 2 caracteres para buscar';
          return;
        }

        this.loading = true;
        this.searchError = '';
        this.searchPerformed = true;
        
        try {
          const response = await axios.get('/api/sales/customers-with-credit', {
            params: { search: this.searchTerm },
            timeout: 10000
          });
          
          if (response.data && Array.isArray(response.data)) {
            this.customersWithCredit = response.data.map(customer => ({
              ...customer,
              saldo_pendiente: parseFloat(customer.saldo_pendiente) || 0,
              ventas_credito_activas: parseInt(customer.ventas_credito_activas) || 0
            }));
          } else {
            this.customersWithCredit = [];
          }
          
        } catch (error) {
          console.error('Error buscando clientes:', error);
          
          if (error.response?.status === 500) {
            this.searchError = 'Error del servidor al buscar clientes. Intente más tarde.';
          } else if (error.code === 'ECONNABORTED') {
            this.searchError = 'La búsqueda tardó demasiado. Intente con menos caracteres.';
          } else if (error.response?.data?.msg) {
            this.searchError = error.response.data.msg;
          } else {
            this.searchError = 'Error de conexión al buscar clientes.';
          }
          
          this.customersWithCredit = [];
        } finally {
          this.loading = false;
        }
      },

      async viewCustomerSales(customer) {
    this.selectedCustomer = customer;
    this.customerSalesLoading = true;
    
    try {
      const response = await axios.get(`/api/sales/customer/${customer.id}/credit-sales`);
      this.customerSales = response.data;
      
      console.log('Ventas cargadas:', this.customerSales);
      
      // Reinicializar completamente los campos de pago
      this.paymentAmounts = {};
      this.paymentCurrencies = {};
      this.cancellationCodes = {};
      this.admin_auth_code= {};
      this.exchangeRates = {};
      this.paymentErrors = {};
      
      this.customerSales.forEach(sale => {
        // Establecer el monto máximo como saldo pendiente
        this.paymentAmounts[sale.id] = parseFloat(sale.balance_due_usd);
        this.paymentCurrencies[sale.id] = 'USD';
        this.cancellationCodes[sale.id] = '';
        this.admin_auth_code[sale.id] = '';
        this.exchangeRates[sale.id] = '';
        this.paymentErrors[sale.id] = '';
        
        console.log(`Venta ${sale.id}:`, {
          estado: sale.status,
          saldo: sale.balance_due_usd,
          pagado: sale.paid_amount_usd
        });
      });
      
    } catch (error) {
      console.error('Error cargando ventas:', error);
      let errorMsg = 'Error al cargar las ventas del cliente';
      if (error.response?.data?.msg) {
        errorMsg = error.response.data.msg;
      }
      alert(errorMsg);
    } finally {
      this.customerSalesLoading = false;
    }
  },

      resetPaymentAmount(sale) {
        // Resetear monto cuando cambia la moneda
        this.paymentAmounts[sale.id] = '';
        this.paymentErrors[sale.id] = '';
      },

      getMaxPaymentAmount(sale) {
        return parseFloat(sale.balance_due_usd);
      },

      validatePaymentAmount(sale) {
        const amount = parseFloat(this.paymentAmounts[sale.id]) || 0;
        const maxAmount = this.getMaxPaymentAmount(sale);
        
        if (amount > maxAmount) {
          this.paymentAmounts[sale.id] = maxAmount;
          this.paymentErrors[sale.id] = `El monto no puede exceder $${maxAmount.toFixed(2)} USD`;
        } else if (amount <= 0) {
          this.paymentErrors[sale.id] = 'El monto debe ser mayor a 0';
        } else if (this.paymentCurrencies[sale.id] === 'VES' && (!this.exchangeRates[sale.id] || this.exchangeRates[sale.id] <= 0)) {
          this.paymentErrors[sale.id] = 'Ingrese una tasa de cambio válida para pagos en bolívares';
        } else {
          this.paymentErrors[sale.id] = '';
        }
      },

      calculateNewBalance(sale) {
        const amount = parseFloat(this.paymentAmounts[sale.id]) || 0;
        const currentBalance = parseFloat(sale.balance_due_usd);
        
        if (this.paymentCurrencies[sale.id] === 'USD') {
          return Math.max(0, currentBalance - amount);
        } else {
          // Para bolívares, convertir a USD usando la tasa
          const exchangeRate = parseFloat(this.exchangeRates[sale.id]) || 1;
          const amountUSD = amount / exchangeRate;
          return Math.max(0, currentBalance - amountUSD);
        }
      },

      isValidPayment(sale) {
        const amount = parseFloat(this.paymentAmounts[sale.id]) || 0;
        const code = this.cancellationCodes[sale.id];
        const adminCode = this.admin_auth_code[sale.id]; 
        const maxAmount = this.getMaxPaymentAmount(sale);
        
        let valid = amount > 0 && 
                  amount <= maxAmount && 
                  code && 
                  code.trim().length > 0 &&
                     adminCode &&  // VALIDAR QUE EXISTA
              adminCode.toString().trim().length > 0 &&  // VALIDAR QUE NO ESTÉ VACÍO
                  !this.paymentErrors[sale.id];
        
        if (this.paymentCurrencies[sale.id] === 'VES') {
          valid = valid && this.exchangeRates[sale.id] && parseFloat(this.exchangeRates[sale.id]) > 0;
        }
        
        return valid;
      },

      getPaymentButtonText(sale) {
        if (this.paymentProcessing) return 'Procesando...';
        
        const newBalance = this.calculateNewBalance(sale);
        if (newBalance === 0) {
          return 'Cancelar Crédito Completo';
        } else {
          return 'Registrar Abono';
        }
      },

      async processPayment(sale) {
    if (!this.isValidPayment(sale)) {
        // Mostrar mensaje específico de qué falta
        let errorMessage = 'Por favor complete todos los campos correctamente:\n';
        
        if (!this.paymentAmounts[sale.id] || parseFloat(this.paymentAmounts[sale.id]) <= 0) {
            errorMessage += '• Monto a pagar\n';
        }
        if (!this.cancellationCodes[sale.id] || this.cancellationCodes[sale.id].trim() === '') {
            errorMessage += '• Código de cancelación del cliente\n';
        }
        if (!this.admin_auth_code[sale.id] || this.admin_auth_code[sale.id].toString().trim() === '') {
            errorMessage += '• Código de autorización del administrador\n';
        }
        if (this.paymentCurrencies[sale.id] === 'VES' && (!this.exchangeRates[sale.id] || this.exchangeRates[sale.id] <= 0)) {
            errorMessage += '• Tasa de cambio para pagos en bolívares\n';
        }
        
        alert(errorMessage);
        return;
    }

    const amount = parseFloat(this.paymentAmounts[sale.id]);
    const currency = this.paymentCurrencies[sale.id];
    const newBalance = this.calculateNewBalance(sale);
    
    // Preparar mensaje de confirmación
    let message = `¿Está seguro de registrar este pago?\n\n`;
    message += `Cliente: ${this.selectedCustomer.name}\n`;
    message += `Venta: #${sale.id.substring(0, 8)}\n`;
    message += `Monto: ${currency === 'USD' ? '$' : 'Bs '}${amount.toFixed(2)} ${currency}\n`;
    
    if (currency === 'VES') {
        message += `Tasa de cambio: ${this.exchangeRates[sale.id]} Bs/$\n`;
        message += `Equivalente: $${(amount / parseFloat(this.exchangeRates[sale.id])).toFixed(2)} USD\n`;
    }
    
    message += `Saldo anterior: $${parseFloat(sale.balance_due_usd).toFixed(2)} USD\n`;
    message += `Nuevo saldo: $${newBalance.toFixed(2)} USD\n`;
    message += `Código cliente: ${this.cancellationCodes[sale.id]}\n`;
    message += `Código admin: ${this.admin_auth_code[sale.id]}`;

    if (newBalance === 0) {
        message += `\n\n⚠️ ¡ATENCIÓN! Este pago CANCELARÁ COMPLETAMENTE el crédito.`;
    }

    this.confirmationMessage = message;
    this.pendingPaymentSale = sale;
    this.showConfirmation = true;
},

      async confirmPayment() {
    if (!this.pendingPaymentSale) return;

    this.showConfirmation = false;
    this.paymentProcessing = true;
    
    try {
      const sale = this.pendingPaymentSale;
      const paymentData = {
        customer_id: this.selectedCustomer.id,
        sale_id: sale.id,
        payment_amount: parseFloat(this.paymentAmounts[sale.id]),
        payment_currency: this.paymentCurrencies[sale.id],
        cancellation_code: this.cancellationCodes[sale.id].trim(),
        admin_auth_code: this.admin_auth_code[sale.id]  ? this.admin_auth_code[sale.id].trim() : ''

      };

      // Agregar tasa de cambio si es pago en bolívares
      if (this.paymentCurrencies[sale.id] === 'VES') {
        paymentData.exchange_rate = parseFloat(this.exchangeRates[sale.id]);
      }

      console.log('Enviando pago:', paymentData);
      
      const response = await axios.post('/api/sales/pay-credit', paymentData);
      
      // Mostrar mensaje específico según el estado
      alert(response.data.msg);
      
      // 🔄 ACTUALIZACIÓN MEJORADA: Recargar datos de forma más completa
      await this.reloadCustomerData();
      
      // Si el crédito fue completamente pagado, cerrar el modal
      if (response.data.new_status === 'Pagado') {
        setTimeout(() => {
          this.closeModal();
        }, 2000);
      }
      
    } catch (error) {
      console.error('Error procesando pago:', error);
      let errorMsg = 'Error al procesar el pago';
      if (error.response && error.response.data && error.response.data.msg) {
        errorMsg = error.response.data.msg;
      }
      alert(errorMsg);
    } finally {
      this.paymentProcessing = false;
      this.pendingPaymentSale = null;
    }
  },

  // 🔄 NUEVO MÉTODO PARA RECARGAR DATOS COMPLETAMENTE
  async reloadCustomerData() {
    if (!this.selectedCustomer) return;

    try {
      // 1. Recargar las ventas del cliente actual
      const salesResponse = await axios.get(`/api/sales/customer/${this.selectedCustomer.id}/credit-sales`);
      this.customerSales = salesResponse.data;
      
      // 2. Recargar la lista de clientes con crédito para actualizar saldos
      const customersResponse = await axios.get('/api/sales/customers-with-credit', {
        params: { search: this.searchTerm }
      });
      
      if (customersResponse.data && Array.isArray(customersResponse.data)) {
        this.customersWithCredit = customersResponse.data.map(customer => ({
          ...customer,
          saldo_pendiente: parseFloat(customer.saldo_pendiente) || 0,
          ventas_credito_activas: parseInt(customer.ventas_credito_activas) || 0
        }));
        
        // 3. Actualizar el cliente seleccionado con los nuevos datos
        // CORREGIDO en CreditPayment.vue
  // ...
  const updatedCustomer = this.customersWithCredit.find(c => c.id === this.selectedCustomer.id);
  if (updatedCustomer) {
    // ✅ Esto actualiza todas las propiedades del objeto reactivo
    Object.assign(this.selectedCustomer, updatedCustomer);
  }
  // ...
      }
      
      // En el método reloadCustomerData, después de cargar las ventas:
  console.log('Estado de ventas después del pago:');
  this.customerSales.forEach(sale => {
    console.log(`- ${sale.id}: ${sale.status} | Saldo: $${sale.balance_due_usd} | Pagado: $${sale.paid_amount_usd}`);
  });
      // 4. Reinicializar los campos de pago para las ventas actualizadas
      this.paymentAmounts = {};
      this.paymentCurrencies = {};
      this.cancellationCodes = {};
      this.exchangeRates = {};
      this.paymentErrors = {};
      
      this.customerSales.forEach(sale => {
        this.paymentAmounts[sale.id] = parseFloat(sale.balance_due_usd);
        this.paymentCurrencies[sale.id] = 'USD';
        this.cancellationCodes[sale.id] = '';
        this.exchangeRates[sale.id] = '';
        this.paymentErrors[sale.id] = '';
      });
      
      console.log('✅ Datos recargados correctamente después del pago');
      
    } catch (error) {
      console.error('Error recargando datos después del pago:', error);
      // Si falla la recarga, al menos recargar las ventas básicas
      await this.viewCustomerSales(this.selectedCustomer);
    }
  },

      cancelPayment() {
        this.showConfirmation = false;
        this.pendingPaymentSale = null;
      },

      closeModal() {
        this.selectedCustomer = null;
        this.customerSales = [];
        this.paymentAmounts = {};
        this.paymentCurrencies = {};
        this.cancellationCodes = {};
        this.admin_auth_code = {}; 
        this.exchangeRates = {};
        this.paymentErrors = {};
      },

      formatDate(date) {
        if (!date) return 'N/A';
        const d = new Date(date);
        return new Intl.DateTimeFormat('es-ES', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        }).format(d);
      }
    }
  };
  </script>

  <style scoped>
  .credit-payment-container {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .page-title {
    color: #333;
    margin-bottom: 30px;
    text-align: center;
  }

  .card {
    background: white;
    border-radius: 10px;
    padding: 25px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
  }

  .form-group {
    margin-bottom: 20px;
  }

  .form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #555;
  }

  .form-group input,
  .form-group select {
    width: 100%;
    padding: 10px;
    border: 2px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
    transition: border-color 0.3s;
  }

  .form-group input:focus,
  .form-group select:focus {
    border-color: #007bff;
    outline: none;
  }

  .form-group input.error-border {
    border-color: #e74c3c;
  }

  .form-group small {
    color: #666;
    font-size: 12px;
  }

  .search-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 10px;
    width: 100%;
  }

  .search-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }

  .search-btn:hover:not(:disabled) {
    background: #0056b3;
  }

  /* Modal Styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .modal-content {
    background: white;
    border-radius: 10px;
    width: 90%;
    max-width: 800px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .confirmation-modal {
    max-width: 500px;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #eee;
    background: #f8f9fa;
    border-radius: 10px 10px 0 0;
  }

  .modal-header h3 {
    margin: 0;
    color: #333;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #666;
  }

  .close-btn:hover {
    color: #333;
  }

  .modal-body {
    padding: 20px;
  }

  /* Customer Cards */
  .customers-list {
    display: grid;
    gap: 15px;
  }

  .customer-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #f9f9f9;
  }

  .customer-info h3 {
    margin: 0 0 10px 0;
    color: #333;
  }

  .customer-info p {
    margin: 5px 0;
    color: #666;
  }

  .view-sales-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
  }

  .view-sales-btn:hover:not(:disabled) {
    background: #0056b3;
  }

  .view-sales-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }

  /* Sales List */
  .sales-list {
    display: grid;
    gap: 20px;
  }

  .sale-item {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #f9f9f9;
  }

  .sale-info p {
    margin: 5px 0;
  }

  .balance-due {
    color: #e74c3c;
    font-size: 18px;
  }

  .cancellation-code {
    background: #e8f4fd;
    padding: 5px;
    border-radius: 3px;
    margin-top: 10px;
  }

  /* Payment Section */
  .payment-section {
    border-left: 2px solid #007bff;
    padding-left: 20px;
  }

  .payment-section h4 {
    margin-top: 0;
    color: #333;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
  }

  .payment-summary {
    background: #f8f9fa;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
    border-left: 3px solid #28a745;
  }

  .payment-summary p {
    margin: 5px 0;
    font-size: 14px;
  }

  .pay-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
    width: 100%;
    margin-top: 10px;
    transition: all 0.3s;
  }

  .pay-btn:hover:not(.disabled) {
    background: #218838;
    transform: translateY(-1px);
  }

  .pay-btn.success {
    background: #dc3545;
    font-weight: bold;
  }

  .pay-btn.success:hover:not(.disabled) {
    background: #c82333;
  }

  .pay-btn.disabled {
    background: #6c757d;
    cursor: not-allowed;
    opacity: 0.6;
    transform: none;
  }

  .confirmation-buttons {
    display: flex;
    gap: 10px;
    margin-top: 20px;
  }

  .confirm-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    flex: 1;
  }

  .confirm-btn:hover {
    background: #218838;
  }

  .cancel-btn {
    background: #6c757d;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    flex: 1;
  }

  .cancel-btn:hover {
    background: #5a6268;
  }

  /* Estados */
  .loading-state {
    text-align: center;
    padding: 20px;
    color: #666;
  }

  .no-results {
    text-align: center;
    padding: 20px;
    color: #666;
    font-style: italic;
  }

  .error-message {
    color: #e74c3c;
    font-size: 14px;
    margin-top: 5px;
    padding: 10px;
    background: #f8d7da;
    border-radius: 5px;
    border: 1px solid #f5c6cb;
  }

  .customer-summary {
    background: #e8f4fd;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
  }

  .customer-summary p {
    margin: 5px 0;
    font-weight: bold;
  }

  .status-credito {
    color: #e74c3c;
    font-weight: bold;
    background: #f8d7da;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .status-abonado {
    color: #e67e22;
    font-weight: bold;
    background: #fff3cd;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .status-pagado {
    color: #28a745;
    font-weight: bold;
    background: #d4edda;
    padding: 2px 8px;
    border-radius: 4px;
  }


  /* Responsive */
  @media (max-width: 768px) {
    .sale-item {
      grid-template-columns: 1fr;
    }
    
    .payment-section {
      border-left: none;
      border-top: 2px solid #007bff;
      padding-left: 0;
      padding-top: 20px;
    }
    
    .customer-card {
      flex-direction: column;
      align-items: flex-start;
      gap: 15px;
    }
    
    .confirmation-buttons {
      flex-direction: column;
    }
  }
  </style>
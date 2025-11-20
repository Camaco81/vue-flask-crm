<template>
  <div class="sales-container">
    <h1 class="page-title text-white">Gestión de Ventas</h1>
    <BackButton />

    <div class="card create-sale-card">
      <h2>Registrar Nueva Venta</h2>

      <div v-if="localStockAlerts.length > 0" class="alert-box warning-alert">
        <p>⚠️ **Advertencia de Stock Bajo (LOCAL):**</p>
        <ul>
          <li v-for="(alert, index) in localStockAlerts" :key="'local-alert-' + index">{{ alert }}</li>
        </ul>
      </div>

      <form @submit.prevent="createSale">
        <div class="form-group">
          <label for="customer">Seleccionar Cliente:</label>
          <AutocompleteSearch
            :items="customers"
            placeholder="Buscar cliente por nombre o cédula..."
            labelKey="fullSearchKey"
            valueKey="id"
            v-model="newSale.customer_id"
            id="customer"
            :secondaryLabelKey="null"
          />
        </div>

        <h3>Productos</h3>
        <div class="form-group product-item-group" v-for="(item, index) in newSale.items" :key="index">
          <div class="product-selection">
            <label :for="'product-' + index">Producto:</label>
            <AutocompleteSearch
              :items="products"
              placeholder="Buscar producto por nombre..."
              labelKey="name"
              valueKey="id"
              secondaryLabelKey="stock"
              :id="'product-autocomplete-' + index"
              :modelValue="item.product_id"
              @update:modelValue="handleProductSelection(item, $event)"
            />
          </div>

          <div class="quantity-input">
            <label :for="'quantity-' + index">Cantidad (Stock: {{ getProductStock(item.product_id) }}):</label>
            <input
              type="number"
              :id="'quantity-' + index"
              v-model.number="item.quantity"
              min="1"
              :max="getProductStock(item.product_id)"
              @input="checkLocalStockAlert(item)"
              required
            >
            <p v-if="item.quantity && item.quantity > getProductStock(item.product_id)" class="error-message">
              ⚠️ ¡La cantidad excede el stock disponible!
            </p>
          </div>
          
          <button type="button" @click="removeItem(index)" class="remove-btn">Quitar</button>
        </div>
        <button type="button" @click="addItem" class="add-item-btn">Agregar Producto</button>

        <hr class="separator">

        <h3>Resumen y Pago</h3>
        <div class="summary-box">
          <p>Total de Venta (USD): <strong>${{ calculateTotalAmountUSD().toFixed(2) }}</strong></p>
          <p>Total de Venta (Bs.): <strong>Bs. {{ (calculateTotalAmountUSD() * bcvRate).toFixed(2) }}</strong></p>
          <p>Tasa BCV actual: <strong>Bs. {{ bcvRate.toFixed(2) }}</strong></p>

          <div v-if="newSale.payment.method === 'CREDIT' && calculateBalanceDue() > 0" class="credit-summary">
            <p class="credit-warning">
              **Crédito Otorgado (Saldo Pendiente):** **${{ calculateBalanceDue().toFixed(2) }}**
            </p>
          </div>
          <p v-if="!isPaymentValid()" class="error-message">
            ⚠️ Monto pagado es insuficiente.
          </p>
        </div>

        <div class="form-group">
          <label for="payment-method">Forma de Pago:</label>
          <select id="payment-method" v-model="newSale.payment.method" @change="handlePaymentMethodChange">
            <option value="USD">Dólar (Efectivo/Transferencia)</option>
            <option value="VES">Bolívares (Transferencia/Punto)</option>
            <option value="MIXED">Mixto (USD + Bolívares)</option>
            <option value="CREDIT">Crédito/Fiado (Venta a Crédito)</option>
          </select>
        </div>

        <!-- Campos específicos para crédito -->
        <div v-if="newSale.payment.method === 'CREDIT'" class="credit-fields">
          <div class="form-group">
            <label for="credit-days">Días de Crédito:</label>
            <input
              type="number"
              id="credit-days"
              v-model.number="newSale.credit_days"
              min="1"
              required
            >
          </div>

          <div class="form-group">
            <label>Generar Código de Cancelación:</label>
            <button type="button" @click="openCancellationModal" class="generate-code-btn">
              🏷️ Generar Código
            </button>
            <p v-if="newSale.cancellation_code" class="code-display">
              Código generado: <strong>{{ newSale.cancellation_code }}</strong>
            </p>
          </div>
        </div>

        <div class="payment-fields-group">
          <div class="form-group" v-if="newSale.payment.method !== 'VES' && newSale.payment.method !== 'CREDIT'">
            <label for="usd-paid">Monto Pagado en Dólares ($):</label>
            <input
              type="number"
              id="usd-paid"
              v-model.number="newSale.payment.usd_paid"
              min="0"
              step="0.01"
              :required="newSale.payment.method !== 'VES'"
            >
          </div>

          <div class="form-group" v-if="newSale.payment.method !== 'USD' && newSale.payment.method !== 'CREDIT'">
            <label for="ves-paid">
              Monto Pagado en Bolívares (Bs):
              <span v-if="newSale.payment.method === 'MIXED'">
                (Bs. Req: {{ calculateVesRequired().toFixed(2) }})
              </span>
            </label>
            <input
              type="number"
              id="ves-paid"
              v-model.number="newSale.payment.ves_paid"
              min="0"
              step="0.01"
              :required="newSale.payment.method !== 'USD'"
            >
          </div>
        </div>
        
        <button
          type="submit"
          :disabled="creating || !isFormValid()"
          class="submit-btn"
        >
          {{ creating ? 'Registrando...' : 'Registrar Venta' }}
        </button>
      </form>
    </div>
    
    <!-- Modal para código de cancelación -->
    <CodeGeneratorModal 
      :show="showCancellationModal" 
      @close="showCancellationModal = false"
      @codeGenerated="handleCodeGenerated"
      ref="cancellationModalRef"
    />

    <!-- Modal para pago de crédito -->
    <CreditPayment 
      :show="showCreditPaymentModal"
      :sale="selectedSaleForPayment"
      @close="showCreditPaymentModal = false"
      @paymentSuccess="handlePaymentSuccess"
    />
    
    <div class="card sales-list-card">
      <h2>Ventas Registradas</h2>
      <div v-if="loading" class="loading-state">Cargando ventas...</div>
      <div v-else-if="sales.length === 0 && !loading" class="no-sales-state">No hay ventas registradas aún.</div>
      <ul v-else class="sales-list">
        <li v-for="sale in sales" :key="sale.id" class="sale-item">
          <div class="sale-header">
            <h3>Venta #{{ sale.id.substring(0, 8) }}... a {{ sale.customer_name }}</h3>
            <span>Total: **${{ sale.total_usd.toFixed(2) }}** (Bs. {{ sale.total_amount_ves.toFixed(2) }})</span>
          </div>
          <div class="sale-details">
  <p>Fecha: {{ formatDate(sale.sale_date) }}</p>
  <p>
    Estado:
    <span class="status-badge" 
      :class="{
        'pending': sale.status === 'Pendiente', 
        'completed': sale.status === 'Completado', 
        'credit': sale.status === 'Crédito',
        'abonado': sale.status === 'Abonado',
        'pagado': sale.status === 'Pagado'
      }"
    >
      {{ sale.status }}
    </span>
  </p>
  <p v-if="sale.seller_email">Vendedor: {{ sale.seller_email }}</p>
  <p>Tasa Utilizada: **Bs. {{ sale.exchange_rate_used.toFixed(2) }}**</p>
  <p class="payment-info">
    Pago: **{{ sale.payment_method || 'N/A' }}** 
    <span v-if="sale.payment_method !== 'Crédito'">
      (USD Pagado: ${{ sale.usd_paid.toFixed(2) }} / Bs Pagado: Bs. {{ sale.ves_paid.toFixed(2) }})
    </span>
  </p>
  
  <!-- Información de crédito mejorada - LÓGICA CORREGIDA -->
  <div v-if="sale.payment_method === 'Crédito'" class="credit-info">
    <p><strong>Total Venta:</strong> ${{ sale.total_usd.toFixed(2) }}</p>
    <p v-if="sale.paid_amount_usd > 0">
      <strong>Abonado:</strong> ${{ sale.paid_amount_usd.toFixed(2) }}
    </p>
    <p>
      <strong>Saldo Pendiente:</strong> 
      <span :class="{'balance-due': sale.balance_due_usd > 0, 'balance-paid': sale.balance_due_usd <= 0}">
        ${{ sale.balance_due_usd.toFixed(2) }}
      </span>
    </p>
    <p v-if="sale.balance_due_usd <= 0" class="fully-paid">
      ✅ <strong>Crédito Completamente Pagado</strong>
    </p>
    <p v-else-if="sale.paid_amount_usd > 0" class="partial-paid">
      ⚠️ <strong>Crédito Parcialmente Pagado</strong>
    </p>
    <p v-else class="not-paid">
      ⏳ <strong>Crédito Pendiente de Pago</strong>
    </p>
  </div>
  
  <p v-if="sale.dias_credito">
    <strong>Días de Crédito:</strong> {{ sale.dias_credito }} días
  </p>
  <p v-if="sale.fecha_vencimiento">
    <strong>Vencimiento:</strong> {{ formatDate(sale.fecha_vencimiento) }}
  </p>
  <p v-if="sale.cancellation_code" class="cancellation-code">
    <small><strong>Código Cancelación:</strong> {{ sale.cancellation_code }}</small>
  </p>
</div>
          <div class="sale-items">
            <h4>Elementos de la venta:</h4>
            <ul>
              <li v-for="item in sale.items" :key="item.product_name">
                {{ item.quantity }} x {{ item.product_name }} (${{ item.price_usd.toFixed(2) }})
              </li>
            </ul>
          </div>
          <div class="sale-actions">
            <button @click="generateInvoicePdf(sale)" class="pdf-btn">
              <i class="fas fa-file-pdf"></i> Generar Factura PDF
            </button>
            <button 
              v-if="sale.payment_method === 'Crédito' && sale.balance_due_usd > 0"
              @click="openCreditPayment(sale)"
              class="pay-credit-btn"
            >
              💳 {{ sale.paid_amount_usd > 0 ? 'Continuar Pago' : 'Pagar Crédito' }}
            </button>
            <span 
              v-if="sale.payment_method === 'Crédito' && sale.balance_due_usd <= 0" 
              class="fully-paid-badge"
            >
              ✅ Completado
            </span>
          </div>
        </li>
      </ul>
    </div>
  </div>

</template>

<script>
import AutocompleteSearch from './AutocompleteSearch.vue';
import axios from '../../axios';
import BackButton from './BackButton.vue';
import { jsPDF } from 'jspdf';
import CodeGeneratorModal from './CodeGeneratorModal.vue';
import CreditPayment from './CreditPayment.vue';

const STOCK_THRESHOLD = 10;
const PAYMENT_TOLERANCE = 0.02;

export default {
  name: 'SalesComponent',
  components: {
    BackButton,
    AutocompleteSearch,
    CodeGeneratorModal,
    CreditPayment
  },
  data() {
    return {
      sales: [],
      customers: [],
      products: [],
      showCancellationModal: false,
      showCreditPaymentModal: false,
      selectedSaleForPayment: null,
      newSale: {
        customer_id: null,
        items: [{ product_id: null, quantity: 1, price: 0 }],
        payment: {
          method: 'USD',
          usd_paid: 0,
          ves_paid: 0,
        },
        credit_days: 30,
        cancellation_code: ''
      },
      loading: false,
      creating: false,
      localStockAlerts: [],
      bcvRate: 0, 
    };
  },
  async mounted() {
    await this.fetchData();
  },
  methods: {
    openCreditPayment(sale) {
      this.selectedSaleForPayment = sale;
      this.showCreditPaymentModal = true;
    },

    async handlePaymentSuccess() {
      this.showCreditPaymentModal = false;
      this.selectedSaleForPayment = null;
      // Forzar recarga de datos
      await this.fetchData();
    },

    async fetchBcvRate() {
      try {
        const response = await axios.get('/api/exchange-rate');
        this.bcvRate = parseFloat(response.data.rate);
        console.log(`Tasa BCV obtenida: Bs. ${this.bcvRate.toFixed(2)}`);
      } catch (error) {
        console.error("Error fetching BCV rate. Using default rate of 36.5.", error);
        this.bcvRate = 36.5;
      }
    },

    async fetchData() {
  this.loading = true;
  try {
    await this.fetchBcvRate();

    const [salesResponse, customersResponse, productsResponse] = await Promise.all([
      axios.get('/api/sales'),
      axios.get('/api/customers'),
      axios.get('/api/products')
    ]);

    const customersMap = new Map(customersResponse.data.map(c => [c.id, c]));

    this.sales = salesResponse.data.map(sale => {
      const customer = customersMap.get(sale.customer_id) || { name: 'Cliente Desconocido', email: '', address: '' };
      
      // Calcular valores importantes
      const totalAmount = parseFloat(sale.total_amount_usd || sale.total_usd || 0);
      const balanceDue = parseFloat(sale.balance_due_usd || 0);
      const paidAmount = parseFloat(sale.paid_amount_usd || 0);
      const isCreditSale = sale.tipo_pago === 'Crédito' || sale.payment_method === 'Crédito';
      
      console.log(`Procesando venta ${sale.id}:`, {
        totalAmount,
        balanceDue,
        paidAmount,
        isCreditSale,
        tipo_pago: sale.tipo_pago,
        status_from_db: sale.status
      }); 
      
     
// Determinar el estado correcto - LÓGICA CORREGIDA

let status;

if (isCreditSale) {
  // Usar toFixed(2) para asegurar la verificación de cero
  const balanceDueCheck = balanceDue.toFixed(2); 
  
  // Si el saldo es menor o igual a la tolerancia, está Pagado
  if (balanceDueCheck <= PAYMENT_TOLERANCE) {
    status = 'Pagado';
  } else if (paidAmount > 0) {
    status = 'Abonado';
  } else {
    status = 'Crédito'; // Crédito recién creado sin abonos
  }
} else {
  // Para ventas normales (contado/mixto)
  status = 'Completado';
}
    
      return {
        ...sale,
        customer_name: customer.name,
        customer_email: customer.email,
        customer_address: customer.address,
        total_usd: totalAmount,
        total_amount_ves: parseFloat(sale.total_amount_ves || totalAmount * this.bcvRate),
        exchange_rate_used: parseFloat(sale.exchange_rate_used || this.bcvRate),
        usd_paid: parseFloat(sale.usd_paid || 0),
        ves_paid: parseFloat(sale.ves_paid || 0),
        payment_method: sale.tipo_pago || 'Contado',
        balance_due_usd: balanceDue,
        paid_amount_usd: paidAmount,
        status: status,
        cancellation_code: sale.cancellation_code || null,
        items: sale.items ? sale.items.map(item => ({
          ...item,
          price_usd: parseFloat(item.price_usd || item.price || 0)
        })) : []
      };
    });

    this.customers = customersResponse.data.map(c => ({
      ...c,
      cedula: c.cedula || 'N/A', 
      fullSearchKey: `${c.name} - Cédula: ${c.cedula || 'N/A'}`
    }));

    this.products = productsResponse.data.map(p => ({
      ...p,
      stock: Number(p.stock) || 0,
      price: Number(p.price) || 0
    }));

    // Debug: Verificar todas las ventas a crédito
    console.log('=== RESUMEN VENTAS A CRÉDITO ===');
    this.sales.filter(s => s.payment_method === 'Crédito').forEach(sale => {
      console.log(`Venta ${sale.id.substring(0, 8)}:`, {
        estado: sale.status,
        total: sale.total_usd,
        saldo: sale.balance_due_usd,
        pagado: sale.paid_amount_usd,
        deberiaSer: sale.balance_due_usd > 0 ? 'Crédito/Abonado' : 'Pagado'
      });
    });

  } catch (error) {
    console.error("Error fetching data:", error);
    alert('Error al cargar ventas o clientes/productos. Verifique la consola.');
  } finally {
    this.loading = false;
  }
},
    
    calculateTotalAmountUSD() {
      return this.newSale.items.reduce((total, item) => {
        const product = this.products.find(p => p.id === item.product_id);
        const price = product ? Number(product.price) : 0;
        const quantity = Number(item.quantity) || 0;
        return total + (price * quantity);
      }, 0);
    },
    
    calculateBalanceDue() {
      const totalUSD = this.calculateTotalAmountUSD();
      const usdPaid = Number(this.newSale.payment.usd_paid) || 0;
      const vesPaid = Number(this.newSale.payment.ves_paid) || 0;

      const vesPaidInUSD = this.bcvRate > 0 ? vesPaid / this.bcvRate : 0;
      const totalPaidInUSD = usdPaid + vesPaidInUSD;

      const balance = totalUSD - totalPaidInUSD;
      return balance > PAYMENT_TOLERANCE ? balance : 0;
    },

    calculateVesRequired() {
      const totalUSD = this.calculateTotalAmountUSD();
      const usdPaid = Number(this.newSale.payment.usd_paid) || 0;

      let remainingUSD = totalUSD - usdPaid;

      if (remainingUSD <= PAYMENT_TOLERANCE) {
        return 0;
      }

      return remainingUSD * this.bcvRate;
    },

    isPaymentValid() {
      if (this.newSale.payment.method === 'CREDIT') {
        return true; 
      }

      const totalUSD = this.calculateTotalAmountUSD();
      const usdPaid = Number(this.newSale.payment.usd_paid) || 0;
      const vesPaid = Number(this.newSale.payment.ves_paid) || 0;

      if (this.bcvRate === 0 && totalUSD > 0) return true;

      const vesPaidInUSD = vesPaid / this.bcvRate;
      const totalPaidInUSD = usdPaid + vesPaidInUSD;

      return totalPaidInUSD >= totalUSD - PAYMENT_TOLERANCE;
    },

    isFormValid() {
      // Validación básica
      if (!this.newSale.customer_id || 
          this.newSale.items.some(i => !i.product_id || i.quantity < 1 || i.quantity > this.getProductStock(i.product_id)) ||
          !this.isPaymentValid()) {
        return false;
      }

      // Validación específica para crédito
      if (this.newSale.payment.method === 'CREDIT') {
        if (!this.newSale.cancellation_code) {
          return false;
        }
        if (!this.newSale.credit_days || this.newSale.credit_days < 1) {
          return false;
        }
      }

      return true;
    },

    handlePaymentMethodChange() {
      this.newSale.payment.usd_paid = 0;
      this.newSale.payment.ves_paid = 0;
      this.newSale.cancellation_code = '';

      const totalUSD = this.calculateTotalAmountUSD();

      if (totalUSD === 0) return;

      if (this.newSale.payment.method === 'VES') {
        this.newSale.payment.ves_paid = totalUSD * this.bcvRate;
      }
      else if (this.newSale.payment.method === 'USD') {
        this.newSale.payment.usd_paid = totalUSD;
      }
    },

    getProductStock(productId) {
      const product = this.products.find(p => p.id === productId);
      return product ? product.stock : 0;
    },
    
    checkLocalStockAlert(item) {
      const product = this.products.find(p => p.id === item.product_id);
      if (!product || item.quantity < 1) return;

      this.updateLocalAlerts();

      if (item.quantity > product.stock) {
        item.quantity = product.stock;
      }
    },

    updateLocalAlerts() {
      const alerts = [];
      const validItems = this.newSale.items.filter(i => i.product_id && i.quantity > 0);

      for (const item of validItems) {
        const product = this.products.find(p => p.id === item.product_id);
        if (product) {
          const remaining_stock = product.stock - item.quantity;
          
          if (remaining_stock <= STOCK_THRESHOLD) {
            let alert_msg;
            if (remaining_stock < 0) {
              alert_msg = `ERROR: La cantidad excede el stock de ${product.name} (${product.stock}).`;
            } else if (remaining_stock === 0) {
              alert_msg = `ADVERTENCIA: El stock de ${product.name} se AGOTARÁ con esta venta.`;
            } else {
              alert_msg = `ALERTA: El stock de ${product.name} quedará en ${remaining_stock} (Umbral: ${STOCK_THRESHOLD}).`;
            }
            alerts.push(alert_msg);
          }
        }
      }
      this.localStockAlerts = [...new Set(alerts)];
    },

    addItem() {
      this.newSale.items.push({ product_id: null, quantity: 1, price: 0 });
      this.updateLocalAlerts();
      this.handlePaymentMethodChange();
    },

    removeItem(index) {
      if (this.newSale.items.length > 1) {
        this.newSale.items.splice(index, 1);
        this.updateLocalAlerts();
        this.handlePaymentMethodChange();
      }
    },

    handleProductSelection(item, productId) {
      item.product_id = productId;

      if (productId) {
        const selectedProduct = this.products.find(p => p.id === productId);
        if (selectedProduct) {
          item.price = selectedProduct.price;
          if (item.quantity > selectedProduct.stock) {
            item.quantity = selectedProduct.stock;
          }
          this.checkLocalStockAlert(item);
          this.handlePaymentMethodChange();
        }
      } else {
        item.price = 0;
        this.updateLocalAlerts();
        this.handlePaymentMethodChange();
      }
    },

    openCancellationModal() {
      this.showCancellationModal = true;
      this.$nextTick(() => {
        if (this.$refs.cancellationModalRef) {
          this.$refs.cancellationModalRef.generateInitialCode();
        }
      }); 
    },

    handleCodeGenerated(generatedCode) {
      this.newSale.cancellation_code = generatedCode;
      this.showCancellationModal = false;
    },

    async createSale() {
      if (!this.isFormValid()) {
        alert('Por favor, complete todos los campos requeridos correctamente.');
        return;
      }

      this.creating = true;
      try {
        const validItems = this.newSale.items
          .filter(i => i.product_id && i.quantity > 0 && i.quantity <= this.getProductStock(i.product_id))
          .map(item => ({
            product_id: item.product_id,
            quantity: Number(item.quantity),
            price: Number(item.price),
          }));

        let tipoPagoValue = 'Contado';
        let creditDaysValue = undefined;
        
        if (this.newSale.payment.method === 'CREDIT') {
          tipoPagoValue = 'Crédito'; 
          creditDaysValue = Number(this.newSale.credit_days); 
        }
        
        const salePayload = {
          customer_id: this.newSale.customer_id,
          items: validItems,
          tipo_pago: tipoPagoValue, 
          dias_credito: creditDaysValue, 
          usd_paid: Number(this.newSale.payment.usd_paid),
          ves_paid: Number(this.newSale.payment.ves_paid),
          cancellation_code: this.newSale.cancellation_code
        };
        
        const response = await axios.post('/api/sales', salePayload);
        const responseData = response.data;

        let successMessage = `Venta #${responseData.sale_id.substring(0, 8)}... registrada exitosamente!`;
        
        if (this.newSale.payment.method === 'CREDIT') {
          successMessage += `\n\n🔐 **VENTA A CRÉDITO REGISTRADA**\nCódigo de Cancelación: ${this.newSale.cancellation_code}\nGuarde este código para futuras cancelaciones.`;
        }
        
        if (responseData.stock_alerts && responseData.stock_alerts.length > 0) {
          successMessage += "\n\n⚠️ **ATENCIÓN INVENTARIO:**\n" + responseData.stock_alerts.join('\n');
        }

        alert(successMessage);
        
        this.resetForm();
        await this.fetchData();
        
      } catch (error) {
        console.error('Error al registrar la venta:', error.response ? error.response.data : error.message);
        let errorMessage = 'Error al registrar la venta. Por favor, inténtalo de nuevo.';
        if (error.response && error.response.data && error.response.data.msg) {
          errorMessage += ' Detalles: ' + error.response.data.msg;
        } else {
          errorMessage += ' Detalles: ' + error.message;
        }
        alert(errorMessage);
      } finally {
        this.creating = false;
        this.showCancellationModal = false;
      }
    },

    resetForm() {
      this.newSale = {
        customer_id: null,
        items: [{ product_id: null, quantity: 1, price: 0 }],
        payment: { 
          method: 'USD', 
          usd_paid: 0, 
          ves_paid: 0 
        },
        credit_days: 30,
        cancellation_code: ''
      };
      this.localStockAlerts = [];
    },

    generateInvoicePdf(sale) {
      const bcvRate = parseFloat(sale.exchange_rate_used);
      const totalAmountUSD = parseFloat(sale.total_usd);
      const totalAmountVES = parseFloat(sale.total_amount_ves);
      
      const balanceDueUSD = sale.balance_due_usd || 0; 
      const balanceDueVES = balanceDueUSD * bcvRate; 
      const paidAmountUSD = sale.paid_amount_usd || 0;

      const itemsWithVES = sale.items.map(item => {
        const priceUSD = parseFloat(item.price_usd);
        return {
          ...item,
          price_ves: priceUSD * bcvRate,
          total_ves: (priceUSD * item.quantity) * bcvRate,
          price_usd: priceUSD
        };
      });

      const doc = new jsPDF();
      let y = 10; 

      doc.setFontSize(18);
      doc.text("Factura de Venta", 105, y, null, null, "center");
      y += 10;
      doc.setFontSize(10);
      doc.text("Empresa XYZ S.A.", 105, y, null, null, "center");
      y += 5;
      doc.text("Av. Principal #123, Ciudad - RIF: J-12345678-9", 105, y, null, null, "center");
      y += 5;
      doc.text("contacto@empresa.com", 105, y, null, null, "center");
      y += 15;

      doc.setFontSize(12);
      doc.setFont(undefined, 'bold');
      doc.text("Detalles de la Factura", 10, y);
      doc.setFont(undefined, 'normal');
      y += 7;
      doc.text(`Número de Factura: ${sale.id.substring(0, 8).toUpperCase()}`, 10, y);
      y += 7;
      doc.text(`Fecha: ${this.formatDate(sale.sale_date)}`, 10, y);
      y += 7;
      doc.text(`Tasa de Cambio (VES/USD): Bs. ${bcvRate.toFixed(2)}`, 10, y);
      y += 7;
      doc.text(`Estado: ${sale.status}`, 10, y);

      if (sale.cancellation_code) {
        y += 7;
        doc.text(`Código Cancelación: ${sale.cancellation_code}`, 10, y);
      }

      if (sale.seller_email) {
        y += 7;
        doc.text(`Vendedor: ${sale.seller_email}`, 10, y);
      }
      y += 10;

      doc.setFont(undefined, 'bold');
      doc.text("Detalles del Cliente", 10, y);
      doc.setFont(undefined, 'normal');
      y += 7;
      doc.text(`Nombre: ${sale.customer_name}`, 10, y);
      if (sale.customer_email) {
        y += 7;
        doc.text(`Email: ${sale.customer_email}`, 10, y);
      }
      if (sale.customer_address) {
        y += 7;
        doc.text(`Dirección: ${sale.customer_address}`, 10, y);
      }
      y += 10;

      doc.setFontSize(10);
      doc.setFillColor(230, 230, 230);
      doc.rect(10, y, 190, 8, 'F');
      doc.setTextColor(0, 0, 0);
      doc.setFont(undefined, 'bold');

      doc.text("Producto", 12, y + 5);
      doc.text("Cantidad", 70, y + 5, null, null, "right"); 
      doc.text("P. Unitario USD", 105, y + 5, null, null, "right");
      doc.text("P. Unitario BS", 140, y + 5, null, null, "right");
      doc.text("TOTAL BS", 185, y + 5, null, null, "right");

      doc.setFont(undefined, 'normal');
      y += 8;

      doc.setFontSize(10);
      doc.setTextColor(50, 50, 50);

      itemsWithVES.forEach(item => {
        doc.text(item.product_name.substring(0, 30), 12, y + 5);
        doc.text(String(item.quantity), 70, y + 5, null, null, "right"); 
        doc.text(`$${item.price_usd.toFixed(2)}`, 105, y + 5, null, null, "right");
        doc.text(`Bs. ${item.price_ves.toFixed(2)}`, 140, y + 5, null, null, "right");
        doc.text(`Bs. ${item.total_ves.toFixed(2)}`, 185, y + 5, null, null, "right");
        y += 7;

        if (y > 270) {
          doc.addPage();
          y = 10;
          doc.setFontSize(10);
          doc.setFillColor(230, 230, 230);
          doc.rect(10, y, 190, 8, 'F');
          doc.setTextColor(0, 0, 0);
          doc.setFont(undefined, 'bold');
          doc.text("Producto", 12, y + 5);
          doc.text("Cantidad", 70, y + 5, null, null, "right");
          doc.text("P. Unitario USD", 105, y + 5, null, null, "right");
          doc.text("P. Unitario BS", 140, y + 5, null, null, "right");
          doc.text("TOTAL BS", 185, y + 5, null, null, "right");
          doc.setFont(undefined, 'normal');
          y += 8;
        }
      });

      y += 10;

      doc.setDrawColor(150, 150, 150);
      doc.setLineWidth(0.3);
      doc.line(120, y, 200, y);
      y += 5;

      doc.setFontSize(14);
      doc.setFont(undefined, 'bold');
      doc.text("TOTAL VENTA (Bs):", 120, y);
      doc.text(`Bs. ${totalAmountVES.toFixed(2)}`, 185, y, null, null, "right");
      y += 7; 

      // Mostrar información de crédito mejorada
      if (sale.status === 'Crédito' || sale.status === 'Abonado' || sale.status === 'Pagado') {
        doc.setFontSize(10);
        doc.setFont(undefined, 'normal');
        doc.text(`Estado del Crédito: ${sale.status}`, 120, y);
        y += 5;
        
        if (paidAmountUSD > 0) {
          doc.text(`Abonado (USD): $${paidAmountUSD.toFixed(2)}`, 120, y);
          y += 5;
        }
        
        if (balanceDueUSD > 0) {
          doc.setFontSize(12);
          doc.setFont(undefined, 'bold');
          doc.text(`SALDO PENDIENTE (Bs):`, 120, y);
          doc.text(`Bs. ${balanceDueVES.toFixed(2)}`, 185, y, null, null, "right");
          y += 7;
          doc.setFontSize(10);
          doc.setFont(undefined, 'normal');
          doc.text(`Saldo Referencial (USD): $${balanceDueUSD.toFixed(2)}`, 120, y);
        } else {
          doc.setFontSize(12);
          doc.setFont(undefined, 'bold');
          doc.text(`✅ CRÉDITO PAGADO COMPLETAMENTE`, 120, y);
          y += 7;
        }
      } else {
        doc.setFontSize(10);
        doc.setFont(undefined, 'normal');
        doc.text(`Total Referencial (USD): $${totalAmountUSD.toFixed(2)}`, 120, y);
        y += 5;
        doc.text(`Método de Pago: ${sale.payment_method || 'N/A'}`, 120, y);
        y += 5;
        doc.text(`Pagado en USD: $${sale.usd_paid.toFixed(2)}`, 120, y);
        y += 5;
        doc.text(`Pagado en BS: Bs. ${sale.ves_paid.toFixed(2)}`, 120, y);
      }
      
      y += 10;

      doc.setFontSize(8);
      doc.setTextColor(100, 100, 100);
      doc.text(`Generado el ${new Date().toLocaleDateString('es-ES')} a las ${new Date().toLocaleTimeString('es-ES')}`, 10, 290);
      doc.text("Gracias por su compra!", 105, 290, null, null, "center");

      doc.save(`Factura_Venta_${sale.id.substring(0, 8)}.pdf`);
    },
    
    formatDate(date) {
      const d = new Date(date);
      if (isNaN(d)) {
        return 'Fecha inválida';
      }
      return new Intl.DateTimeFormat('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }).format(d);
    }
  },
};
</script>






<style scoped>
.sales-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

.card {
  background: white;
  border-radius: 10px;
  padding: 25px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.create-sale-card {
  border-left: 4px solid #007bff;
}

.sales-list-card {
  border-left: 4px solid #28a745;
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

.product-item-group {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 15px;
  align-items: end;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 15px;
}

.product-selection {
  grid-column: 1;
}

.quantity-input {
  grid-column: 2;
}

.remove-btn {
  grid-column: 3;
  background: #dc3545;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 5px;
  cursor: pointer;
  height: fit-content;
}

.remove-btn:hover {
  background: #c82333;
}

.add-item-btn {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  margin-bottom: 20px;
}

.add-item-btn:hover {
  background: #138496;
}

.separator {
  margin: 25px 0;
  border: none;
  border-top: 2px solid #eee;
}

.summary-box {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.summary-box p {
  margin: 8px 0;
}

.credit-summary {
  background: #fff3cd;
  padding: 10px;
  border-radius: 5px;
  margin-top: 10px;
}

.credit-warning {
  color: #856404;
  font-weight: bold;
  margin: 0;
}

.credit-fields {
  background: #e8f4fd;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.payment-fields-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.generate-code-btn {
  background: #6f42c1;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 5px;
  cursor: pointer;
  margin-right: 10px;
}

.generate-code-btn:hover {
  background: #5a2d91;
}

.code-display {
  background: #d1ecf1;
  padding: 10px;
  border-radius: 5px;
  margin-top: 10px;
  font-family: monospace;
}

.submit-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  width: 100%;
  margin-top: 20px;
}
.text-white{
  color: white;
}

.submit-btn:hover:not(:disabled) {
  background: #218838;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}

.alert-box {
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.warning-alert {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  color: #856404;
}

.error-message {
  color: #dc3545;
  font-size: 14px;
  margin-top: 5px;
}

.loading-state {
  text-align: center;
  padding: 20px;
  color: #666;
}

.no-sales-state {
  text-align: center;
  padding: 40px;
  color: #666;
  font-style: italic;
}

.sales-list {
  list-style: none;
  padding: 0;
}

.sale-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background: #f9f9f9;
}

.sale-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.sale-header h3 {
  margin: 0;
  color: #333;
}

.sale-details p {
  margin: 5px 0;
  color: #666;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.completed {
  background: #d1edff;
  color: #0c5460;
}

.status-badge.credit {
  background: #f8d7da;
  color: #721c24;
}

.sale-items {
  margin-top: 15px;
}

.sale-items h4 {
  margin-bottom: 10px;
  color: #333;
}

.sale-items ul {
  list-style: none;
  padding-left: 0;
}

.sale-items li {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
}

.sale-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  flex-wrap: wrap;
}

.pdf-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.pdf-btn:hover {
  background: #c82333;
}

.pay-credit-btn {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.pay-credit-btn:hover {
  background: linear-gradient(135deg, #218838, #1e9e8a);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

/* Responsive */
@media (max-width: 768px) {
  .product-item-group {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .payment-fields-group {
    grid-template-columns: 1fr;
  }
  
  .sale-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .sale-actions {
    flex-direction: column;
  }
  
  .sales-container {
    padding: 10px;
  }
}
.balance-due {
  color: #e74c3c;
  font-weight: bold;
}

.balance-paid {
  color: #27ae60;
  font-weight: bold;
}

.fully-paid {
  color: #27ae60;
  background: #d4edda;
  padding: 5px;
  border-radius: 4px;
  font-weight: bold;
}

.partial-paid {
  color: #e67e22;
  background: #fff3cd;
  padding: 5px;
  border-radius: 4px;
  font-weight: bold;
}

.not-paid {
  color: #f39c12;
  background: #fef9e7;
  padding: 5px;
  border-radius: 4px;
  font-weight: bold;
}
</style>


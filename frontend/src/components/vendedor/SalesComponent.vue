<template>
  <div class="sales-container">
    <h1 class="page-title text-white">Gestión de Ventas</h1>
    <BackButton />

    <!-- Panel principal con dos columnas -->
    <div class="dashboard-grid">
      <!-- Columna izquierda: Registrar venta -->
      <div class="col-left">
        <div class="card create-sale-card">
          <h2 class="card-header">
            <i class="fas fa-cart-plus"></i>
            Registrar Nueva Venta
          </h2>

          <div v-if="localStockAlerts.length > 0" class="alert-box warning-alert">
            <p><i class="fas fa-exclamation-triangle"></i> <strong>Advertencia de Stock Bajo:</strong></p>
            <ul>
              <li v-for="(alert, index) in localStockAlerts" :key="'local-alert-' + index">{{ alert }}</li>
            </ul>
          </div>

          <!-- Formulario compacto -->
          <form @submit.prevent="createSale" class="sale-form">
            <!-- Sección rápida de cliente -->
            <div class="quick-section">
              <label class="section-label"><i class="fas fa-user"></i> Cliente</label>
              <AutocompleteSearch :items="customers" placeholder="Buscar cliente..." labelKey="fullSearchKey"
                valueKey="id" v-model="newSale.customer_id" :secondaryLabelKey="null" class="compact-autocomplete" />
              <span v-if="newSale.customer_id" class="selected-info">
                Cliente seleccionado
              </span>
            </div>

            <!-- Sección de productos en acordeón -->
            <div class="quick-section">
              <div class="section-header" @click="showProductsSection = !showProductsSection">
                <label class="section-label">
                  <i class="fas fa-boxes"></i> Productos ({{newSale.items.filter(i => i.product_id).length}})
                </label>
                <i class="fas" :class="showProductsSection ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
              </div>

              <div v-show="showProductsSection" class="products-section">
                <div class="product-item-group" v-for="(item, index) in newSale.items" :key="index">
                  <div class="product-row">
                    <AutocompleteSearch :items="products" placeholder="Producto..." labelKey="name" valueKey="id"
                      secondaryLabelKey="stock" :modelValue="item.product_id"
                      @update:modelValue="handleProductSelection(item, $event)" class="product-autocomplete" />

                    <div class="quantity-controls">
                      <button type="button" @click="item.quantity > 1 ? item.quantity-- : null" class="qty-btn"
                        :disabled="item.quantity <= 1">-</button>
                      <input type="number" v-model.number="item.quantity" min="1"
                        :max="getProductStock(item.product_id)" class="qty-input" @input="checkLocalStockAlert(item)">
                      <button type="button"
                        @click="item.quantity < getProductStock(item.product_id) ? item.quantity++ : null"
                        class="qty-btn"
                        :disabled="!item.product_id || item.quantity >= getProductStock(item.product_id)">+</button>
                    </div>

                    <span class="price-display" v-if="item.product_id">
                      ${{ (getProductPrice(item.product_id) * item.quantity).toFixed(2) }}
                    </span>

                    <button type="button" @click="removeItem(index)" class="remove-btn-icon"
                      :disabled="newSale.items.length <= 1" title="Quitar producto">
                      <i class="fas fa-times"></i>
                    </button>
                  </div>

                  <div v-if="item.product_id" class="product-info">
                    <small>Stock: {{ getProductStock(item.product_id) }} |
                      Precio: ${{ getProductPrice(item.product_id).toFixed(2) }}</small>
                  </div>
                </div>

                <button type="button" @click="addItem" class="add-item-btn">
                  <i class="fas fa-plus"></i> Agregar Producto
                </button>
              </div>
            </div>

            <!-- Resumen rápido -->
            <div class="quick-summary">
              <div class="summary-row">
                <span>Total USD:</span>
                <strong>${{ calculateTotalAmountUSD().toFixed(2) }}</strong>
              </div>
              <div class="summary-row">
                <span>Total Bs:</span>
                <strong>Bs. {{ (calculateTotalAmountUSD() * bcvRate).toFixed(2) }}</strong>
              </div>
              <div class="summary-row">
                <span>Tasa BCV:</span>
                <strong>Bs. {{ bcvRate.toFixed(2) }}</strong>
              </div>
            </div>

            <!-- Método de pago compacto -->
            <div class="quick-section">
              <label class="section-label"><i class="fas fa-credit-card"></i> Pago</label>
              <div class="payment-methods">
                <button type="button" v-for="method in paymentMethods" :key="method.value"
                  @click="selectPaymentMethod(method.value)" class="payment-method-btn"
                  :class="{ active: newSale.payment.method === method.value }">
                  <i :class="method.icon"></i>
                  {{ method.label }}
                </button>
              </div>

              <!-- Campos de pago dinámicos -->
              <div class="payment-fields" v-if="newSale.payment.method !== 'CREDIT'">
                <div class="payment-input" v-if="newSale.payment.method !== 'VES'">
                  <label>USD Pagado:</label>
                  <input type="number" v-model.number="newSale.payment.usd_paid" min="0" step="0.01"
                    :placeholder="`Máx: $${calculateTotalAmountUSD().toFixed(2)}`" class="compact-input">
                </div>

                <div class="payment-input" v-if="newSale.payment.method !== 'USD'">
                  <label>Bs Pagados:</label>
                  <input type="number" v-model.number="newSale.payment.ves_paid" min="0" step="0.01" readonly
                    :placeholder="`Req: Bs. ${calculateVesRequired()}`" class="compact-input">
                </div>
              </div>

              <!-- Campos para crédito -->
              <div v-if="newSale.payment.method === 'CREDIT'" class="credit-fields">
                <div class="form-group-inline">
                  <label>Días:</label>
                  <input type="number" v-model.number="newSale.credit_days" min="1" max="365" class="compact-input">
                </div>

                <div class="form-group-inline">
                  <label>Código:</label>
                  <input type="text" v-model="newSale.cancellation_code" placeholder="Código de cancelación"
                    class="compact-input" readonly>
                  <button type="button" @click="openCancellationModal" class="icon-btn-small">
                    <i class="fas fa-tag"></i>
                  </button>
                </div>
                <div class="form-group-inline full-width">
                  <label><i class="fas fa-user-shield"></i> Código Admin:</label>
                  <input type="text" v-model="newSale.admin_auth_code"
                    placeholder="Ingrese código de autorización del administrador" class="compact-input" maxlength="10">
                  <button type="button" @click="fetchAdminCode" class="icon-btn-small" title="Obtener código del día">
                    <i class="fas fa-sync"></i>
                  </button>
                </div>

              </div>


              <div v-if="!isPaymentValid() && newSale.payment.method !== 'CREDIT'" class="error-message">
                <i class="fas fa-exclamation-circle"></i> Monto pagado insuficiente
              </div>

              <div v-if="newSale.payment.method === 'CREDIT' && calculateBalanceDue() > 0" class="credit-warning">
                <i class="fas fa-handshake"></i> Crédito: Saldo ${{ calculateBalanceDue().toFixed(2) }}
              </div>
            </div>

            <!-- Botón de registro -->
            <button type="submit" :disabled="creating || !isFormValid()" class="submit-btn-primary">
              <i class="fas" :class="creating ? 'fa-spinner fa-spin' : 'fa-check-circle'"></i>
              {{ creating ? 'Procesando...' : 'Registrar Venta' }}
            </button>
          </form>
        </div>
      </div>

      <!-- Columna derecha: Lista de ventas -->
      <div class="col-right">
        <div class="card sales-list-card">
          <div class="list-header">
            <h2><i class="fas fa-history"></i> Ventas Registradas</h2>

            <!-- Filtros rápidos -->
            <div class="filters-bar">
              <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" v-model="searchQuery" placeholder="Buscar cliente o ID..." class="search-input">
              </div>

              <select v-model="statusFilter" class="filter-select">
                <option value="">Todos los estados</option>
                <option value="Completado">Completado</option>
                <option value="Crédito">Crédito</option>
                <option value="Abonado">Abonado</option>
                <option value="Pagado">Pagado</option>
                <option value="Pendiente">Pendiente</option>
              </select>

              <select v-model="paymentFilter" class="filter-select">
                <option value="">Todos los pagos</option>
                <option value="Contado">Contado</option>
                <option value="Crédito">Crédito</option>
              </select>
            </div>
          </div>

          <!-- Lista de ventas -->
          <div v-if="loading" class="loading-state">
            <i class="fas fa-spinner fa-spin"></i> Cargando ventas...
          </div>

          <div v-else-if="filteredSales.length === 0" class="no-sales-state">
            <i class="fas fa-shopping-cart"></i>
            <p>No hay ventas registradas</p>
            <small v-if="searchQuery || statusFilter || paymentFilter">Intenta con otros filtros</small>
          </div>

          <div v-else class="sales-list-scroll">
            <div v-for="sale in filteredSales" :key="sale.id" class="sale-card" :class="{
              'credit-sale': sale.payment_method === 'Crédito',
              'paid-sale': sale.status === 'Pagado',
              'partial-sale': sale.status === 'Abonado'
            }">
              <div class="sale-card-header">
                <div class="sale-title">
                  <h3>{{ sale.customer_name }}</h3>
                  <small class="sale-id">#{{ sale.id.substring(0, 8) }}</small>
                </div>
                <div class="sale-total">
                  <strong>${{ sale.total_usd.toFixed(2) }}</strong>
                  <small>Bs. {{ sale.total_amount_ves.toFixed(2) }}</small>
                </div>
              </div>

              <div class="sale-card-body">
                <div class="sale-info">
                  <span class="sale-date">
                    <i class="far fa-calendar"></i> {{ formatDateShort(sale.sale_date) }}
                  </span>
                  <span class="sale-status" :class="sale.status.toLowerCase()">
                    {{ sale.status }}
                  </span>
                  <span class="sale-payment">
                    <i class="fas fa-money-bill-wave"></i> {{ sale.payment_method }}
                  </span>
                </div>

                <!-- Resumen de crédito -->
                <div v-if="sale.payment_method === 'Crédito'" class="credit-summary-compact">
                  <div class="credit-row">
                    <span>Saldo:</span>
                    <strong :class="sale.balance_due_usd > 0 ? 'balance-due' : 'balance-paid'">
                      ${{ sale.balance_due_usd.toFixed(2) }}
                    </strong>
                  </div>
                  <div class="credit-row" v-if="sale.paid_amount_usd > 0">
                    <span>Abonado:</span>
                    <span>${{ sale.paid_amount_usd.toFixed(2) }}</span>
                  </div>
                </div>

                <!-- Acciones rápidas -->
                <div class="sale-actions-compact">
                  <button v-if="sale.payment_method === 'Crédito' && sale.balance_due_usd > 0"
                    @click="openCreditPayment(sale)" class="action-btn pay-btn" title="Registrar pago">
                    <i class="fas fa-hand-holding-dollar"></i>
                    <span>Pagar</span>
                  </button>

                  <button @click="generateInvoicePdf(sale)" class="action-btn pdf-btn" title="Factura PDF">
                    <i class="fas fa-file-pdf"></i>
                  </button>

                  <button v-if="sale.status !== 'Pagado' && sale.status !== 'Completado' && sale.status !== 'Cancelado'"
                    @click="confirmCancellation(sale)" class="action-btn cancel-btn" title="Cancelar venta">
                    <i class="fas fa-ban"></i>
                  </button>

                  <button @click="toggleSaleDetails(sale.id)" class="action-btn details-btn"
                    :title="expandedSale === sale.id ? 'Ocultar detalles' : 'Ver detalles'">
                    <i class="fas" :class="expandedSale === sale.id ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                  </button>
                </div>

                <!-- Detalles expandibles -->
                <div v-if="expandedSale === sale.id" class="sale-details-expanded">
                  <div class="detail-section">
                    <h4><i class="fas fa-box"></i> Productos</h4>
                    <div class="products-list">
                      <div v-for="item in sale.items" :key="item.product_name" class="product-item">
                        <span>{{ item.quantity }}x {{ item.product_name }}</span>
                        <span>${{ item.price_usd.toFixed(2) }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="detail-section">
                    <h4><i class="fas fa-info-circle"></i> Información</h4>
                    <div class="info-grid">
                      <div><strong>Vendedor:</strong> {{ sale.seller_email || 'No especificado' }}</div>
                      <div><strong>Tasa BCV:</strong> Bs. {{ sale.exchange_rate_used.toFixed(2) }}</div>
                      <div v-if="sale.dias_credito">
                        <strong>Días crédito:</strong> {{ sale.dias_credito }}
                      </div>
                      <div v-if="sale.fecha_vencimiento">
                        <strong>Vence:</strong> {{ formatDateShort(sale.fecha_vencimiento) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Paginación -->
          <div v-if="filteredSales.length > 0" class="pagination">
            <button @click="currentPage--" :disabled="currentPage === 1" class="page-btn">
              <i class="fas fa-chevron-left"></i>
            </button>
            <span class="page-info">Página {{ currentPage }} de {{ totalPages }}</span>
            <button @click="currentPage++" :disabled="currentPage >= totalPages" class="page-btn">
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modales -->
    <CodeGeneratorModal :show="showCancellationModal" @close="showCancellationModal = false"
      @codeGenerated="handleCodeGenerated" ref="cancellationModalRef" />

    <CreditPayment :show="showCreditPaymentModal" :sale="selectedSaleForPayment" @close="showCreditPaymentModal = false"
      @paymentSuccess="handlePaymentSuccess" />
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
const ITEMS_PER_PAGE = 5;

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
      showProductsSection: true,
      expandedSale: null,
      searchQuery: '',
      statusFilter: '',
      paymentFilter: '',
      currentPage: 1,
      newSale: {
        customer_id: null,
        items: [{ product_id: null, quantity: 1, price: 0 }],
        payment: {
          method: 'USD',
          usd_paid: 0,
          ves_paid: 0,
        },
        credit_days: 30,
        cancellation_code: '',
        admin_auth_code: '',
      },
      loading: false,
      creating: false,
      localStockAlerts: [],
      bcvRate: 0,
      paymentMethods: [
        { value: 'USD', label: 'USD', icon: 'fa-dollar-sign' },
        { value: 'VES', label: 'Bs', icon: 'fa-boliviano-sign' },
        { value: 'MIXED', label: 'Mixto', icon: 'fa-money-bill-transfer' },
        { value: 'CREDIT', label: 'Crédito', icon: 'fa-handshake' }
      ]
    };
  },
  async mounted() {
    await this.fetchData();
  },
  computed: {
    filteredSales() {
      let filtered = this.sales;

      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        filtered = filtered.filter(sale =>
          sale.customer_name.toLowerCase().includes(query) ||
          sale.id.toLowerCase().includes(query)
        );
        // console.log(filtered)
      }

      if (this.statusFilter) {
        filtered = filtered.filter(sale => sale.status === this.statusFilter);
      }

      if (this.paymentFilter) {
        filtered = filtered.filter(sale => sale.payment_method === this.paymentFilter);
      }

      return filtered;
    },

    paginatedSales() {
      const start = (this.currentPage - 1) * ITEMS_PER_PAGE;
      const end = start + ITEMS_PER_PAGE;
      return this.filteredSales.slice(start, end);
    },

    totalPages() {
      return Math.ceil(this.filteredSales.length / ITEMS_PER_PAGE);
    }
  },
  watch: {
    searchQuery() {
      this.currentPage = 1;
    },
    statusFilter() {
      this.currentPage = 1;
    },
    paymentFilter() {
      this.currentPage = 1;
    }
  },
  methods: {

    selectPaymentMethod(method) {
      this.newSale.payment.method = method;
      this.handlePaymentMethodChange();
    },

    getProductPrice(productId) {
      const product = this.products.find(p => p.id === productId);
      return product ? Number(product.price) : 0;
    },

    formatDateShort(date) {
      const d = new Date(date);
      if (isNaN(d)) return 'Fecha inválida';
      return new Intl.DateTimeFormat('es-ES', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(d);
    },

    toggleSaleDetails(saleId) {
      this.expandedSale = this.expandedSale === saleId ? null : saleId;
    },

    confirmCancellation(sale) {
      if (confirm(`¿Estás seguro de que quieres cancelar la Venta #${sale.id.substring(0, 8)}? Esta acción es irreversible.`)) {
        // TODO: Implementar la lógica real para llamar a la API de cancelación
        // this.cancelSale(sale.id); 
        alert(`Venta ${sale.id.substring(0, 8)} marcada para cancelación. Por favor, implementa la llamada a la API de cancelación.`);
      }
    },

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
          const customerId = sale.customer_id || sale.customer_name;
          const customer = customersMap.get(customerId) || {
            name: sale.customer_name || 'Cliente Desconocido',
            email: 'N/A',
            address: 'N/A'
          };


          // Calcular valores importantes
          const totalAmount = parseFloat(sale.total_amount_usd || sale.total_usd || 0);
          const balanceDue = parseFloat(sale.balance_due_usd || 0);
          const paidAmount = parseFloat(sale.paid_amount_usd || 0);
          const isCreditSale = sale.tipo_pago === 'Crédito' || sale.payment_method === 'Crédito';

          console.log(`Procesando venta ${sale.id}:`, {
            totalAmount,
            balanceDue,
            name_client: sale.customer_name,
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

      // Usamos la constante de tolerancia que ya definiste
      if (remainingUSD <= 0.01) {
        return 0;
      }

      // Calculamos el monto en VES
      const totalVES = remainingUSD * this.bcvRate;

      /**
       * CORRECCIÓN: 
       * 1. toFixed(2) redondea y convierte a string "XX.XX"
       * 2. Number() lo convierte de nuevo a valor numérico para que el 
       * input type="number" lo acepte sin errores de validación.
       */
      return Number(totalVES.toFixed(2));
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
      if (!this.newSale.customer_name ||
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
        // NUEVO: Validar código del administrador
        if (!this.newSale.admin_auth_code || this.newSale.admin_auth_code.trim().length < 4) {
          return false;
        }
      }

      return true;
    },

    handlePaymentMethodChange() {
      this.newSale.payment.usd_paid = 0;
      this.newSale.payment.ves_paid = 0;
      this.newSale.cancellation_code = '';
      this.newSale.admin_auth_code = '';

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
          cancellation_code: this.newSale.cancellation_code,
          admin_auth_code: this.newSale.admin_auth_code
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
        cancellation_code: '',
        admin_auth_code: ''
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
/* Estilos mejorados para UI/UX y responsive */

.sales-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  color: white;
  margin-bottom: 20px;
  text-align: center;
  font-size: 1.8rem;
}

/* Layout principal */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 20px;
  margin-top: 20px;
}

@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

/* Tarjetas */
.card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  height: fit-content;
  max-height: calc(100vh - 150px);
  overflow-y: auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.3rem;
}

/* Formulario compacto */
.sale-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.quick-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #e9ecef;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #495057;
  margin-bottom: 10px;
  font-size: 0.95rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 5px 0;
}

.section-header:hover {
  opacity: 0.8;
}

/* Productos */
.product-item-group {
  background: white;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #dee2e6;
}

.product-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.product-autocomplete {
  flex: 1;
  min-width: 200px;
}

.quantity-controls {
  display: flex;
  align-items: center;
  gap: 5px;
}

.qty-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.qty-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qty-input {
  width: 60px;
  padding: 5px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  text-align: center;
}

.price-display {
  font-weight: 600;
  color: #28a745;
  min-width: 80px;
}

.remove-btn-icon {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
}

.remove-btn-icon:hover {
  background: #f8d7da;
}

.product-info {
  margin-top: 5px;
  padding-top: 5px;
  border-top: 1px dashed #dee2e6;
  font-size: 0.85rem;
  color: #6c757d;
}

/* Resumen rápido */
.quick-summary {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  padding: 15px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.summary-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.summary-row span {
  font-size: 0.85rem;
  color: #6c757d;
}

.summary-row strong {
  font-size: 1.1rem;
  color: #2c3e50;
}

/* Métodos de pago */
.payment-methods {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 15px;
}

.payment-method-btn {
  padding: 10px;
  border: 2px solid #dee2e6;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.payment-method-btn:hover {
  border-color: #007bff;
}

.payment-method-btn.active {
  border-color: #007bff;
  background: #e7f3ff;
  color: #007bff;
}

.payment-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .payment-fields {
    grid-template-columns: 1fr;
  }
}

.payment-input {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.compact-input {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 0.9rem;
}

/* Crédito */
.credit-fields {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.form-group-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn-small {
  padding: 8px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

/* Botones */
.add-item-btn {
  width: 100%;
  padding: 10px;
  background: #17a2b8;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 0.9rem;
}

.add-item-btn:hover {
  background: #138496;
}

.submit-btn-primary {
  padding: 15px;
  background: linear-gradient(135deg, #28a745 0%, #218838 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 10px;
}

.submit-btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838 0%, #1e7e34 100%);
}

.submit-btn-primary:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.7;
}

/* Lista de ventas */
.list-header {
  margin-bottom: 20px;
}

.filters-bar {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  position: relative;
  min-width: 200px;
}

.search-box i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #6c757d;
}

.search-input {
  width: 100%;
  padding: 10px 10px 10px 35px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 0.9rem;
}

.filter-select {
  padding: 10px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
  min-width: 150px;
}

/* Tarjeta de venta */
.sales-list-scroll {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 5px;
}

.sale-card {
  background: white;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  border: 1px solid #dee2e6;
  transition: all 0.2s;
}

.sale-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.sale-card.credit-sale {
  border-left: 4px solid #ffc107;
}

.sale-card.paid-sale {
  border-left: 4px solid #28a745;
}

.sale-card.partial-sale {
  border-left: 4px solid #17a2b8;
}

.sale-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.sale-title h3 {
  margin: 0;
  font-size: 1rem;
  color: #2c3e50;
}

.sale-id {
  color: #6c757d;
  font-size: 0.8rem;
}

.sale-total {
  text-align: right;
}

.sale-total strong {
  font-size: 1.2rem;
  color: #28a745;
}

.sale-total small {
  display: block;
  color: #6c757d;
  font-size: 0.85rem;
}

.sale-card-body {
  font-size: 0.9rem;
}

.sale-info {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  color: #6c757d;
}

.sale-status {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.sale-status.completado {
  background: #d1edff;
  color: #0c5460;
}

.sale-status.crédito {
  background: #fff3cd;
  color: #856404;
}

.sale-status.abonado {
  background: #d4edda;
  color: #155724;
}

.sale-status.pagado {
  background: #c3e6cb;
  color: #1a5e2f;
}

.sale-status.pendiente {
  background: #f8d7da;
  color: #721c24;
}

/* Resumen crédito compacto */
.credit-summary-compact {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 10px;
  margin: 10px 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.credit-row {
  display: flex;
  justify-content: space-between;
}

/* Acciones compactas */
.sale-actions-compact {
  display: flex;
  gap: 8px;
  margin-top: 15px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.pay-btn {
  background: #28a745;
  color: white;
}

.pdf-btn {
  background: #6f42c1;
  color: white;
}

.cancel-btn {
  background: #dc3545;
  color: white;
}

.details-btn {
  background: #6c757d;
  color: white;
}

/* Detalles expandidos */
.sale-details-expanded {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #dee2e6;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-section {
  margin-bottom: 15px;
}

.detail-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 10px 0;
  font-size: 0.95rem;
  color: #495057;
}

.products-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-item {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 0.85rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  font-size: 0.85rem;
}

@media (max-width: 576px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}

/* Paginación */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #dee2e6;
}

.page-btn {
  padding: 8px 15px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #6c757d;
  font-size: 0.9rem;
}

/* Alertas y mensajes */
.alert-box {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 15px;
  font-size: 0.9rem;
}

.warning-alert {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  color: #856404;
}

.error-message {
  color: #dc3545;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 5px;
}

.credit-warning {
  color: #e67e22;
  background: #fff3cd;
  padding: 8px;
  border-radius: 6px;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

/* Responsive */
@media (max-width: 768px) {
  .payment-methods {
    grid-template-columns: repeat(2, 1fr);
  }

  .sale-card-header {
    flex-direction: column;
    gap: 10px;
  }

  .sale-total {
    text-align: left;
  }

  .quick-summary {
    grid-template-columns: 1fr;
    gap: 15px;
  }
}

@media (max-width: 480px) {
  .sales-container {
    padding: 10px;
  }

  .card {
    padding: 15px;
  }

  .filters-bar {
    flex-direction: column;
  }

  .search-box,
  .filter-select {
    min-width: 100%;
  }

  .product-row {
    flex-direction: column;
    align-items: stretch;
  }

  .product-autocomplete {
    min-width: 100%;
  }
}

/* Scrollbar personalizado */
.sales-list-scroll::-webkit-scrollbar {
  width: 6px;
}

.sales-list-scroll::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.sales-list-scroll::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.sales-list-scroll::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Estilos para selectores y autocomplete */
.compact-autocomplete {
  width: 100%;
}

.selected-info {
  display: block;
  font-size: 0.8rem;
  color: #28a745;
  margin-top: 5px;
  font-style: italic;
}

/* Ajustes de color para balances */
.balance-due {
  color: #e74c3c;
}

.balance-paid {
  color: #27ae60;
}

.exchange-rate-badge {
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  border: 1px solid var(--primary-color);
  display: inline-block;
  color: #fff;
}

.summary-row.highlight {
  color: var(--secondary-color);
  font-size: 1.1rem;
  border-top: 1px dashed rgba(255, 255, 255, 0.2);
  padding-top: 10px;
}

.credit-sale {
  border-left: 4px solid #f1c40f;
}

.paid-sale {
  border-left: 4px solid #2ecc71;
}

.void-sale {
  opacity: 0.6;
  text-decoration: line-through;
}

/* Estilos adicionales de tus archivos anteriores omitidos por brevedad pero implícitos */
</style>
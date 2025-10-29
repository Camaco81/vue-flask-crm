<template>
  <div class="sales-container">
    <h1 class="page-title">Gestión de Ventas</h1>
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
            placeholder="Buscar cliente por nombre o email..."
            labelKey="name"
            secondaryLabelKey="email"
            v-model="newSale.customer_id"
            id="customer"
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
              required>
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
            <p v-if="!isPaymentValid()" class="error-message">
                ⚠️ Monto pagado es insuficiente.
            </p>
        </div>

        <div class="form-group">
            <label for="payment-method">Forma de Pago:</label>
            <select id="payment-method" v-model="newSale.payment.method" @change="resetPaymentFields">
                <option value="USD">Dólar (Efectivo/Transferencia)</option>
                <option value="VES">Bolívares (Transferencia/Punto)</option>
                <option value="MIXED">Mixto (USD + Bolívares)</option>
            </select>
        </div>

        <div class="payment-fields-group">
            <div class="form-group" v-if="newSale.payment.method !== 'VES'">
                <label for="usd-paid">Monto Pagado en Dólares ($):</label>
                <input 
                    type="number" 
                    id="usd-paid" 
                    v-model.number="newSale.payment.usd_paid" 
                    min="0" 
                    step="0.01" 
                    :required="newSale.payment.method !== 'VES'">
            </div>

            <div class="form-group" v-if="newSale.payment.method !== 'USD'">
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
                    :required="newSale.payment.method !== 'USD'">
            </div>
        </div>
        <button 
          type="submit" 
          :disabled="creating || !newSale.customer_id || newSale.items.some(i => !i.product_id || i.quantity < 1 || i.quantity > getProductStock(i.product_id)) || !isPaymentValid()" 
          class="submit-btn"
        >
          {{ creating ? 'Registrando...' : 'Registrar Venta' }}
        </button>
      </form>
    </div>
    
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
              <span class="status-badge" :class="{'pending': sale.status === 'Pendiente', 'completed': sale.status === 'Completado'}">
                {{ sale.status }}
              </span>
            </p>
            <p v-if="sale.seller_email">Vendedor: {{ sale.seller_email }}</p>
            <p>Tasa Utilizada: **Bs. {{ sale.exchange_rate_used.toFixed(2) }}**</p> 
            <p class="payment-info">
              Pago: **{{ sale.payment_method || 'N/A' }}** (USD Pagado: ${{ sale.usd_paid.toFixed(2) }} / Bs Pagado: Bs. {{ sale.ves_paid.toFixed(2) }})
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

const STOCK_THRESHOLD = 10;
const PAYMENT_TOLERANCE = 0.02; // 2 centavos de tolerancia para la verificación de pago

export default {
  name: 'SalesComponent',
  components: {
    BackButton,
    AutocompleteSearch
  },
  data() {
    return {
      sales: [],
      customers: [],
      products: [],
      newSale: {
        customer_id: null, 
        items: [{ product_id: null, quantity: 1, price: 0 }],
        payment: {
            method: 'USD',
            usd_paid: 0,
            ves_paid: 0,
        }
      },
      loading: false,
      creating: false,
      localStockAlerts: [],
      bcvRate: 0, // 🚨 INICIALIZADO en 0, se llenará con la API
    };
  },
  async mounted() {
    await this.fetchData();
  },
  methods: {
    // 🚨 Función: Obtener la tasa de cambio actual (usando tu endpoint simulado)
    async fetchBcvRate() {
        try {
            // Nota: Se asume que /api/exchange-rate devuelve { rate: <number> }
            const response = await axios.get('/api/exchange-rate'); 
            this.bcvRate = parseFloat(response.data.rate);
            console.log(`Tasa BCV obtenida: Bs. ${this.bcvRate.toFixed(2)}`);
        } catch (error) {
            console.error("Error fetching BCV rate. Using default rate of 36.5.", error);
            // Usar una tasa de respaldo si el backend falla
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
          return {
            ...sale,
            customer_name: customer.name,
            customer_email: customer.email,  
            customer_address: customer.address,
            // 🚨 CORRECCIÓN: Mapear nuevos campos del backend
            total_usd: parseFloat(sale.total_usd), // total_amount_usd mapeado a total_usd
            total_amount_ves: parseFloat(sale.total_amount_ves), 
            exchange_rate_used: parseFloat(sale.exchange_rate_used || this.bcvRate), // Tasa usada
            usd_paid: parseFloat(sale.usd_paid || 0),
            ves_paid: parseFloat(sale.ves_paid || 0),
            payment_method: sale.payment_method || 'N/A',
            items: sale.items.map(item => ({
              ...item,
              price_usd: parseFloat(item.price_usd || item.price) // El backend devuelve price_usd en la consulta GET
            }))
          };
        });

        this.customers = customersResponse.data;
        this.products = productsResponse.data.map(p => ({
            ...p,
            stock: Number(p.stock),
            price: Number(p.price) // Precio unitario en USD
        }));
      } catch (error) {
        console.error("Error fetching data:", error);
        alert('Error al cargar ventas o clientes/productos. Verifique la consola.');
      } finally {
        this.loading = false;
      }
    },
    
    // Función: Calcula el total de la venta en USD
    calculateTotalAmountUSD() {
        return this.newSale.items.reduce((total, item) => {
            const product = this.products.find(p => p.id === item.product_id);
            const price = product ? Number(product.price) : 0; 
            const quantity = Number(item.quantity) || 0;
            return total + (price * quantity);
        }, 0);
    },

    // Función: Calcula la cantidad restante a pagar en VES (para pago mixto)
    calculateVesRequired() {
        const totalUSD = this.calculateTotalAmountUSD();
        const usdPaid = Number(this.newSale.payment.usd_paid) || 0;
        
        let remainingUSD = totalUSD - usdPaid;
        
        // Si ya pagó de más o completo en USD, no necesita VES
        if (remainingUSD <= PAYMENT_TOLERANCE) {
            return 0;
        }
        
        return remainingUSD * this.bcvRate;
    },

    // Función: Validar que el pago cubra el total de la venta
    isPaymentValid() {
        const totalUSD = this.calculateTotalAmountUSD();
        const usdPaid = Number(this.newSale.payment.usd_paid) || 0;
        const vesPaid = Number(this.newSale.payment.ves_paid) || 0;

        // Si la tasa BCV no se ha cargado, evitamos errores y asumimos temporalmente que es válida
        if (this.bcvRate === 0 && totalUSD > 0) return true; 

        // Equivalencia del pago en bolívares a USD
        const vesPaidInUSD = vesPaid / this.bcvRate;
        
        const totalPaidInUSD = usdPaid + vesPaidInUSD;

        // Verificar si el pago cubre el total (con tolerancia)
        return totalPaidInUSD >= totalUSD - PAYMENT_TOLERANCE;
    },

    // Función: Reinicia los campos de pago al cambiar el método
    resetPaymentFields() {
        this.newSale.payment.usd_paid = 0;
        this.newSale.payment.ves_paid = 0;

        const totalUSD = this.calculateTotalAmountUSD();
        
        // Lógica de autocompletado: Si no hay items, no hacemos nada
        if (totalUSD === 0) return;

        // Lógica de autocompletado para 'VES'
        if (this.newSale.payment.method === 'VES') {
            this.newSale.payment.ves_paid = totalUSD * this.bcvRate;
        }
        // Lógica de autocompletado para 'USD'
        else if (this.newSale.payment.method === 'USD') {
            this.newSale.payment.usd_paid = totalUSD;
        }
    },

    // ... (Métodos de Stock y Formularios: getProductStock, checkLocalStockAlert, updateLocalAlerts, addItem, removeItem, handleProductSelection)
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
      this.resetPaymentFields(); // Reajustar el pago al agregar/quitar items
    },

    removeItem(index) {
      if (this.newSale.items.length > 1) {
        this.newSale.items.splice(index, 1);
        this.updateLocalAlerts();
        this.resetPaymentFields(); // Reajustar el pago al agregar/quitar items
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
          this.resetPaymentFields(); // Reajustar el pago al cambiar de producto
        }
      } else {
        item.price = 0;
        this.updateLocalAlerts();
        this.resetPaymentFields(); // Reajustar el pago
      }
    },


    async createSale() {
      const validItems = this.newSale.items
          .filter(i => i.product_id && i.quantity > 0 && i.quantity <= this.getProductStock(i.product_id))
          .map(item => ({
              product_id: item.product_id,
              quantity: Number(item.quantity), 
              price: Number(item.price), 
          }));

      if (!this.isPaymentValid()) {
          alert('El monto pagado es insuficiente para cubrir el total de la venta.');
          return;
      }

      if (!this.newSale.customer_id || this.newSale.customer_id.trim() === "") {
          alert('Por favor, selecciona un cliente válido.');
          return;
      }
      if (validItems.length === 0) {
          alert('Por favor, añade al menos un producto válido con una cantidad positiva que no exceda el stock.');
          return;
      }

      this.creating = true;
      try {
          // 🚨 PREPARAR PAYLOAD con datos de pago y la tasa de cambio actual
          const salePayload = {
              customer_id: this.newSale.customer_id,
              items: validItems,
              // Nota: El backend llama a la BCV API internamente, pero es buena práctica enviarla como referencia 
              // si se quisiera usar una tasa manual, aunque aquí solo se envía la obtenida.
              // En este caso, el backend la ignorará y usará la que el mismo obtiene, pero la dejo para ser explícitos.
              // El backend se encarga de usar la tasa del sistema, no la del frontend.
              // bcv_rate: this.bcvRate, 
              payment: {
                  method: this.newSale.payment.method,
                  usd_paid: Number(this.newSale.payment.usd_paid),
                  ves_paid: Number(this.newSale.payment.ves_paid),
              }
          };
          
          const response = await axios.post('/api/sales', salePayload);
          const responseData = response.data;

          let successMessage = `Venta #${responseData.sale_id.substring(0, 8)}... registrada exitosamente!`;
          if (responseData.stock_alerts && responseData.stock_alerts.length > 0) {
              successMessage += "\n\n⚠️ **ATENCIÓN INVENTARIO:**\n" + responseData.stock_alerts.join('\n');
              console.warn("Stock Alerts from Backend:", responseData.stock_alerts);
          }

          alert(successMessage);
          
          // 3. **Reiniciar formulario**
          this.newSale = { 
            customer_id: null, 
            items: [{ product_id: null, quantity: 1, price: 0 }],
            payment: { method: 'USD', usd_paid: 0, ves_paid: 0 }
          };
          this.localStockAlerts = []; 
          await this.fetchData(); // Volver a cargar datos para ver el nuevo stock y las ventas
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
      }
    },

    // 🚨 Función: Generar Factura en Bolívares (VES)
   // 🚨 MODIFICADO Y CORREGIDO: Generar Factura en Bolívares (VES)
    generateInvoicePdf(sale) {
      // Usar los montos ya convertidos y la tasa registrada en la DB (sale.exchange_rate_used)
      const bcvRate = parseFloat(sale.exchange_rate_used); 
      const totalAmountUSD = parseFloat(sale.total_usd);
      const totalAmountVES = parseFloat(sale.total_amount_ves); 
      
      // Preparación de ítems con precio en VES
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
      let y = 10; // Posición Y inicial

      // === ENCABEZADO ===
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

      // === DETALLES DE FACTURA ===
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

      if (sale.seller_email) {
          y += 7;
          doc.text(`Vendedor: ${sale.seller_email}`, 10, y);
      }
      y += 10;

      // === DETALLES DEL CLIENTE ===
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

      // === TABLA DE PRODUCTOS (Encabezado) ===
      doc.setFontSize(10);
      doc.setFillColor(230, 230, 230);
      doc.rect(10, y, 190, 8, 'F');
      doc.setTextColor(0, 0, 0);
      doc.setFont(undefined, 'bold');
      
      // Encabezados de Columna
      doc.text("Producto", 12, y + 5); 
      doc.text("Cantidad", 70, y + 5, null, null, "right"); // Alineación a la derecha
      doc.text("P. Unitario USD", 105, y + 5, null, null, "right"); 
      doc.text("P. Unitario BS", 140, y + 5, null, null, "right"); 
      doc.text("TOTAL BS", 185, y + 5, null, null, "right"); 
      
      doc.setFont(undefined, 'normal');
      y += 8;

      // === TABLA DE PRODUCTOS (Filas) ===
      doc.setFontSize(10);
      doc.setTextColor(50, 50, 50);
      
      itemsWithVES.forEach(item => {
        // Filas de Producto
        doc.text(item.product_name.substring(0, 30), 12, y + 5);
        doc.text(String(item.quantity), 70, y + 5, null, null, "right"); // Alineación a la derecha
        doc.text(`$${item.price_usd.toFixed(2)}`, 105, y + 5, null, null, "right"); 
        doc.text(`Bs. ${item.price_ves.toFixed(2)}`, 140, y + 5, null, null, "right"); 
        doc.text(`Bs. ${item.total_ves.toFixed(2)}`, 185, y + 5, null, null, "right"); 
        y += 7;
        
        // Manejo de Salto de Página (mantenido)
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
      
      // === TOTALES Y PAGO ===

      // Línea divisoria de totales
      doc.setDrawColor(150, 150, 150);
      doc.setLineWidth(0.3);
      // Ajuste de coordenadas: La línea se dibuja de 120 a 200 para centrarse con los totales.
      doc.line(120, y, 200, y); 
      y += 5;

      // TOTAL A PAGAR (Bs)
      doc.setFontSize(14);
      doc.setFont(undefined, 'bold');
      // Ajuste de posición (X=120, alineado a la izquierda)
      doc.text("TOTAL A PAGAR (Bs):", 120, y); 
      // Ajuste de posición (X=185, alineado a la derecha)
      doc.text(`Bs. ${totalAmountVES.toFixed(2)}`, 185, y, null, null, "right"); 

      y += 7; // Más espacio
      
      // Total en USD como referencia
      doc.setFontSize(10);
      doc.setFont(undefined, 'normal');
      doc.text(`Total Referencial (USD): $${totalAmountUSD.toFixed(2)}`, 120, y);
      
      // Detalles de Pago
      y += 5;
      doc.text(`Método de Pago: ${sale.payment_method || 'N/A'}`, 120, y);
      y += 5;
      doc.text(`Pagado en USD: $${sale.usd_paid.toFixed(2)}`, 120, y);
      y += 5;
      doc.text(`Pagado en BS: Bs. ${sale.ves_paid.toFixed(2)}`, 120, y);

      // === PIE DE PÁGINA ===
      doc.setFontSize(8);
      doc.setTextColor(100, 100, 100);
      // Se mantiene 290 para asegurar que esté al fondo
      doc.text(`Generado el ${new Date().toLocaleDateString('es-ES')} a las ${new Date().toLocaleTimeString('es-ES')}`, 10, 290);
      doc.text("Gracias por su compra!", 105, 290, null, null, "center");

      doc.save(`Factura_Venta_${sale.id.substring(0, 8)}.pdf`);
    },
    
    // ... (rest of methods)
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
/* Estilos CSS */
.sales-container {
    padding: 2rem;
    font-family: 'Inter', sans-serif;
    background-color: #f0f4f8;
    min-height: 100vh;
}

.page-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #2d3748;
    margin-bottom: 2rem;
    border-bottom: 3px solid #667eea;
    padding-bottom: 0.5rem;
}

.card {
    background: white;
    border-radius: 1rem;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    margin-bottom: 2rem;
}

.create-sale-card h2 {
    color: #2d3748;
    margin-bottom: 1.5rem;
}

.form-group {
    margin-bottom: 1rem;
}

.product-item-group {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 1rem;
    align-items: end;
    margin-bottom: 1.5rem;
    padding: 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.75rem;
    background-color: #fafcff;
}

.product-item-group label {
    margin-bottom: 0.25rem;
}

.alert-box {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
}
.warning-alert {
    background-color: #fff3cd;
    border: 1px solid #ffc107;
    color: #856404;
}
.warning-alert ul {
    list-style: disc;
    padding-left: 20px;
    margin-top: 5px;
}
.warning-alert p {
    margin-bottom: 5px;
}

.error-message {
    color: #e53e3e;
    font-size: 0.85rem;
    margin-top: 5px;
    font-weight: 600;
}

/* Nuevo estilo para la línea divisoria */
.separator {
    margin: 2rem 0;
    border: 0;
    border-top: 1px dashed #e2e8f0;
}
.summary-box {
    padding: 1rem;
    background-color: #f7fcf9;
    border: 1px solid #c6f6d5;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}
.summary-box strong {
    font-weight: 700;
    color: #2f855a;
}
.payment-fields-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}
.payment-info {
    font-weight: 500;
    color: #2f855a; /* Color para destacar la información de pago */
    border-left: 3px solid #48bb78;
    padding-left: 10px;
}


select,
input[type="number"] {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    font-size: 1rem;
}

.add-item-btn,
.remove-btn,
.pdf-btn {
    background-color: #667eea;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    cursor: pointer;
    margin-top: 1rem;
    transition: background-color 0.3s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.add-item-btn:hover,
.remove-btn:hover,
.pdf-btn:hover {
    background-color: #5a67d8;
}

.remove-btn {
    background-color: #e53e3e;
    margin-left: 1rem;
    margin-top: 0;
}
.remove-btn:hover {
    background-color: #c53030;
}

.submit-btn {
    width: 100%;
    background-color: #48bb78;
    color: white;
    border: none;
    padding: 1rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 1.125rem;
    cursor: pointer;
    transition: background-color 0.3s;
    margin-top: 1.5rem;
}

.submit-btn:disabled {
    background-color: #a0aec0;
    cursor: not-allowed;
}

.sales-list-card {
    margin-top: 2rem;
}

.loading-state {
    text-align: center;
    font-size: 1.125rem;
    color: #718096;
}

.no-sales-state {
    text-align: center;
    font-size: 1.125rem;
    color: #718096;
    margin-top: 1rem;
}

.sales-list {
    list-style: none;
    padding: 0;
}

.sale-item {
    background-color: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
}

.sale-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 0.75rem;
    margin-bottom: 0.75rem;
}

.sale-header h3 {
    margin: 0;
    font-size: 1.25rem;
    color: #2d3748;
}

.sale-details p {
    margin: 0.5rem 0;
    color: #718096;
}

.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: capitalize;
}

.status-badge.pending {
    background-color: #fefcbf;
    color: #8b5b2e;
}

.status-badge.completed {
    background-color: #c6f6d5;
    color: #2f855a;
}

.sale-actions {
    margin-top: 1rem;
    text-align: right;
}

.pdf-btn {
    background-color: #e53e3e;
    margin-left: auto;
}
.pdf-btn:hover {
    background-color: #c53030;
}
</style>
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
        
        <button 
          type="submit" 
          :disabled="creating || !newSale.customer_id || newSale.items.some(i => !i.product_id || i.quantity < 1 || i.quantity > getProductStock(i.product_id))" 
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
            <h3>Venta #{{ sale.id.substring(0, 8) }}... a {{ sale.customer_name }}</h3> <span>Total: ${{ sale.total_amount.toFixed(2) }}</span>
          </div>
          <div class="sale-details">
            <p>Fecha: {{ formatDate(sale.sale_date) }}</p> <p>Estado: 
              <span class="status-badge" :class="{'pending': sale.status === 'Pendiente', 'completed': sale.status === 'Completado'}">
                {{ sale.status }}
              </span>
            </p>
            <p v-if="sale.seller_email">Vendedor: {{ sale.seller_email }}</p>
          </div>
          <div class="sale-items">
            <h4>Elementos de la venta:</h4>
            <ul>
              <li v-for="item in sale.items" :key="item.product_name">
                {{ item.quantity }} x {{ item.product_name }} (${{ item.price.toFixed(2) }})
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

// 🚨 NUEVA CONSTANTE LOCAL: Debe coincidir con la de tu backend (sale_routes.py)
const STOCK_THRESHOLD = 10; 

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
      },
      loading: false,
      creating: false,
      // 🚨 NUEVO: Alertas de stock generadas LOCALMENTE (antes del envío)
      localStockAlerts: [], 
    };
  },
  async mounted() {
    await this.fetchData();
  },
  methods: {
    async fetchData() {
      this.loading = true;
      try {
        // Se asegura de obtener los productos más recientes (con stock actualizado)
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
            total_amount: parseFloat(sale.total_amount),
            items: sale.items.map(item => ({
              ...item,
              price: parseFloat(item.price)
            }))
          };
        });

        this.customers = customersResponse.data;
        // 🚨 IMPORTANTE: Asegurarse que el stock sea un número para las validaciones
        this.products = productsResponse.data.map(p => ({
            ...p,
            stock: Number(p.stock) // Asegura que 'stock' es numérico
        }));
      } catch (error) {
        console.error("Error fetching data:", error);
        alert('Error al cargar ventas o clientes/productos. Verifique la consola.');
      } finally {
        this.loading = false;
      }
    },

    getProductStock(productId) {
      const product = this.products.find(p => p.id === productId);
      // Devuelve el stock si existe, o 0 para evitar errores si el producto no está seleccionado.
      return product ? product.stock : 0; 
    },
    
    // 🚨 NUEVA FUNCIÓN: Verifica el stock localmente (Requisito 2)
    checkLocalStockAlert(item) {
        const product = this.products.find(p => p.id === item.product_id);
        if (!product || item.quantity < 1) return;

        // Actualizar la alerta local
        this.updateLocalAlerts();

        // Si la cantidad es mayor que el stock, forzar al máximo stock
        if (item.quantity > product.stock) {
            item.quantity = product.stock;
        }
    },

    // 🚨 NUEVA FUNCIÓN: Genera las alertas de stock local
    updateLocalAlerts() {
        const alerts = [];
        // Filtra los ítems válidos para verificar el stock
        const validItems = this.newSale.items.filter(i => i.product_id && i.quantity > 0);

        for (const item of validItems) {
            const product = this.products.find(p => p.id === item.product_id);
            if (product) {
                const remaining_stock = product.stock - item.quantity;
                
                if (remaining_stock <= STOCK_THRESHOLD) {
                    let alert_msg;
                    if (remaining_stock < 0) {
                        // Esto no debería pasar debido al `max` en el input, pero como respaldo:
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
        // Almacena las alertas ÚNICAS
        this.localStockAlerts = [...new Set(alerts)];
    },

    addItem() {
      this.newSale.items.push({ product_id: null, quantity: 1, price: 0 });
      this.updateLocalAlerts();
    },

    removeItem(index) {
      if (this.newSale.items.length > 1) {
        this.newSale.items.splice(index, 1);
        this.updateLocalAlerts();
      }
    },

    handleProductSelection(item, productId) {
      item.product_id = productId;
      
      if (productId) {
        const selectedProduct = this.products.find(p => p.id === productId);
        if (selectedProduct) {
          item.price = selectedProduct.price;
          // Asegurar que la cantidad no exceda el stock si la selección cambia
          if (item.quantity > selectedProduct.stock) {
            item.quantity = selectedProduct.stock;
          }
          // Llamar a la validación después de seleccionar el producto
          this.checkLocalStockAlert(item);
        }
      } else {
        item.price = 0;
        // Si se deselecciona, limpia la alerta local
        this.updateLocalAlerts();
      }
    },

    async createSale() {
      // 1. **Filtrar ítems inválidos y sanear los datos**
      const validItems = this.newSale.items
          .filter(i => i.product_id && i.quantity > 0 && i.quantity <= this.getProductStock(i.product_id))
          .map(item => ({
              product_id: item.product_id,
              quantity: Number(item.quantity), 
              price: Number(item.price), 
          }));

      // 2. **Re-validación final antes del envío**
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
          const salePayload = {
              customer_id: this.newSale.customer_id,
              items: validItems
          };
          
          const response = await axios.post('/api/sales', salePayload);
          const responseData = response.data;

          // 🚨 Manejar Alertas de Stock del Backend
          let successMessage = 'Venta registrada exitosamente!';
          if (responseData.stock_alerts && responseData.stock_alerts.length > 0) {
              successMessage += "\n\n⚠️ **ATENCIÓN INVENTARIO:**\n" + responseData.stock_alerts.join('\n');
              // Usar 'console.warn' para mejor visibilidad en desarrollo
              console.warn("Stock Alerts from Backend:", responseData.stock_alerts);
          }

          alert(successMessage);
          
          // 3. **Reiniciar formulario**
          this.newSale = { customer_id: null, items: [{ product_id: null, quantity: 1, price: 0 }] };
          this.localStockAlerts = []; // Limpiar alertas locales
          await this.fetchData(); // Volver a cargar datos para ver el nuevo stock
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

    generateInvoicePdf(sale) {
      // ... (Lógica de jsPDF sin cambios)
      const doc = new jsPDF();
      let y = 10; 

      doc.setFontSize(18);
      doc.text("Factura de Venta", 105, y, null, null, "center");
      y += 10;
      doc.setFontSize(10);
      doc.text("Empresa XYZ S.A.", 105, y, null, null, "center");
      y += 5;
      doc.text("Av. Principal #123, Ciudad", 105, y, null, null, "center");
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
      doc.text(`Estado: ${sale.status}`, 10, y);
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
      doc.text("Producto", 15, y + 5);
      doc.text("Cantidad", 85, y + 5);
      doc.text("Precio Unitario", 120, y + 5);
      doc.text("Total", 170, y + 5);
      doc.setFont(undefined, 'normal');
      y += 8;

      doc.setFontSize(10);
      doc.setTextColor(50, 50, 50);
      sale.items.forEach(item => {
        const itemTotal = item.quantity * item.price;
        doc.text(item.product_name.substring(0, 40), 15, y + 5);
        doc.text(String(item.quantity), 90, y + 5, null, null, "right");
        doc.text(`$${item.price.toFixed(2)}`, 140, y + 5, null, null, "right");
        doc.text(`$${itemTotal.toFixed(2)}`, 185, y + 5, null, null, "right");
        y += 7;
        if (y > 270) {
          doc.addPage();
          y = 10;
          doc.setFontSize(10);
          doc.setFillColor(230, 230, 230);
          doc.rect(10, y, 190, 8, 'F');
          doc.setTextColor(0, 0, 0);
          doc.setFont(undefined, 'bold');
          doc.text("Producto", 15, y + 5);
          doc.text("Cantidad", 85, y + 5);
          doc.text("Precio Unitario", 120, y + 5);
          doc.text("Total", 170, y + 5);
          doc.setFont(undefined, 'normal');
          y += 8;
        }
      });

      y += 10;

      doc.setDrawColor(150, 150, 150);
      doc.setLineWidth(0.3);
      doc.line(140, y, 200, y);
      y += 5;
      doc.setFontSize(14);
      doc.setFont(undefined, 'bold');
      doc.text("TOTAL:", 140, y);
      doc.text(`$${sale.total_amount.toFixed(2)}`, 185, y, null, null, "right");

      doc.setFontSize(8);
      doc.setTextColor(100, 100, 100);
      doc.text(`Generado el ${new Date().toLocaleDateString('es-ES')} a las ${new Date().toLocaleTimeString('es-ES')}`, 10, 290);
      doc.text("Gracias por su compra!", 105, 290, null, null, "center");

      doc.save(`Factura_Venta_${sale.id}.pdf`);
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
/* Estilos CSS (Se añadieron estilos para la alerta y la validación local) */
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

/* Estilos para la Alerta de Stock */
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

/* Estilo para mensaje de error local */
.error-message {
    color: #e53e3e;
    font-size: 0.85rem;
    margin-top: 5px;
    font-weight: 600;
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
<template>
  <div class="orders-container">
    <h1 class="page-title">Gestión de Pedidos</h1>
    <div class="card create-order-card">
      <h2>Crear Nuevo Pedido</h2>
      <form @submit.prevent="createOrder">
        <div class="form-group">
          <label for="customer">Seleccionar Cliente:</label>
          <select id="customer" v-model="newOrder.customer_id" required>
            <option disabled value="">Selecciona un cliente</option>
            <option v-for="customer in customers" :key="customer.id" :value="customer.id">
              {{ customer.name }}
            </option>
          </select>
        </div>
        
        <h3>Productos</h3>
        <div class="form-group" v-for="(item, index) in newOrder.items" :key="index">
          <label :for="'product-' + index">Producto:</label>
          <select :id="'product-' + index" v-model="item.product_id" required>
            <option disabled value="">Selecciona un producto</option>
            <option v-for="product in products" :key="product.id" :value="product.id">
              {{ product.name }} (${{ product.price }})
            </option>
          </select>
          <label :for="'quantity-' + index">Cantidad:</label>
          <input type="number" :id="'quantity-' + index" v-model.number="item.quantity" min="1" required>
          <button type="button" @click="removeItem(index)" class="remove-btn">Quitar</button>
        </div>
        <button type="button" @click="addItem" class="add-item-btn">Agregar Producto</button>
        
        <button type="submit" :disabled="creating" class="submit-btn">
          {{ creating ? 'Creando...' : 'Crear Pedido' }}
        </button>
      </form>
    </div>

    <div class="card orders-list-card">
      <h2>Pedidos Registrados</h2>
      <div v-if="loading" class="loading-state">Cargando pedidos...</div>
      <div v-if="orders.length === 0 && !loading">No hay pedidos registrados aún.</div>
      <ul v-else class="orders-list">
        <li v-for="order in orders" :key="order.id" class="order-item">
          <div class="order-header">
            <h3>Pedido de {{ order.customer_name }}</h3>
            <span>Total: ${{ order.total_amount.toFixed(2) }}</span>
          </div>
          <div class="order-details">
            <p>Fecha: {{ formatDate(order.order_date) }}</p>
            <p>Estado: 
              <span class="status-badge" :class="{'pending': order.status === 'Pendiente', 'completed': order.status === 'Completado'}">
                {{ order.status }}
              </span>
            </p>
          </div>
          <div class="order-items">
            <h4>Elementos del pedido:</h4>
            <ul>
              <li v-for="item in order.items" :key="item.product_name">
                {{ item.quantity }} x {{ item.product_name }} (${{ item.price.toFixed(2) }})
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import apiClient from '../axios';

export default {
  name: 'OrdersComponent',
  data() {
    return {
      orders: [],
      customers: [],
      products: [],
      newOrder: {
        customer_id: '',
        items: [{ product_id: '', quantity: 1 }],
      },
      loading: false,
      creating: false,
    };
  },
  async mounted() {
    await this.fetchData();
  },
  methods: {
    async fetchData() {
      this.loading = true;
      try {
        const [ordersResponse, customersResponse, productsResponse] = await Promise.all([
          apiClient.get('/api/orders'),
          apiClient.get('/api/customers'),
          apiClient.get('/api/products')
        ]);

        // Fix: Parse total_amount to a number before assigning to orders
        this.orders = ordersResponse.data.map(order => ({
          ...order,
          total_amount: parseFloat(order.total_amount)
        }));

        this.customers = customersResponse.data;
        this.products = productsResponse.data;
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        this.loading = false;
      }
    },
    addItem() {
      this.newOrder.items.push({ product_id: '', quantity: 1 });
    },
    removeItem(index) {
      if (this.newOrder.items.length > 1) {
        this.newOrder.items.splice(index, 1);
      }
    },
    async createOrder() {
      this.creating = true;
      try {
        await apiClient.post('/api/orders', this.newOrder);
        alert('Pedido creado exitosamente!');
        // Reiniciar el formulario
        this.newOrder = { customer_id: '', items: [{ product_id: '', quantity: 1 }] };
        await this.fetchData(); // Volver a cargar la lista de pedidos
      } catch (error) {
        console.error('Error al crear pedido:', error);
        alert('Error al crear el pedido. Por favor, inténtalo de nuevo.');
      } finally {
        this.creating = false;
      }
    },
    formatDate(date) {
      return new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(date));
    }
  },
};
</script>

<style scoped>
.orders-container {
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

.create-order-card h2 {
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #4a5568;
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
.remove-btn {
  background-color: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  margin-top: 1rem;
  transition: background-color 0.3s;
}

.remove-btn {
  background-color: #e53e3e;
  margin-left: 1rem;
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

.orders-list-card {
  margin-top: 2rem;
}

.loading-state {
  text-align: center;
  font-size: 1.125rem;
  color: #718096;
}

.orders-list {
  list-style: none;
  padding: 0;
}

.order-item {
  background-color: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.75rem;
  margin-bottom: 0.75rem;
}

.order-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2d3748;
}

.order-details p {
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
</style>
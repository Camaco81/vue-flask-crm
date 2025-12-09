<template>
  <div class="almacenista-container">
    <!-- Header con navegación -->
    <header class="almacenista-header">
      <div class="header-content">
        <div class="user-info">
          <h1>👋 Bienvenido, Almacenista</h1>
          <p class="user-role">Tu función es mantener el inventario al día.</p>
        </div>
        <div class="header-actions">
          <NotificationBell class="notification-bell" />
          <button @click="logout" class="logout-btn">
            <i class="fas fa-sign-out-alt"></i>
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </div>
    </header>

    <!-- Contenido principal -->
    <main class="almacenista-main">
      <!-- Sección de estadísticas rápidas -->
      <div class="stats-section">
        
        
        <div class="stat-card warning">
          <div class="stat-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <div class="stat-info">
            <h3>{{ lowStockCount }}</h3>
            <p>Stock Bajo </p>
          </div>
        </div>
      </div>

      <!-- Gestión de productos -->
      <div class="management-section">
        <div class="section-header">
          <h2><i class="fas fa-box-open"></i> Gestión de Productos</h2>
          <p>Administra tu inventario desde aquí</p>
        </div>

        <!-- Formulario para agregar producto -->
        <div class="add-product-card">
          <h3><i class="fas fa-plus-circle"></i> Agregar Nuevo Producto</h3>
          
          <form @submit.prevent="addProduct" class="product-form">
            <div class="form-row">
              <div class="form-group">
                <label for="product-name">
                  <i class="fas fa-tag"></i> Nombre del Producto *
                </label>
                <input
                  id="product-name"
                  type="text"
                  v-model="newProduct.name"
                  placeholder="Ej: Harina cali"
                  required
                  class="form-input"
                />
              </div>
              
              <div class="form-group">
                <label for="product-price">
                  <i class="fas fa-dollar-sign"></i> Precio *
                </label>
                <input
                  id="product-price"
                  type="number"
                  v-model.number="newProduct.price"
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                  required
                  class="form-input"
                />
              </div>
              
              <div class="form-group">
                <label for="product-stock">
                  <i class="fas fa-warehouse"></i> Stock Inicial *
                </label>
                <input
                  id="product-stock"
                  type="number"
                  v-model.number="newProduct.stock"
                  placeholder="Cantidad"
                  min="0"
                  required
                  class="form-input"
                />
              </div>
              
              <div class="form-actions">
                <button type="button" @click="resetForm" class="btn btn-secondary">
                  <i class="fas fa-undo"></i> Limpiar
                </button>
                <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
                  <i v-if="!isSubmitting" class="fas fa-plus"></i>
                  <span v-if="isSubmitting">Agregando...</span>
                  <span v-else>Agregar Producto</span>
                </button>
              </div>
            </div>
          </form>

          <!-- Alertas de formulario -->
          <div v-if="addError" class="alert alert-error">
            <i class="fas fa-exclamation-circle"></i>
            {{ addError }}
          </div>
          
          <div v-if="addSuccess" class="alert alert-success">
            <i class="fas fa-check-circle"></i>
            {{ addSuccess }}
          </div>
        </div>

        <!-- Lista de productos -->
        <div class="products-list-card">
          <div class="list-header">
            <h3><i class="fas fa-list"></i> Lista de Productos</h3>
            <div class="list-controls">
              <div class="search-box">
                <i class="fas fa-search"></i>
                <input
                  type="text"
                  v-model="searchTerm"
                  placeholder="Buscar productos..."
                  class="search-input"
                />
                <button v-if="searchTerm" @click="searchTerm = ''" class="clear-btn">
                  <i class="fas fa-times"></i>
                </button>
              </div>
              <button @click="fetchProducts" class="btn btn-refresh" :disabled="loading">
                <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
                {{ loading ? 'Cargando...' : 'Actualizar' }}
              </button>
            </div>
          </div>

          <!-- Estados de carga -->
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>Cargando productos...</p>
          </div>
          
          <div v-else-if="error" class="error-state">
            <i class="fas fa-exclamation-triangle"></i>
            <p>{{ error }}</p>
            <button @click="fetchProducts" class="btn btn-primary">
              Reintentar
            </button>
          </div>
          
          <div v-else-if="products.length === 0" class="empty-state">
            <i class="fas fa-boxes"></i>
            <p>No hay productos registrados</p>
            <p class="sub-text">Comienza agregando tu primer producto</p>
          </div>
          
          <!-- Tabla de productos -->
          <div v-else class="products-table">
            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Precio</th>
                  <th>Stock</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="product in filteredProducts" :key="product.id">
                  <td class="product-name">
                    <i class="fas fa-box"></i>
                    {{ product.name }}
                  </td>
                  <td class="product-price">
                    ${{ parseFloat(product.price).toFixed(2) }}
                  </td>
                  <td class="product-stock" :class="{ 'low-stock': product.stock < 10 }">
                    {{ product.stock }}
                    <span v-if="product.stock < 10" class="stock-warning">
                      <i class="fas fa-exclamation-circle"></i>
                    </span>
                  </td>
                  <td class="product-actions">
                    <button @click="openEditModal(product)" class="btn-icon btn-edit" title="Editar">
                      <i class="fas fa-edit"></i>
                    </button>
                    <button @click="confirmDelete(product)" class="btn-icon btn-delete" title="Eliminar">
                      <i class="fas fa-trash"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            
            <!-- Paginación -->
            <div v-if="filteredProducts.length > itemsPerPage" class="pagination">
              <button 
                @click="prevPage" 
                :disabled="currentPage === 1" 
                class="page-btn"
              >
                <i class="fas fa-chevron-left"></i>
              </button>
              
              <span class="page-info">
                Página {{ currentPage }} de {{ totalPages }}
              </span>
              
              <button 
                @click="nextPage" 
                :disabled="currentPage === totalPages" 
                class="page-btn"
              >
                <i class="fas fa-chevron-right"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal de edición -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3><i class="fas fa-edit"></i> Editar Producto</h3>
          <button @click="closeEditModal" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <form @submit.prevent="updateProduct" class="modal-form">
          <div class="form-group">
            <label>Nombre del Producto</label>
            <input 
              type="text" 
              v-model="editingProduct.name" 
              required 
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label>Precio</label>
            <input 
              type="number" 
              v-model.number="editingProduct.price" 
              required 
              min="0" 
              step="0.01" 
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label>Stock</label>
            <input 
              type="number" 
              v-model.number="editingProduct.stock" 
              required 
              min="0" 
              class="form-input"
            />
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="closeEditModal" class="btn btn-secondary">
              Cancelar
            </button>
            <button type="submit" class="btn btn-primary" :disabled="isUpdating">
              <span v-if="isUpdating">Actualizando...</span>
              <span v-else>Guardar Cambios</span>
            </button>
          </div>
        </form>
        
        <div v-if="editError" class="alert alert-error">
          {{ editError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import NotificationBell from './NotificationBell.vue';
import apiClient from '../../axios';

export default {
  name: 'AlmacenistaDashboard',
  components: {
    NotificationBell
  },
  data() {
    return {
      products: [],
      newProduct: {
        name: '',
        price: 0.00,
        stock: 0
      },
      loading: false,
      error: null,
      addError: null,
      addSuccess: null,
      isSubmitting: false,
      searchTerm: '',
      currentPage: 1,
      itemsPerPage: 8,
      showEditModal: false,
      editingProduct: null,
      editError: null,
      isUpdating: false
    };
  },
  computed: {
    filteredProducts() {
      if (!this.searchTerm) return this.products;
      const term = this.searchTerm.toLowerCase();
      return this.products.filter(product => 
        product.name.toLowerCase().includes(term)
      );
    },
    totalPages() {
      return Math.ceil(this.filteredProducts.length / this.itemsPerPage);
    },
    lowStockCount() {
      return this.products.filter(product => product.stock < 10).length;
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info'); 
      this.$router.push('/login');
    },

    async addProduct() {
      this.addError = null;
      this.addSuccess = null;
      this.isSubmitting = true;

      // Validaciones
      if (!this.newProduct.name.trim()) {
        this.addError = "El nombre del producto es requerido";
        this.isSubmitting = false;
        return;
      }

      if (this.newProduct.price <= 0) {
        this.addError = "El precio debe ser mayor a 0";
        this.isSubmitting = false;
        return;
      }

      if (this.newProduct.stock < 0) {
        this.addError = "El stock no puede ser negativo";
        this.isSubmitting = false;
        return;
      }

      const productToSend = {
        name: this.newProduct.name.trim(),
        price: parseFloat(this.newProduct.price).toFixed(2),
        stock: parseInt(this.newProduct.stock)
      };

      try {
        const { data } = await apiClient.post('/api/products', productToSend);
        
        this.addSuccess = `Producto "${data.name}" agregado exitosamente`;
        this.products.unshift({
          ...data,
          price: parseFloat(data.price),
          stock: parseInt(data.stock)
        });
        
        this.resetForm();
        
        setTimeout(() => {
          this.addSuccess = null;
        }, 3000);
      } catch (error) {
        this.addError = error.response?.data?.msg || 'Error al agregar el producto';
        console.error("Error:", error);
      } finally {
        this.isSubmitting = false;
      }
    },

    async fetchProducts() {
      this.loading = true;
      this.error = null;

      try {
        const { data } = await apiClient.get('/api/products');
        this.products = data.map(p => ({
          ...p,
          price: parseFloat(p.price),
          stock: parseInt(p.stock)
        }));
      } catch (error) {
        this.error = 'Error al cargar los productos';
        console.error("Error:", error);
      } finally {
        this.loading = false;
      }
    },

    resetForm() {
      this.newProduct = { name: '', price: 0.00, stock: 0 };
      this.addError = null;
    },

    openEditModal(product) {
      this.editingProduct = { ...product };
      this.showEditModal = true;
      this.editError = null;
    },

    closeEditModal() {
      this.showEditModal = false;
      this.editingProduct = null;
      this.editError = null;
    },

    async updateProduct() {
      this.isUpdating = true;
      this.editError = null;

      try {
        const productId = this.editingProduct.id;
        const productUpdate = {
          name: this.editingProduct.name.trim(),
          price: parseFloat(this.editingProduct.price).toFixed(2),
          stock: parseInt(this.editingProduct.stock)
        };

        const { data } = await apiClient.put(`/api/products/${productId}`, productUpdate);
        
        const index = this.products.findIndex(p => p.id === data.id);
        if (index !== -1) {
          this.products.splice(index, 1, {
            ...data,
            price: parseFloat(data.price),
            stock: parseInt(data.stock)
          });
        }
        
        this.closeEditModal();
        alert(`Producto "${data.name}" actualizado exitosamente`);
      } catch (error) {
        this.editError = error.response?.data?.msg || 'Error al actualizar el producto';
        console.error("Error:", error);
      } finally {
        this.isUpdating = false;
      }
    },

    async confirmDelete(product) {
      if (confirm(`¿Eliminar producto "${product.name}"?`)) {
        try {
          await apiClient.delete(`/api/products/${product.id}`);
          this.products = this.products.filter(p => p.id !== product.id);
        } catch (error) {
          alert('Error al eliminar el producto');
          console.error("Error:", error);
        }
      }
    },

    prevPage() {
      if (this.currentPage > 1) this.currentPage--;
    },

    nextPage() {
      if (this.currentPage < this.totalPages) this.currentPage++;
    }
  },
  mounted() {
    this.fetchProducts();
  }
};
</script>

<style scoped>
.almacenista-container {
  min-height: 100vh;
  background-color: #f8fafc;
}

/* Header */
.almacenista-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.user-role {
  margin: 0.25rem 0 0;
  opacity: 0.9;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.notification-bell {
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Main content */
.almacenista-main {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
}

/* Stats section */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 1rem;
  border-left: 4px solid #667eea;
}

.stat-card.warning {
  border-left-color: #e53e3e;
}

.stat-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.25rem;
}

.stat-card.warning .stat-icon {
  background: linear-gradient(135deg, #e53e3e, #f56565);
}

.stat-info h3 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d3748;
}

.stat-info p {
  margin: 0.25rem 0 0;
  color: #718096;
  font-size: 0.9rem;
}

/* Management section */
.section-header {
  margin-bottom: 2rem;
}

.section-header h2 {
  margin: 0;
  color: #2d3748;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-header p {
  margin: 0.5rem 0 0;
  color: #718096;
}

/* Cards */
.add-product-card,
.products-list-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.add-product-card h3,
.list-header h3 {
  margin: 0 0 1rem;
  color: #2d3748;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Form styles */
.product-form {
  margin-top: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr auto;
  gap: 1rem;
  align-items: end;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  color: #4a5568;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-actions {
  display: flex;
  gap: 0.5rem;
}

/* Buttons */
.btn {
  padding: 0.625rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a67d8;
}

.btn-secondary {
  background: #edf2f7;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-refresh {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  color: #4a5568;
}

.btn-refresh:hover:not(:disabled) {
  background: #edf2f7;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-edit {
  background: #e6fffa;
  color: #319795;
}

.btn-edit:hover {
  background: #b2f5ea;
}

.btn-delete {
  background: #fed7d7;
  color: #e53e3e;
}

.btn-delete:hover {
  background: #feb2b2;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Alerts */
.alert {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-top: 1rem;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.alert-error {
  background: #fed7d7;
  color: #c53030;
  border: 1px solid #fc8181;
}

.alert-success {
  background: #c6f6d5;
  color: #22543d;
  border: 1px solid #9ae6b4;
}

/* List controls */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.list-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-box i {
  position: absolute;
  left: 0.75rem;
  color: #a0aec0;
}

.search-input {
  padding: 0.5rem 2rem 0.5rem 2.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  width: 250px;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.clear-btn {
  position: absolute;
  right: 0.5rem;
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  padding: 0.25rem;
}

/* States */
.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state i,
.empty-state i {
  font-size: 2rem;
  color: #a0aec0;
  margin-bottom: 1rem;
}

.empty-state .sub-text {
  color: #a0aec0;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

/* Products table */
.products-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f7fafc;
}

th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #4a5568;
  border-bottom: 1px solid #e2e8f0;
}

td {
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.product-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.product-price {
  font-weight: 600;
  color: #2d3748;
}

.product-stock {
  font-weight: 600;
}

.product-stock.low-stock {
  color: #e53e3e;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stock-warning {
  color: #e53e3e;
}

.product-actions {
  display: flex;
  gap: 0.5rem;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.page-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #718096;
  font-size: 0.875rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 10px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #a0aec0;
  cursor: pointer;
  padding: 0.25rem;
}

.modal-form {
  padding: 1.5rem;
}

.modal-form .form-group {
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

/* Responsive */
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .list-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .list-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input {
    width: 100%;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
    flex-direction: row-reverse ;
  }
}

@media (max-width: 480px) {
  .almacenista-header {
    padding: 1rem;
  }
  
  .stats-section {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    margin: 1rem;
  }
  
  .modal-actions {
    flex-direction: column;
  }
}
</style>
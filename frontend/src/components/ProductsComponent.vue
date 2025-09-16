<template>
  <div class="products-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-info">
          <div class="header-icon">
            <i class="fas fa-boxes"></i>
          </div>
          <div class="header-text">
            <h1 class="page-title">Gestión de Productos</h1>
            <p class="page-subtitle">Administra tu inventario de productos</p>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-number">{{ products ? products.length : 0 }}</span>
            <span class="stat-label">Productos</span>
          </div>
        </div>
      </div>
    </div>

    <div class="content-wrapper">
      <div class="form-card">
        <div class="card-header">
          <div class="card-icon">
            <i class="fas fa-box-open"></i>
          </div>
          <div class="card-title">
            <h3>Registrar Nuevo Producto</h3>
            <p>Agrega un nuevo producto a tu inventario</p>
          </div>
        </div>
        
        <form @submit.prevent="addProduct" class="product-form">
          <div class="form-grid">
            <div class="form-group">
              <label for="product-name">
                <i class="fas fa-tag"></i>
                <span>Nombre del Producto *</span>
              </label>
              <input 
                id="product-name"
                type="text" 
                v-model="newProduct.name" 
                placeholder="Ingresa el nombre del producto"
                required 
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label for="product-price">
                <i class="fas fa-dollar-sign"></i>
                <span>Precio *</span>
              </label>
              <input 
                id="product-price"
                type="number" 
                v-model.number="newProduct.price" 
                placeholder="0.00"
                required 
                class="form-input"
              />
            </div>
          </div>

          <div class="form-actions">
            <button type="button" @click="resetForm" class="reset-btn">
              <i class="fas fa-undo"></i>
              <span>Limpiar</span>
            </button>
            <button type="submit" class="submit-btn" :disabled="isSubmitting">
              <div v-if="isSubmitting" class="button-spinner"></div>
              <i v-else class="fas fa-plus"></i>
              <span>{{ isSubmitting ? 'Agregando...' : 'Agregar Producto' }}</span>
            </button>
          </div>
        </form>

        <transition name="slide-down">
          <div v-if="addError" class="alert alert-error">
            <div class="alert-icon">
              <i class="fas fa-exclamation-circle"></i>
            </div>
            <div class="alert-content">
              <strong>Error:</strong> {{ addError }}
            </div>
            <button @click="addError = null" class="alert-close">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </transition>

        <transition name="slide-down">
          <div v-if="addSuccess" class="alert alert-success">
            <div class="alert-icon">
              <i class="fas fa-check-circle"></i>
            </div>
            <div class="alert-content">
              <strong>¡Éxito!</strong> {{ addSuccess }}
            </div>
            <button @click="addSuccess = null" class="alert-close">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </transition>
      </div>

      <div class="list-card">
        <div class="card-header">
          <div class="card-icon">
            <i class="fas fa-cubes"></i>
          </div>
          <div class="card-title">
            <h3>Lista de Productos</h3>
            <p>Visualiza y gestiona tu inventario de productos</p>
          </div>
          <div class="card-actions">
            <button @click="fetchProducts" class="refresh-btn" :disabled="loading">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
              <span>{{ loading ? 'Cargando...' : 'Actualizar' }}</span>
            </button>
          </div>
        </div>

        <div class="search-section">
          <div class="search-bar">
            <div class="search-icon">
              <i class="fas fa-search"></i>
            </div>
            <input 
              type="text" 
              v-model="searchTerm" 
              placeholder="Buscar productos por nombre..."
              class="search-input"
            />
            <button v-if="searchTerm" @click="searchTerm = ''" class="clear-search">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div v-if="loading && products.length === 0" class="loading-state">
          <div class="loading-spinner">
            <div class="spinner"></div>
          </div>
          <p class="loading-text">Cargando productos...</p>
        </div>

        <div v-if="error && !loading" class="error-state">
          <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <div class="error-content">
            <h3>Error al cargar productos</h3>
            <p>{{ error }}</p>
            <button @click="fetchProducts" class="retry-btn">
              <i class="fas fa-redo-alt"></i>
              Reintentar
            </button>
          </div>
        </div>

        <div v-if="!loading && !error && products.length === 0" class="empty-state">
          <div class="empty-icon">
            <i class="fas fa-boxes"></i>
          </div>
          <div class="empty-content">
            <h3>No hay productos registrados</h3>
            <p>Comienza agregando tu primer producto usando el formulario de arriba</p>
          </div>
        </div>

        <div v-if="!loading && !error && filteredProducts.length > 0" class="products-grid">
          <transition-group name="product-item" tag="div" class="grid-container">
            <div 
              v-for="product in paginatedProducts" 
              :key="product.id" 
              class="product-card"
            >
              <div class="product-avatar">
                <i class="fas fa-box"></i>
              </div>
              <div class="product-info">
                <h4 class="product-name">{{ product.name }}</h4>
                <p class="product-price">
                  <i class="fas fa-dollar-sign"></i>
                  {{ product.price }}
                </p>
              </div>
              <div class="product-actions">
                <button 
                  class="action-btn edit-btn" 
                  title="Editar" 
                  @click="openEditModal(product)"
                >
                  <i class="fas fa-edit"></i>
                </button>
                <button 
                  class="action-btn delete-btn" 
                  title="Eliminar" 
                  @click="confirmDelete(product)"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </transition-group>
        </div>

        <div v-if="totalPages > 1" class="pagination">
          <button 
            @click="currentPage--" 
            :disabled="currentPage === 1"
            class="page-btn"
          >
            <i class="fas fa-chevron-left"></i>
          </button>
          
          <div class="page-numbers">
            <button 
              v-for="page in visiblePages" 
              :key="page"
              @click="currentPage = page"
              :class="['page-number', { active: currentPage === page }]"
            >
              {{ page }}
            </button>
          </div>

          <button 
            @click="currentPage++" 
            :disabled="currentPage === totalPages"
            class="page-btn"
          >
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>

        <div v-if="filteredProducts.length > 0" class="results-info">
          <span>
            Mostrando {{ ((currentPage - 1) * itemsPerPage) + 1 }} - 
            {{ Math.min(currentPage * itemsPerPage, filteredProducts.length) }} 
            de {{ filteredProducts.length }} productos
          </span>
        </div>
      </div>
    </div>

    <transition name="fade">
      <div v-if="showEditModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>Editar Producto</h3>
            <button class="close-btn" @click="closeEditModal">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <form @submit.prevent="updateProduct" class="modal-form">
            <div class="form-group">
              <label for="edit-name">Nombre del Producto</label>
              <input type="text" id="edit-name" v-model="editingProduct.name" required class="form-input" />
            </div>
            <div class="form-group">
              <label for="edit-price">Precio</label>
              <input type="number" id="edit-price" v-model.number="editingProduct.price" required class="form-input" />
            </div>
            <div class="form-actions">
              <button type="button" class="cancel-btn" @click="closeEditModal">Cancelar</button>
              <button type="submit" class="submit-btn" :disabled="isUpdating">
                <div v-if="isUpdating" class="button-spinner"></div>
                <i v-else class="fas fa-save"></i>
                <span>{{ isUpdating ? 'Actualizando...' : 'Guardar Cambios' }}</span>
              </button>
            </div>
          </form>
          <transition name="slide-down">
            <div v-if="editError" class="alert alert-error">{{ editError }}</div>
          </transition>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import apiClient from '../axios';

export default {
  name: 'ProductsManagement',
  data() {
    return {
      products: [],
      newProduct: {
        name: '',
        price: 0
      },
      loading: false,
      error: null,
      addError: null,
      addSuccess: null,
      isSubmitting: false,
      searchTerm: '',
      currentPage: 1,
      itemsPerPage: 6,
      // Nuevas propiedades para la edición
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
    
    paginatedProducts() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.filteredProducts.slice(start, end);
    },
    
    visiblePages() {
      const pages = [];
      const maxVisible = 5;
      let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
      let end = Math.min(this.totalPages, start + maxVisible - 1);
      
      if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1);
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      
      return pages;
    }
  },
  watch: {
    searchTerm() {
      this.currentPage = 1;
    }
  },
  methods: {
    async addProduct() {
      this.addError = null;
      this.addSuccess = null;
      this.isSubmitting = true;

      if (!this.newProduct.name.trim() || !this.newProduct.price) {
        this.addError = "El nombre y el precio del producto son campos obligatorios.";
        this.isSubmitting = false;
        return;
      }

      try {
        const { data } = await apiClient.post('/api/products', {
          ...this.newProduct,
          name: this.newProduct.name.trim()
        });
        
        this.addSuccess = 'Producto registrado exitosamente.';
        this.products.unshift(data);
        this.resetForm();

        setTimeout(() => {
          this.addSuccess = null;
        }, 5000);
      } catch (error) {
        if (error.response?.data?.msg) {
          this.addError = error.response.data.msg;
        } else {
          this.addError = 'Error al registrar el producto. Por favor, inténtalo de nuevo.';
        }
        console.error("Error al agregar producto:", error);
      } finally {
        this.isSubmitting = false;
      }
    },
    
    async fetchProducts() {
      this.loading = true;
      this.error = null;
      
      try {
        const { data } = await apiClient.get('/api/products');
        this.products = data;
      } catch (error) {
        this.error = 'Error al cargar los productos. Por favor, inténtalo de nuevo.';
        console.error("Error al cargar productos:", error);
      } finally {
        this.loading = false;
      }
    },
    
    resetForm() {
      this.newProduct = {
        name: '',
        price: 0
      };
      this.addError = null;
      this.addSuccess = null;
    },

    // --- Métodos de Edición ---
    openEditModal(product) {
      this.editingProduct = { ...product };
      this.showEditModal = true;
      this.editError = null;
    },

    closeEditModal() {
      this.showEditModal = false;
      this.editingProduct = null;
    },

    async updateProduct() {
      this.isUpdating = true;
      this.editError = null;
      try {
          // En el método updateProduct()
// Ya no es necesario hacer la conversión, usa el ID original
  const productId = this.editingProduct.id; // ¡Es un string UUID!
 
// Envía la solicitud con el ID como string
  const { data } = await apiClient.put(`/api/products/${productId}`, this.editingProduct);
        
        // Actualiza el producto en la lista local
        const index = this.products.findIndex(p => p.id === data.id);
        if (index !== -1) {
          // Reemplaza el producto antiguo con el nuevo
          this.products.splice(index, 1, data);
        }
        
        this.closeEditModal();
        // Muestra un mensaje de éxito
        alert('Producto actualizado exitosamente.');
      } catch (error) {
        this.editError = 'Error al actualizar el producto. Por favor, inténtalo de nuevo.';
        console.error("Error al actualizar producto:", error);
      } finally {
        this.isUpdating = false;
      }
    },

// --- Método de Eliminación ---
async confirmDelete(product) {
  if (confirm(`¿Estás seguro de que quieres eliminar el producto "${product.name}"?`)) {
    try {
      // Usa el ID del producto tal como viene, que es un string UUID
      const productId = product.id;
      
      await apiClient.delete(`/api/products/${productId}`);
      
      // Elimina el producto de la lista local
      this.products = this.products.filter(p => p.id !== product.id);
      
      alert('Producto eliminado exitosamente.');
    } catch (error) {
      alert('Error al eliminar el producto.');
      console.error("Error al eliminar producto:", error);
    }
  }
}
  },
  
  mounted() {
    this.fetchProducts();
  }
};
</script>

<style scoped>

* {
  box-sizing: border-box;
}

.products-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  padding: 40px;
}

/* ===== PAGE HEADER ===== */
.page-header {
  background: white;
  border-radius: 24px;
  padding: 40px;
  margin-bottom: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  display: flex;
  align-items: center;
}

.header-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
  margin-right: 24px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  color: #718096;
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.header-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-radius: 16px;
  border: 2px solid rgba(102, 126, 234, 0.2);
}

.stat-number {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 4px;
}

.stat-label {
  color: #718096;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ===== CONTENT WRAPPER ===== */
.content-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: start;
}

/* ===== FORM CARD ===== */
.form-card, .list-card {
  background: white;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.card-header {
  padding: 32px 40px 24px 40px;
  border-bottom: 2px solid #f7fafc;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
  margin-right: 16px;
}

.card-title h3 {
  font-size: 20px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 4px 0;
}

.card-title p {
  color: #718096;
  margin: 0;
  font-size: 14px;
}

.card-actions {
  display: flex;
  gap: 12px;
}

/* ===== FORM STYLES ===== */
.product-form {
  padding: 40px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  display: flex;
  align-items: center;
  color: #4a5568;
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
}

.form-group label i {
  margin-right: 8px;
  width: 16px;
  color: #718096;
}

.form-input, .form-textarea {
  padding: 16px 20px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
  background: #f8fafc;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
}

.reset-btn, .submit-btn {
  padding: 16px 24px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  font-size: 16px;
}

.reset-btn {
  background: #f7fafc;
  color: #4a5568;
  border: 2px solid #e2e8f0;
}

.reset-btn:hover {
  background: #edf2f7;
  transform: translateY(-2px);
}

.submit-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.button-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* ===== ALERTS ===== */
.alert {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-radius: 12px;
  margin-top: 24px;
  border: 1px solid;
}

.alert-error {
  background: linear-gradient(135deg, #fed7d7, #feb2b2);
  border-color: #fc8181;
  color: #c53030;
}

.alert-success {
  background: linear-gradient(135deg, #c6f6d5, #9ae6b4);
  border-color: #68d391;
  color: #276749;
}

.alert-icon {
  margin-right: 12px;
  font-size: 20px;
}

.alert-content {
  flex: 1;
}

.alert-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.alert-close:hover {
  background: rgba(0, 0, 0, 0.1);
}

/* ===== SEARCH BAR ===== */
.search-section {
  padding: 24px 40px;
  border-bottom: 2px solid #f7fafc;
}

.search-bar {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 16px;
  color: #718096;
  z-index: 2;
}

.search-input {
  width: 100%;
  padding: 16px 20px 16px 48px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 16px;
  background: #f8fafc;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.clear-search {
  position: absolute;
  right: 16px;
  background: none;
  border: none;
  color: #718096;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.clear-search:hover {
  background: #e2e8f0;
  color: #4a5568;
}

/* ===== REFRESH BUTTON ===== */
.refresh-btn {
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.refresh-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* ===== LOADING, ERROR, EMPTY STATES ===== */
.loading-state, .error-state, .empty-state {
  padding: 60px 40px;
  text-align: center;
}

.loading-spinner {
  margin-bottom: 24px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #718096;
  font-size: 18px;
  margin: 0;
}

.error-icon, .empty-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 32px;
}

.error-icon {
  background: linear-gradient(135deg, #fed7d7, #feb2b2);
  color: #e53e3e;
}

.empty-icon {
  background: linear-gradient(135deg, #e2e8f0, #cbd5e0);
  color: #718096;
}

.error-content h3, .empty-content h3 {
  font-size: 24px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 12px 0;
}

.error-content p, .empty-content p {
  color: #718096;
  margin: 0 0 24px 0;
  font-size: 16px;
}

.retry-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

/* ===== PRODUCTS GRID ===== */
.products-grid {
  padding: 24px 40px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.product-card {
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s ease;
  position: relative;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.15);
  border-color: #667eea;
}

.product-avatar {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  margin-bottom: 16px;
}

.product-info {
  margin-bottom: 16px;
}

.product-name {
  font-size: 18px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 12px 0;
}

.product-price {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #4a5568;
  margin: 8px 0;
}

.product-price i {
  margin-right: 8px;
  color: #718096;
}

.product-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-size: 14px;
}

.edit-btn {
  background: #e6fffa;
  color: #319795;
}

.edit-btn:hover {
  background: #b2f5ea;
}

.delete-btn {
  background: #fef2f2;
  color: #e53e3e;
}

.delete-btn:hover {
  background: #feb2b2;
}

/* Animations */
.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.5s ease;
}
.slide-down-enter-from, .slide-down-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}

.product-item-enter-active, .product-item-leave-active {
  transition: all 0.5s ease;
}

.product-item-enter-from, .product-item-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

.product-item-leave-active {
  position: absolute;
}
/* ... (tu código CSS actual) ... */

/* ===== MODAL STYLES ===== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: white;
  border-radius: 24px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 500px;
  animation: slide-up 0.4s ease-out forwards;
}

.modal-header {
  padding: 24px 32px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #2d3748;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #718096;
  cursor: pointer;
  transition: color 0.3s;
}

.close-btn:hover {
  color: #2d3748;
}

.modal-form {
  padding: 32px;
}

.modal-form .form-group {
  margin-bottom: 24px;
}

.modal-form .form-actions {
  margin-top: 32px;
  justify-content: flex-end;
}

.cancel-btn {
  background: #f7fafc;
  color: #4a5568;
  border: 2px solid #e2e8f0;
  padding: 12px 20px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.cancel-btn:hover {
  background: #edf2f7;
}

/* Animations */
@keyframes slide-up {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
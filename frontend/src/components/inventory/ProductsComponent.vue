
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
 <BackButton />
</div>
 </div>
 <div class="header-stats">

<div class="stat-item stat-low-stock">
 <span class="stat-number">{{ lowStockCount }}</span>
 <span class="stat-label">Productos con Stock Bajo</span>
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
 <div class="card-content">
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
 min="0"
 step="0.01"
 required
 class="form-input"
/>
 </div>

 <div class="form-group">
<label for="product-stock">
 <i class="fas fa-warehouse"></i>
 <span>Stock Inicial *</span>
</label>
<input
 id="product-stock"
 type="number"
 v-model.number="newProduct.stock"
 placeholder="Cantidad inicial en inventario"
 required
 min="0"
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
 </div>
 
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
 {{ parseFloat(product.price).toFixed(2) }} </p>
   <p class="product-stock" :class="{ 'low-stock': product.stock < 10 }">
 <i class="fas fa-cubes"></i>
 Stock: {{ product.stock }}
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
 </div >
</transition-group>
 </div>

 <div v-if="totalPages > 1 && filteredProducts.length > 0" class="pagination">
<button
 @click="prevPage"
 :disabled="currentPage === 1"
 class="page-btn"
>
 <i class="fas fa-chevron-left"></i>
</button>

<div class="page-numbers">
 <button
 v-for="page in visiblePages"
 :key="page"
 @click="goToPage(page)"
 :class="['page-number', { active: page === currentPage }]"
 >
 {{ page }}
 </button>
</div>

<button
 @click="nextPage"
 :disabled="currentPage === totalPages"
 class="page-btn"
>
 <i class="fas fa-chevron-right"></i>
</button>
 </div>
 <div v-if="!loading && filteredProducts.length > 0" class="results-info">
Mostrando {{ (currentPage - 1) * itemsPerPage + 1 }} - {{ Math.min(currentPage * itemsPerPage, filteredProducts.length) }} de {{ filteredProducts.length }} productos.
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
 <input type="number" id="edit-price" v-model.number="editingProduct.price" required class="form-input" min="0" step="0.01" />
 </div>
 <div class="form-group">
 <label for="edit-stock">Stock</label>
 <input type="number" id="edit-stock" v-model.number="editingProduct.stock" required class="form-input" min="0" />
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
import apiClient from '../../axios';
import BackButton from '../vendedor/BackButton.vue';

export default {
name: 'ProductsManagement',
components: {
BackButton
},
data() {
return {
products: [],
newProduct: {
// Inicializar price como 0.00 para reforzar el tipo decimal/número
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
itemsPerPage: 6,
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
// Asegura que el número de páginas sea al menos 1
return Math.ceil(this.filteredProducts.length / this.itemsPerPage) || 1;
},

paginatedProducts() {
const start = (this.currentPage - 1) * this.itemsPerPage;
const end = start + this.itemsPerPage;
return this.filteredProducts.slice(start, end);
},

totalStock() {
// Se mantiene la función por si se usa en otro lugar, pero se eliminó del template
return this.products.reduce((sum, product) => sum + (product.stock || 0), 0);
},

// 💡 NUEVO CÓMPUTO: Productos con stock bajo (Stock < 10)
lowStockCount() {
    if (!this.products) return 0;
    // Usa la misma lógica de "low-stock" definida en el CSS
    return this.products.filter(product => product.stock < 10).length;
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
},
// Asegura que la página actual sea válida al cambiar el filtro
filteredProducts() {
if (this.currentPage > this.totalPages) {
this.currentPage = this.totalPages;
}
}
},
methods: {
// --- Métodos de Paginación ---
goToPage(page) {
if (page >= 1 && page <= this.totalPages) {
this.currentPage = page;
}
},
prevPage() {
if (this.currentPage > 1) {
this.currentPage--;
}
},
nextPage() {
if (this.currentPage < this.totalPages) {
this.currentPage++;
}
},

async addProduct() {
this.addError = null;
this.addSuccess = null;
this.isSubmitting = true;

// Saneamiento inicial: asegura que null/undefined se manejen como 0
const price = this.newProduct.price === null || this.newProduct.price === undefined ? 0 : this.newProduct.price;
const stock = this.newProduct.stock === null || this.newProduct.stock === undefined ? 0 : this.newProduct.stock;

// Validaciones de negocio y tipo de dato
if (!this.newProduct.name.trim() || isNaN(price) || price <= 0 || isNaN(stock) || stock < 0) {
this.addError = "El nombre, el precio y el stock son obligatorios. El precio debe ser positivo y el stock no negativo.";
this.isSubmitting = false;
return;
}

// Clonar y formatear el producto antes de enviar
const productToSend = {
name: this.newProduct.name.trim(),
// Asegura dos decimales para el envío a la API
price: parseFloat(price).toFixed(2),
stock: parseInt(stock)
};


try {
const { data } = await apiClient.post('/api/products', productToSend);

this.addSuccess = `Producto "${data.name}" registrado exitosamente.`;
// Añadimos el nuevo producto (mapeando a números para el FE)
this.products.unshift({
...data,
price: parseFloat(data.price),
stock: parseInt(data.stock)
});

this.resetForm();

// Ir a la primera página para ver el producto recién agregado
this.currentPage = 1;

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
// Mapeamos los datos para asegurar que price y stock son NUMEROS antes de guardarlos en el estado de Vue
this.products = data.map(p => ({
...p,
price: parseFloat(p.price),
stock: parseInt(p.stock)
}));
} catch (error) {
// Manejo de error para el componente de productos
this.error = 'Error al cargar los productos. Por favor, inténtalo de nuevo.';
console.error("Error al cargar productos:", error);
} finally {
this.loading = false;
}
},

resetForm() {
this.newProduct = {
name: '',
price: 0.00,
stock: 0
};
this.addError = null;
this.addSuccess = null;
},

// --- Métodos de Edición ---
openEditModal(product) {
// Aseguramos que los valores sean números antes de ponerlos en el modal (crucial para v-model.number)
this.editingProduct = {
...product,
price: parseFloat(product.price),
stock: parseInt(product.stock)
};
this.showEditModal = true;
this.editError = null;
},

closeEditModal() {
this.showEditModal = false;
this.editingProduct = null;
},

async updateProduct() {
// 1. Saneamiento: Si el usuario borra el campo, v-model.number lo setea a null.
// Esto causaría el 400 en el backend. Lo saneamos a 0.
const price = this.editingProduct.price === null || this.editingProduct.price === undefined ? 0 : this.editingProduct.price;
const stock = this.editingProduct.stock === null || this.editingProduct.stock === undefined ? 0 : this.editingProduct.stock;

// Asignar los valores saneados para la validación (Vue actualizará el input)
this.editingProduct.price = price;
this.editingProduct.stock = stock;

this.isUpdating = true;
this.editError = null;

// 2. Validación: precio debe ser positivo y stock no negativo
if (!this.editingProduct.name.trim() || isNaN(price) || price <= 0 || isNaN(stock) || stock < 0) {
this.editError = "El nombre, el precio y el stock son obligatorios. El precio debe ser positivo y el stock no negativo.";
this.isUpdating = false;
return; // Detiene la ejecución si la validación falla
}

try {
const productId = this.editingProduct.id;

// 3. Formateo y Envío: Clonamos y formateamos antes de enviar
const productUpdate = {
// Formatear precio antes de enviar (ej: 12.5 -> "12.50")
price: parseFloat(price).toFixed(2),
stock: parseInt(stock),
name: this.editingProduct.name.trim()
};

const { data } = await apiClient.put(`/api/products/${productId}`, productUpdate);

const index = this.products.findIndex(p => p.id === data.id);
if (index !== -1) {
// 4. Actualización del Estado: Actualizamos con los nuevos datos (mapeando a números para el frontend)
this.products.splice(index, 1, {
...data,
price: parseFloat(data.price),
stock: parseInt(data.stock)
});
}

this.closeEditModal();
alert(`Producto "${data.name}" actualizado exitosamente.`);
} catch (error) {
// Manejo de error de la API (incluyendo el 400 Bad Request que venías recibiendo)
this.editError = error.response?.data?.msg || 'Error al actualizar el producto. Por favor, inténtalo de nuevo.';
console.error("Error al actualizar producto:", error);
} finally {
this.isUpdating = false;
}
},

// --- Método de Eliminación ---
async confirmDelete(product) {
if (confirm(`¿Estás seguro de que quieres eliminar el producto "${product.name}"?`)) {
try {
const productId = product.id;

// 🟢 CORRECCIÓN 2: Se usa el endpoint y el ID de PRODUCTO
await apiClient.delete(`/api/products/${productId}`);

// Filtramos la lista para remover el producto eliminado
this.products = this.products.filter(p => p.id !== product.id);

// Aseguramos que la paginación se ajuste si se elimina el último elemento de la página
if (this.paginatedProducts.length === 0 && this.currentPage > 1) {
this.currentPage--;
}

alert(`Producto "${product.name}" eliminado exitosamente.`);
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
/* ===== RESPONSIVE RESET ===== */
* {
  box-sizing: border-box;
}

.products-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  padding: 20px;
}

/* ===== PAGE HEADER ===== */
.page-header {
  background: white;
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.header-info {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  margin-right: 16px;
  flex-shrink: 0;
}

.page-title {
  font-size: clamp(20px, 4vw, 32px);
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.page-subtitle {
  color: #718096;
  margin: 0;
  font-size: clamp(14px, 2.5vw, 16px);
  font-weight: 500;
}

.header-stats {
  flex-shrink: 0;
}

.stat-item {
  text-align: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-radius: 16px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  min-width: 100px;
}

.stat-number {
  display: block;
  font-size: clamp(20px, 4vw, 32px);
  font-weight: 700;
  color: #667eea;
  margin-bottom: 4px;
}

.stat-label {
  color: #718096;
  font-size: clamp(12px, 2vw, 14px);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 💡 NUEVO ESTILO PARA ALERTA DE STOCK BAJO */
.stat-item.stat-low-stock {
  /* Usar colores de advertencia */
  border: 2px solid #dc3545; /* Rojo de peligro */
  background: linear-gradient(135deg, rgba(220, 53, 69, 0.1), rgba(255, 193, 7, 0.1));
}

.stat-item.stat-low-stock .stat-number {
  color: #dc3545; /* Rojo para visibilidad inmediata */
}

.stat-item.stat-low-stock .stat-label {
  color: #dc3545;
}


/* ===== CONTENT WRAPPER ===== */
.content-wrapper {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  align-items: start;
}

/* ===== FORM CARD ===== */
.form-card, .list-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.card-header {
  padding: 24px 20px 16px 20px;
  border-bottom: 2px solid #f7fafc;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.card-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
  margin-right: 12px;
  flex-shrink: 0;
}

.card-title {
  flex: 1;
  min-width: 0;
}

.card-title h3 {
  font-size: clamp(16px, 3vw, 20px);
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 4px 0;
}

.card-title p {
  color: #718096;
  margin: 0;
  font-size: clamp(12px, 2.5vw, 14px);
}

.card-actions {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

/* ===== FORM STYLES ===== */
.product-form {
  padding: 24px 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
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
  padding: 14px 16px;
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

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.reset-btn, .submit-btn {
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  font-size: 14px;
  min-width: 120px;
  justify-content: center;
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
  align-items: flex-start;
  padding: 16px;
  border-radius: 12px;
  margin-top: 20px;
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
  font-size: 18px;
  margin-top: 2px;
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
  min-width: 0;
  word-break: break-word;
}

.alert-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.3s ease;
  margin-left: 12px;
  flex-shrink: 0;
}

.alert-close:hover {
  background: rgba(0, 0, 0, 0.1);
}

/* ===== SEARCH BAR ===== */
.search-section {
  padding: 20px;
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
  padding: 14px 16px 14px 48px;
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
  padding: 10px 16px;
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
  font-size: 14px;
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
  padding: 40px 20px;
  text-align: center;
}

.loading-spinner {
  margin-bottom: 20px;
}

.spinner {
  width: 40px;
  height: 40px;
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
  font-size: 16px;
  margin: 0;
}

.error-icon, .empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 28px;
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
  font-size: clamp(18px, 3.5vw, 24px);
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 12px 0;
}

.error-content p, .empty-content p {
  color: #718096;
  margin: 0 0 20px 0;
  font-size: clamp(14px, 2.5vw, 16px);
}

.retry-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 12px 20px;
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
  padding: 20px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.product-card {
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.15);
  border-color: #667eea;
}

.product-avatar {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
  margin-bottom: 16px;
}

.product-info {
  margin-bottom: 16px;
}

.product-name {
  font-size: clamp(16px, 3vw, 18px);
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 12px 0;
  line-height: 1.4;
  word-break: break-word;
}

.product-price {
  display: flex;
  align-items: center;
  font-size: clamp(14px, 2.5vw, 16px);
  font-weight: 600;
  color: #4a5568;
  margin: 8px 0;
}

.product-price i {
  margin-right: 8px;
  color: #718096;
}

.product-stock {
  display: flex;
  align-items: center;
  font-size: clamp(14px, 2.5vw, 16px);
  font-weight: 600;
  color: #4a5568;
  margin: 8px 0;
}

.product-stock i {
  margin-right: 8px;
  color: #718096;
}

/* Stock bajo en la tarjeta individual */
.product-stock.low-stock {
  color: #dc3545; /* Rojo para alertar */
  font-weight: 700;
}
.product-stock.low-stock i {
  color: #dc3545;
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

/* ===== PAGINATION ===== */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  gap: 8px;
  flex-wrap: wrap;
}

.page-btn {
  width: 40px;
  height: 40px;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-size: 14px;
  color: #4a5568;
}

.page-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.page-number {
  width: 40px;
  height: 40px;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-weight: 600;
  color: #4a5568;
}

.page-number:hover {
  border-color: #667eea;
  color: #667eea;
}

.page-number.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: #667eea;
  color: white;
}

/* ===== RESULTS INFO ===== */
.results-info {
  padding: 16px 20px;
  text-align: center;
  color: #718096;
  font-size: 14px;
  border-top: 1px solid #e2e8f0;
}

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
  padding: 20px;
}

.modal-container {
  background: white;
  border-radius: 20px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  animation: slide-up 0.4s ease-out forwards;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.modal-header h3 {
  margin: 0;
  font-size: clamp(18px, 4vw, 24px);
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
  padding: 8px;
  border-radius: 50%;
}

.close-btn:hover {
  color: #2d3748;
  background: #f7fafc;
}

.modal-form {
  padding: 24px;
}

.modal-form .form-group {
  margin-bottom: 20px;
}

.modal-form .form-actions {
  margin-top: 24px;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 12px;
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
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cancel-btn:hover {
  background: #edf2f7;
}

/* ===== ANIMATIONS ===== */
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

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

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

/* ===== RESPONSIVE BREAKPOINTS ===== */

/* Tablets */
@media (min-width: 768px) {
  .products-container {
    padding: 30px;
  }
  
  .page-header {
    padding: 32px;
    margin-bottom: 32px;
  }
  
  .header-icon {
    width: 64px;
    height: 64px;
    font-size: 28px;
    margin-right: 24px;
  }
  
  .content-wrapper {
    grid-template-columns: 1fr 1.2fr;
    gap: 32px;
  }
  
  .form-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .product-form {
    padding: 32px;
  }
  
  .card-header {
    padding: 32px 32px 24px 32px;
  }
  
  .search-section, .products-grid {
    padding: 24px 32px;
  }
  
  .grid-container {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 24px;
  }
  
  .product-card {
    padding: 24px;
  }
  
  .product-avatar {
    width: 56px;
    height: 56px;
    font-size: 24px;
  }
  
  .form-actions {
    justify-content: flex-end;
  }
  
  .modal-container {
    max-width: 600px;
  }
  
  .modal-header {
    padding: 24px 32px;
  }
  
  .modal-form {
    padding: 32px;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .products-container {
    padding: 40px;
  }
  
  .content-wrapper {
    grid-template-columns: 1fr 1.5fr;
  }
  
  .grid-container {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }
  
  .stat-item {
    padding: 20px 24px;
  }
}

/* Large Desktop */
@media (min-width: 1200px) {
  .grid-container {
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  }
}

/* Mobile optimizations */
@media (max-width: 480px) {
  .products-container {
    padding: 16px;
  }
  
  .page-header {
    padding: 20px;
    margin-bottom: 20px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-info {
    width: 100%;
  }
  
  .header-icon {
    width: 48px;
    height: 48px;
    font-size: 20px;
    margin-right: 12px;
  }
  
  .card-header {
    padding: 20px 16px 16px 16px;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .card-title {
    margin-bottom: 12px;
  }
  
  .product-form {
    padding: 20px 16px;
  }
  
  .search-section, .products-grid {
    padding: 16px;
  }
  
  .form-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .reset-btn, .submit-btn {
    width: 100%;
    justify-content: center;
    min-width: auto;
  }
  
  .grid-container {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .product-card {
    padding: 16px;
  }
  
  .pagination {
    gap: 4px;
    padding: 16px;
  }
  
  .page-btn, .page-number {
    width: 36px;
    height: 36px;
  }
  
  .modal-container {
    margin: 16px;
    max-height: calc(100vh - 32px);
  }
  
  .modal-header {
    padding: 16px 20px;
  }
  
  .modal-form {
    padding: 20px;
  }
  
  .modal-form .form-actions {
    flex-direction: column;
  }
  
  .cancel-btn, .submit-btn {
    width: 100%;
  }
}

/* Ultra small screens */
@media (max-width: 320px) {
  .products-container {
    padding: 12px;
  }
  
  .page-header {
    padding: 16px;
  }
  
  .card-header {
    padding: 16px 12px;
  }
  
  .product-form, .search-section, .products-grid {
    padding: 16px 12px;
  }
}

/* Print styles */
@media print {
  .products-container {
    background: white !important;
    padding: 20px !important;
  }
  
  .form-card {
    display: none !important;
  }
  
  .page-header {
    box-shadow: none !important;
    border: 1px solid #ccc !important;
  }
  
  .product-card {
    break-inside: avoid;
    box-shadow: none !important;
    border: 1px solid #ccc !important;
  }
  
  .product-actions {
    display: none !important;
  }
}
</style>
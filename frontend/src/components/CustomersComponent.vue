<template>
  <div class="customers-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-info">
          <div class="header-icon">
            <i class="fas fa-users"></i>
          </div>
          <div class="header-text">
            <h1 class="page-title">Gestión de Clientes</h1>
            <p class="page-subtitle">Administra tu base de datos de clientes</p>
                <BackButton />
          </div>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-number">{{ customers.length }}</span>
            <span class="stat-label">Clientes</span>
          </div>
        </div>
      </div>
    </div>

    <div class="content-wrapper">
      <div class="form-card">
        <div class="card-header">
          <div class="card-icon">
            <i :class="isEditing ? 'fas fa-user-edit' : 'fas fa-user-plus'"></i>
          </div>
          <div class="card-title">
            <h3>{{ isEditing ? 'Editar Cliente' : 'Registrar Nuevo Cliente' }}</h3>
            <p>{{ isEditing ? 'Modifica los datos del cliente seleccionado' : 'Agrega un nuevo cliente a tu base de datos' }}</p>
          </div>
        </div>
        
        <form @submit.prevent="isEditing ? updateCustomer() : addCustomer()" class="customer-form">
          <div class="form-grid">
            <div class="form-group full-width">
              <label for="customer-name">
                <i class="fas fa-user"></i>
                <span>Nombre del Cliente *</span>
              </label>
              <input 
                id="customer-name"
                type="text" 
                v-model="newCustomer.name" 
                placeholder="Ingresa el nombre completo del cliente"
                required 
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label for="customer-email">
                <i class="fas fa-envelope"></i>
                <span>Email *</span>
              </label>
              <input 
                id="customer-email"
                type="email" 
                v-model="newCustomer.email" 
                placeholder="cliente@ejemplo.com"
                required 
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label for="customer-phone">
                <i class="fas fa-phone-alt"></i>
                <span>Teléfono</span>
              </label>
              <input 
                id="customer-phone"
                type="tel" 
                v-model="newCustomer.phone" 
                placeholder="Ingresa el número de teléfono"
                class="form-input"
              />
            </div>
          </div>
          
          <div class="form-group full-width">
            <label for="customer-address">
              <i class="fas fa-map-marker-alt"></i>
              <span>Dirección</span>
            </label>
            <textarea 
              id="customer-address"
              v-model="newCustomer.address" 
              placeholder="Ingresa la dirección del cliente"
              class="form-textarea"
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="button" @click="resetForm" class="reset-btn">
              <i class="fas fa-undo"></i>
              <span>{{ isEditing ? 'Cancelar' : 'Limpiar' }}</span>
            </button>
            <button type="submit" class="submit-btn" :disabled="isSubmitting">
              <div v-if="isSubmitting" class="button-spinner"></div>
              <i v-else :class="isEditing ? 'fas fa-save' : 'fas fa-plus'"></i>
              <span>{{ isSubmitting ? 'Guardando...' : (isEditing ? 'Guardar Cambios' : 'Agregar Cliente') }}</span>
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
            <i class="fas fa-address-book"></i>
          </div>
          <div class="card-title">
            <h3>Lista de Clientes</h3>
            <p>Visualiza y gestiona tu base de clientes</p>
          </div>
          <div class="card-actions">
            <button @click="fetchCustomers" class="refresh-btn" :disabled="loading">
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
              placeholder="Buscar clientes por nombre o email..."
              class="search-input"
            />
            <button v-if="searchTerm" @click="searchTerm = ''" class="clear-search">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div v-if="loading && customers.length === 0" class="loading-state">
          <div class="loading-spinner">
            <div class="spinner"></div>
          </div>
          <p class="loading-text">Cargando clientes...</p>
        </div>

        <div v-if="error && !loading" class="error-state">
          <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <div class="error-content">
            <h3>Error al cargar clientes</h3>
            <p>{{ error }}</p>
            <button @click="fetchCustomers" class="retry-btn">
              <i class="fas fa-redo-alt"></i>
              Reintentar
            </button>
          </div>
        </div>

        <div v-if="!loading && !error && customers.length === 0" class="empty-state">
          <div class="empty-icon">
            <i class="fas fa-users-slash"></i>
          </div>
          <div class="empty-content">
            <h3>No hay clientes registrados</h3>
            <p>Comienza agregando tu primer cliente usando el formulario de arriba</p>
          </div>
        </div>

        <div v-if="!loading && !error && filteredCustomers.length > 0" class="customers-grid">
          <transition-group name="customer-item" tag="div" class="grid-container">
            <div 
              v-for="customer in paginatedCustomers" 
              :key="customer._id" 
              class="customer-card"
            >
              <div class="customer-avatar">
                <i class="fas fa-user-circle"></i>
              </div>
              <div class="customer-info">
                <h4 class="customer-name">{{ customer.name }}</h4>
                <p class="customer-email">
                  <i class="fas fa-envelope"></i>
                  {{ customer.email }}
                </p>
                <p v-if="customer.phone" class="customer-phone">
                  <i class="fas fa-phone-alt"></i>
                  {{ customer.phone }}
                </p>
              </div>
              <div class="customer-actions">
                <button @click="editCustomer(customer)" class="action-btn edit-btn" title="Editar">
                  <i class="fas fa-edit"></i>
                </button>
                <button @click="showDeleteConfirmation(customer)" class="action-btn delete-btn" title="Eliminar">
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

        <div v-if="filteredCustomers.length > 0" class="results-info">
          <span>
            Mostrando {{ ((currentPage - 1) * itemsPerPage) + 1 }} - 
            {{ Math.min(currentPage * itemsPerPage, filteredCustomers.length) }} 
            de {{ filteredCustomers.length }} clientes
          </span>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Confirmar Eliminación</h3>
          <button @click="cancelDelete" class="modal-close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <p>¿Estás seguro de que deseas eliminar a **{{ customerToDelete.name }}**?</p>
          <p>Esta acción no se puede deshacer.</p>
        </div>
        <div class="modal-footer">
          <button @click="cancelDelete" class="btn-cancel">Cancelar</button>
          <button @click="deleteCustomer" class="btn-delete">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import apiClient from '../axios';
import BackButton from '@/components/BackButton.vue';

export default {
components: {
    BackButton
  },
name: 'CustomersManagement',
data() {
return {
customers: [],
newCustomer: {
name: '',
email: '',
phone: '',
address: ''
},
loading: false,
error: null,
addError: null,
addSuccess: null,
isSubmitting: false,
searchTerm: '',
currentPage: 1,
itemsPerPage: 6,
editingCustomer: null,
customerToDelete: null,
showDeleteModal: false
};
},
computed: {
filteredCustomers() {
if (!this.searchTerm) return this.customers;

const term = this.searchTerm.toLowerCase();
return this.customers.filter(customer => 
customer.name.toLowerCase().includes(term) ||
customer.email.toLowerCase().includes(term)
);
},

totalPages() {
return Math.ceil(this.filteredCustomers.length / this.itemsPerPage);
},

paginatedCustomers() {
const start = (this.currentPage - 1) * this.itemsPerPage;
const end = start + this.itemsPerPage;
return this.filteredCustomers.slice(start, end);
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
},

isEditing() {
return this.editingCustomer !== null;
}
},
watch: {
searchTerm() {
this.currentPage = 1;
}
},
methods: {
async addCustomer() {
this.addError = null;
this.addSuccess = null;
this.isSubmitting = true;

if (!this.newCustomer.name.trim() || !this.newCustomer.email.trim()) {
this.addError = "El nombre y el email del cliente son campos obligatorios.";
this.isSubmitting = false;
return;
}

try {
const { data } = await apiClient.post('/api/customers', {
...this.newCustomer,
name: this.newCustomer.name.trim(),
email: this.newCustomer.email.trim()
});

this.addSuccess = 'Cliente registrado exitosamente.';
this.customers.unshift(data);
this.resetForm();

setTimeout(() => {
this.addSuccess = null;
}, 5000);
} catch (error) {
if (error.response?.data?.msg) {
this.addError = error.response.data.msg;
} else {
this.addError = 'Error al registrar el cliente. Por favor, inténtalo de nuevo.';
}
console.error("Error al agregar cliente:", error);
} finally {
this.isSubmitting = false;
}
},

editCustomer(customer) {
// Usa el ID para actualizar el cliente
this.editingCustomer = { ...customer };
this.newCustomer = { ...customer };
this.addError = null;
this.addSuccess = null;
window.scrollTo({ top: 0, behavior: 'smooth' });
},

async updateCustomer() {
this.addError = null;
this.addSuccess = null;
this.isSubmitting = true;

try {
// **Cambiado de _id a id**
if (!this.editingCustomer || !this.editingCustomer.id) {
this.addError = "Error: El ID del cliente no está definido para la actualización.";
this.isSubmitting = false;
return;
}

const { data } = await apiClient.put(`/api/customers/${this.editingCustomer.id}`, {
name: this.newCustomer.name.trim(),
email: this.newCustomer.email.trim(),
phone: this.newCustomer.phone,
address: this.newCustomer.address
});

this.addSuccess = 'Cliente actualizado exitosamente.';
// **Cambiado de _id a id**
const index = this.customers.findIndex(c => c.id === this.editingCustomer.id);
if (index !== -1) {
this.customers.splice(index, 1, data);
}
this.resetForm();

setTimeout(() => {
this.addSuccess = null;
}, 5000);
} catch (error) {
if (error.response?.data?.msg) {
this.addError = error.response.data.msg;
} else {
this.addError = 'Error al actualizar el cliente. Por favor, inténtalo de nuevo.';
}
console.error("Error al actualizar cliente:", error);
} finally {
this.isSubmitting = false;
}
},

showDeleteConfirmation(customer) {
// Copia el objeto completo del cliente
this.customerToDelete = { ...customer };
this.showDeleteModal = true;
},

cancelDelete() {
this.customerToDelete = null;
this.showDeleteModal = false;
},

async deleteCustomer() {
try {
// **Cambiado de _id a id**
await apiClient.delete(`/api/customers/${this.customerToDelete.id}`);
// **Cambiado de _id a id**
this.customers = this.customers.filter(c => c.id !== this.customerToDelete.id);
this.cancelDelete();
this.addSuccess = 'Cliente eliminado exitosamente.';
setTimeout(() => {
this.addSuccess = null;
}, 5000);
} catch (error) {
this.addError = 'Error al eliminar el cliente. Por favor, inténtalo de nuevo.';
console.error("Error al eliminar cliente:", error);
this.cancelDelete();
}
},

async fetchCustomers() {
this.loading = true;
this.error = null;

try {
const { data } = await apiClient.get('/api/customers');
this.customers = data;
} catch (error) {
this.error = 'Error al cargar los clientes. Por favor, inténtalo de nuevo.';
console.error("Error al cargar clientes:", error);
} finally {
this.loading = false;
}
},

resetForm() {
this.newCustomer = {
name: '',
email: '',
phone: '',
address: ''
};
this.editingCustomer = null;
this.addError = null;
this.addSuccess = null;
}
},

mounted() {
this.fetchCustomers();
}
};
</script>



<style scoped>
/* Estilos existentes de tu código original, adaptados para las nuevas funciones */

* {
  box-sizing: border-box;
}

.customers-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  padding: 40px;
}

/* Page Header */
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

/* Content Wrapper */
.content-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: start;
}

/* Form Card and List Card */
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

.card-title {
  flex-grow: 1;
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

/* Form Styles */
.customer-form {
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

/* Alerts */
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

/* Search Bar */
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

/* Refresh Button */
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

/* Loading, Error, Empty States */
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

/* Customers Grid */
.customers-grid {
  padding: 24px 40px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.customer-card {
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s ease;
  position: relative;
}

.customer-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.15);
  border-color: #667eea;
}

.customer-avatar {
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

.customer-info {
  margin-bottom: 16px;
}

.customer-name {
  font-size: 18px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 12px 0;
}

.customer-email, .customer-phone {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #4a5568;
  margin: 8px 0;
}

.customer-email i, .customer-phone i {
  margin-right: 8px;
  color: #718096;
}

.customer-actions {
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

.customer-item-enter-active, .customer-item-leave-active {
  transition: all 0.5s ease;
}

.customer-item-enter-from, .customer-item-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

.customer-item-leave-active {
  position: absolute;
}

/* Modal Styles */
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

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 450px;
  position: relative;
  animation: modal-fade-in 0.3s ease-out;
}

@keyframes modal-fade-in {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h3 {
  font-size: 24px;
  font-weight: 700;
  color: #e53e3e;
  margin: 0;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 30px;
  cursor: pointer;
  color: #718096;
}

.modal-body {
  margin-bottom: 20px;
}

.modal-body p {
  color: #4a5568;
  line-height: 1.5;
  margin: 0 0 10px 0;
}

.modal-body strong {
  color: #2d3748;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel, .btn-delete {
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.btn-cancel {
  background: #e2e8f0;
  color: #4a5568;
}

.btn-cancel:hover {
  background: #cbd5e0;
}

.btn-delete {
  background: #e53e3e;
  color: white;
}

.btn-delete:hover {
  background: #c53030;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(229, 62, 62, 0.3);
}

/* Responsive */
@media (max-width: 992px) {
  .content-wrapper {
    grid-template-columns: 1fr;
  }
  
  .page-header, .form-card, .list-card {
    padding: 30px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .customers-container {
    padding: 20px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  
  .header-stats {
    width: 100%;
    justify-content: space-between;
    gap: 16px;
  }
  
  .form-card, .list-card {
    padding: 20px;
  }
  
  .customer-form {
    padding: 20px;
  }
  
  .search-section {
    padding: 20px;
  }
  
  .customers-grid {
    padding: 20px;
  }
  
  .grid-container {
    grid-template-columns: 1fr;
  }
}
</style>
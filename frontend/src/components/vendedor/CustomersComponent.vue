<template>
  <div class="customers-container">
    <!-- Header con estadísticas dinámicas -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-info">
          <div class="header-icon">
            <i class="fas fa-users"></i>
          </div>
          <div class="header-text-container">
            <div class="header-text">
              <h1 class="page-title">Gestión de Clientes</h1>
              <p class="page-subtitle">Base de datos centralizada de tu organización</p>
            </div>
            <div class="header-actions">
              <BackButton />
            </div>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-number">{{ customers.length }}</span>
            <span class="stat-label">Total Clientes</span>
          </div>
        </div>
      </div>
    </div>

    <div class="content-wrapper">
      <!-- Formulario de Registro/Edición -->
      <div class="form-card">
        <div class="card-header"> 
          <div class="card-icon">
            <i :class="isEditing ? 'fas fa-edit' : 'fas fa-user-plus'"></i>
          </div>
          <div class="card-title">
            <h3>{{ isEditing ? 'Modificar Cliente' : 'Nuevo Registro' }}</h3>
            <p>{{ isEditing ? `Editando a: ${editingCustomer.name}` : 'Asocia un nuevo cliente a tu tenant' }}</p>
          </div>
        </div>
        
        <form @submit.prevent="handleSubmit" class="customer-form">
          <div class="form-grid">
            <!-- Cédula - Clave para Multitenant e integridad -->
            <div class="form-group">
              <label for="customer-cedula">
                <i class="fas fa-id-card"></i>
                <span>Cédula / ID Identificador *</span>
              </label>
              <input
                id="customer-cedula"
                type="text"
                v-model="newCustomer.cedula"
                placeholder="V-12345678"
                required
                :disabled="isEditing"
                class="form-input"
              />
              <small v-if="isEditing" class="input-hint">El identificador legal no es editable.</small>
            </div>

            <div class="form-group">
              <label for="customer-name">
                <i class="fas fa-user"></i>
                <span>Nombre Completo  *</span>
              </label>
              <input
                id="customer-name"
                type="text"
                v-model="newCustomer.name"
                placeholder="Ej: Juan Pérez "
                required
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label for="customer-email">
                <i class="fas fa-envelope"></i>
                <span>Correo Electrónico *</span>
              </label>
              <input
                id="customer-email"
                type="email"
                v-model="newCustomer.email"
                placeholder="correo@ejemplo.com"
                required
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label for="customer-phone">
                <i class="fas fa-phone-alt"></i>
                <span>Teléfono de Contacto</span>
              </label>
              <input
                id="customer-phone"
                type="tel"
                v-model="newCustomer.phone"
                placeholder="0412-0000000"
                class="form-input"
              />
            </div>
          </div>
        
          <div class="form-group full-width">
            <label for="customer-address">
              <i class="fas fa-map-marker-alt"></i>
              <span>Dirección Fiscal / Habitación</span>
            </label>
            <textarea
              id="customer-address"
              v-model="newCustomer.address"
              placeholder="Estado, Ciudad, Calle..."
              class="form-textarea"
            ></textarea>
          </div>

          <!-- Botonera de Acción -->
          <div class="form-actions">
            <button type="button" @click="resetForm" class="reset-btn" :disabled="isSubmitting">
              <i class="fas fa-undo"></i>
              <span>{{ isEditing ? 'Cancelar' : 'Limpiar' }}</span>
            </button>
            <button type="submit" class="submit-btn" :disabled="isSubmitting">
              <span v-if="isSubmitting" class="button-spinner"></span>
              <i v-else :class="isEditing ? 'fas fa-save' : 'fas fa-plus'"></i>
              <span>{{ isSubmitting ? 'Procesando...' : (isEditing ? 'Guardar Cambios' : 'Registrar Cliente') }}</span>
            </button>
          </div>
        </form>

        <!-- Mensajes de Feedback -->
        <transition name="slide-down">
          <div v-if="addError" class="alert alert-error">
            <i class="fas fa-exclamation-circle"></i>
            <span>{{ addError }}</span>
            <button @click="addError = null" class="alert-close">&times;</button>
          </div>
        </transition>

        <transition name="slide-down">
          <div v-if="addSuccess" class="alert alert-success">
            <i class="fas fa-check-circle"></i>
            <span>{{ addSuccess }}</span>
            <button @click="addSuccess = null" class="alert-close">&times;</button>
          </div>
        </transition>
      </div>

      <!-- Buscador y Lista -->
      <div class="list-card">
        <div class="card-header list-header">
          <div class="header-title-search">
            <div class="card-title">
              <h3>Directorio de Clientes</h3>
            </div>
            <div class="search-bar">
              <i class="fas fa-search"></i>
              <input 
                type="text" 
                v-model="searchTerm" 
                placeholder="Buscar por cédula, nombre o correo..."
              />
            </div>
          </div>
          <button @click="fetchCustomers" class="refresh-btn" :disabled="loading">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          </button>
        </div>

        <!-- Estados de la Lista -->
        <div v-if="loading" class="state-container">
          <div class="spinner"></div>
          <p>Sincronizando clientes con el servidor...</p>
        </div>

        <div v-else-if="error" class="state-container error">
          <i class="fas fa-wifi-slash"></i>
          <p>{{ error }}</p>
          <button @click="fetchCustomers" class="retry-btn">Reintentar</button>
        </div>

        <div v-else-if="filteredCustomers.length === 0" class="state-container empty">
          <i class="fas fa-search"></i>
          <p>No se encontraron clientes que coincidan con "{{ searchTerm }}"</p>
        </div>

        <!-- Tabla/Grid de Clientes -->
        <div v-else class="customers-grid">
          <div class="grid-container">
            <div v-for="customer in paginatedCustomers" :key="customer.id" class="customer-card">
              <div class="customer-header">
                <div class="avatar">
                  {{ customer.name.charAt(0).toUpperCase() }}
                </div>
                <div class="customer-main-info">
                  <h4 class="customer-name">{{ customer.name }}</h4>
                  <span class="badge-cedula">C.I: {{ customer.cedula }}</span>
                </div>
              </div>
              
              <div class="customer-details">
                <div class="detail">
                  <i class="fas fa-envelope"></i>
                  <span>{{ customer.email }}</span>
                </div>
                <div class="detail" v-if="customer.phone">
                  <i class="fas fa-phone"></i>
                  <span>{{ customer.phone }}</span>
                </div>
                <div class="detail address" v-if="customer.address">
                  <i class="fas fa-map-marker-alt"></i>
                  <span>{{ customer.address }}</span>
                </div>
              </div>

              <div class="customer-actions">
                <button @click="editCustomer(customer)" class="action-btn edit" title="Editar">
                  <i class="fas fa-pencil-alt"></i>
                </button>
                <button @click="showDeleteConfirmation(customer)" class="action-btn delete" title="Eliminar">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Paginación -->
        <div v-if="totalPages > 1" class="pagination-container">
          <button @click="currentPage--" :disabled="currentPage === 1" class="page-nav">
            <i class="fas fa-chevron-left"></i>
          </button>
          <div class="pages">
            <button 
              v-for="page in visiblePages" 
              :key="page" 
              @click="currentPage = page"
              :class="['page-num', { active: currentPage === page }]"
            >
              {{ page }}
            </button>
          </div>
          <button @click="currentPage++" :disabled="currentPage === totalPages" class="page-nav">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Modal de Eliminación -->
    <transition name="fade">
      <div v-if="showDeleteModal" class="modal-overlay">
        <div class="modal-content">
          <div class="modal-warning-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <h3>¿Eliminar Cliente?</h3>
          <p>Estás por eliminar a <strong>{{ customerToDelete.name }}</strong>. Se perderá el historial de contacto, pero los registros de ventas previas se mantendrán por integridad contable.</p>
          <div class="modal-footer">
            <button @click="cancelDelete" class="btn-cancel">Cancelar</button>
            <button @click="deleteCustomer" class="btn-confirm-delete">Confirmar Eliminación</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import axios from '../../axios';
import BackButton from '@/components/vendedor/BackButton.vue';

export default {
  name: 'CustomersManagement',
  components: { BackButton },
  data() {
    return {
      customers: [],
      newCustomer: {
        name: '',
        email: '',
        phone: '',
        address: '',
        cedula: ''
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
    isEditing() {
      return this.editingCustomer !== null;
    },
    filteredCustomers() {
      const term = this.searchTerm.toLowerCase();
      return this.customers.filter(c => 
        c.name.toLowerCase().includes(term) || 
        c.cedula.toLowerCase().includes(term) || 
        c.email.toLowerCase().includes(term)
      );
    },
    totalPages() {
      return Math.ceil(this.filteredCustomers.length / this.itemsPerPage);
    },
    paginatedCustomers() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      return this.filteredCustomers.slice(start, start + this.itemsPerPage);
    },
    visiblePages() {
      let pages = [];
      for (let i = 1; i <= this.totalPages; i++) pages.push(i);
      return pages;
    }
  },
  methods: {
    async fetchCustomers() {
      this.loading = true;
      try {
        const { data } = await axios.get('/api/customers');
        // El backend filtrará por tenant_id basándose en el JWT del usuario
        this.customers = data;
      } catch (err) {
        this.error = "No se pudieron obtener los clientes del servidor.";
      } finally {
        this.loading = false;
      }
    },

    async handleSubmit() {
      this.isSubmitting = true;
      this.addError = null;
      
      try {
        if (this.isEditing) {
          const { data } = await axios.put(`/api/customers/${this.editingCustomer.id}`, this.newCustomer);
          const index = this.customers.findIndex(c => c.id === data.id);
          this.customers.splice(index, 1, data);
          this.addSuccess = "Cliente actualizado correctamente.";
        } else {
          // Al enviar el POST, el backend asignará el tenant_id del creador automáticamente
          const { data } = await axios.post('/api/customers', this.newCustomer);
          this.customers.unshift(data);
          this.addSuccess = "Cliente registrado en el sistema.";
        }
        this.resetForm();
      } catch (err) {
        this.addError = err.response?.data?.msg || "Ocurrió un error en la operación.";
      } finally {
        this.isSubmitting = false;
      }
    },

    editCustomer(customer) {
      this.editingCustomer = customer;
      this.newCustomer = { ...customer };
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    showDeleteConfirmation(customer) {
      this.customerToDelete = customer;
      this.showDeleteModal = true;
    },

    cancelDelete() {
      this.showDeleteModal = false;
      this.customerToDelete = null;
    },

    async deleteCustomer() {
      try {
        await axios.delete(`/api/customers/${this.customerToDelete.id}`);
        this.customers = this.customers.filter(c => c.id !== this.customerToDelete.id);
        this.addSuccess = "Cliente removido con éxito.";
        this.cancelDelete();
      } catch (err) {
        this.addError = "No se pudo eliminar el registro.";
      }
    },

    resetForm() {
      this.newCustomer = { name: '', email: '', phone: '', address: '', cedula: '' };
      this.editingCustomer = null;
      setTimeout(() => { this.addSuccess = null; this.addError = null; }, 3000);
    }
  },
  mounted() {
    this.fetchCustomers();
  }
};
</script>

<style scoped>
.customers-container { padding: 30px; background: #f8fafc; min-height: 100vh; }

/* Page Header */
.page-header { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.header-info { display: flex; align-items: center; gap: 20px; }
.header-icon { width: 60px; height: 60px; background: #3f51b5; color: white; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.page-title { margin: 0; font-size: 1.8rem; color: #1e293b; }
.page-subtitle { margin: 5px 0 0; color: #64748b; }
.header-stats .stat-item { text-align: right; }
.stat-number { display: block; font-size: 2rem; font-weight: 800; color: #3f51b5; line-height: 1; }
.stat-label { font-size: 0.9rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }

/* Form Card */
.form-card { background: white; border-radius: 20px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-bottom: 30px; }
.card-header { display: flex; gap: 15px; align-items: center; margin-bottom: 25px; }
.card-icon { font-size: 1.5rem; color: #3f51b5; }
.card-title h3 { margin: 0; font-size: 1.2rem; }
.card-title p { margin: 0; font-size: 0.9rem; color: #94a3b8; }

.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
.form-group label { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-weight: 600; color: #475569; font-size: 0.9rem; }
.form-group label i { color: #3f51b5; }
.form-input, .form-textarea { width: 100%; padding: 12px 15px; border: 2px solid #e2e8f0; border-radius: 12px; transition: 0.3s; font-size: 1rem; }
.form-input:focus, .form-textarea:focus { border-color: #3f51b5; outline: none; box-shadow: 0 0 0 4px rgba(63,81,181,0.1); }
.full-width { grid-column: 1 / -1; }
.form-textarea { height: 80px; resize: vertical; }

.form-actions { display: flex; justify-content: flex-end; gap: 15px; padding-top: 10px; }
.submit-btn { background: #3f51b5; color: white; border: none; padding: 12px 25px; border-radius: 12px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: 0.3s; }
.submit-btn:hover:not(:disabled) { background: #303f9f; transform: translateY(-2px); }
.reset-btn { background: #f1f5f9; color: #475569; border: none; padding: 12px 25px; border-radius: 12px; cursor: pointer; font-weight: 600; }

/* Alerts */
.alert { margin-top: 20px; padding: 15px; border-radius: 12px; display: flex; align-items: center; gap: 12px; position: relative; }
.alert-error { background: #fef2f2; color: #991b1b; border: 1px solid #fee2e2; }
.alert-success { background: #f0fdf4; color: #166534; border: 1px solid #dcfce7; }
.alert-close { margin-left: auto; background: none; border: none; font-size: 1.2rem; cursor: pointer; color: inherit; opacity: 0.5; }

/* List Card */
.list-card { background: white; border-radius: 20px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
.list-header { flex-direction: row; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.header-title-search { display: flex; align-items: center; gap: 30px; flex: 1; }
.search-bar { position: relative; flex: 1; max-width: 400px; }
.search-bar i { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
.search-bar input { width: 100%; padding: 10px 15px 10px 45px; border-radius: 12px; border: 1px solid #e2e8f0; font-size: 0.9rem; }

/* Customer Cards */
.grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
.customer-card { border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; transition: 0.3s; position: relative; }
.customer-card:hover { border-color: #3f51b5; transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
.customer-header { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
.avatar { width: 50px; height: 50px; background: #e8eaf6; color: #3f51b5; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.2rem; }
.customer-name { margin: 0; font-size: 1.1rem; color: #1e293b; }
.badge-cedula { font-size: 0.8rem; background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 6px; font-weight: 700; }

.customer-details { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
.detail { display: flex; align-items: center; gap: 10px; font-size: 0.9rem; color: #64748b; }
.detail i { color: #94a3b8; width: 16px; }
.detail.address { border-top: 1px dashed #e2e8f0; padding-top: 10px; margin-top: 5px; }

.customer-actions { display: flex; gap: 10px; justify-content: flex-end; }
.action-btn { width: 35px; height: 35px; border-radius: 8px; border: none; cursor: pointer; transition: 0.2s; }
.action-btn.edit { background: #e0e7ff; color: #3f51b5; }
.action-btn.delete { background: #fee2e2; color: #ef4444; }
.action-btn:hover { transform: scale(1.1); }

/* Modals & Helpers */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 2000; backdrop-filter: blur(4px); }
.modal-content { background: white; padding: 30px; border-radius: 20px; max-width: 450px; text-align: center; }
.modal-warning-icon { font-size: 3rem; color: #ef4444; margin-bottom: 15px; }
.modal-footer { display: flex; gap: 15px; margin-top: 25px; }
.btn-cancel { flex: 1; padding: 12px; border-radius: 12px; border: none; cursor: pointer; font-weight: 600; }
.btn-confirm-delete { flex: 1; padding: 12px; border-radius: 12px; border: none; background: #ef4444; color: white; cursor: pointer; font-weight: 700; }

.state-container { padding: 50px; text-align: center; color: #94a3b8; }
.spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #3f51b5; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* Pagination */
.pagination-container { display: flex; justify-content: center; align-items: center; gap: 20px; margin-top: 30px; }
.page-nav { width: 40px; height: 40px; border-radius: 10px; border: 1px solid #e2e8f0; background: white; cursor: pointer; }
.page-num { width: 40px; height: 40px; border-radius: 10px; border: none; background: #f1f5f9; cursor: pointer; font-weight: 600; }
.page-num.active { background: #3f51b5; color: white; }

@media (max-width: 768px) {
  .header-content { flex-direction: column; align-items: flex-start; gap: 20px; }
  .header-stats { display: none; }
  .header-title-search { flex-direction: column; align-items: flex-start; gap: 15px; }
}
</style>


<!-- 
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
  flex-grow: 1;
}

.header-text-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-grow: 1;
  gap: 20px; /* Espacio entre el texto y las acciones */
}

.header-actions {
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
    width: 100%;
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
    padding: 10px;
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
</style> -->
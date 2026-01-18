<template>
  <div class="user-management-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.push('/dashboard')" title="Volver al Dashboard">
        <i class="fas fa-arrow-left">⬅️</i>
      </button>
      <div class="header-content">
        <h1 class="page-title">
          <i class="fas fa-users-cog"></i>
          Gestión de Empleaods
        </h1>
        <p class="page-subtitle">Administra los empleados del sistema</p>
      </div>
      <div class="header-actions">
        <button @click="openModal('create')" class="btn-add-user">
          <i class="fas fa-user-plus"></i>
          <span>Nuevo Usuario</span>
        </button>
      </div>
    </div>

    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon admin">
          <i class="fas fa-crown"></i>
        </div>
        <div class="stat-content">
          <h3>{{ stats.admins || 0 }}</h3>
          <p>Administradores</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon seller">
          <i class="fas fa-chart-line"></i>
        </div>
        <div class="stat-content">
          <h3>{{ stats.sellers || 0 }}</h3>
          <p>Vendedores</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warehouse">
          <i class="fas fa-boxes"></i>
        </div>
        <div class="stat-content">
          <h3>{{ stats.warehouses || 0 }}</h3>
          <p>Almacenistas</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon total">
          <i class="fas fa-users"></i>
        </div>
        <div class="stat-content">
          <h3>{{ stats.total || 0 }}</h3>
          <p>Total Usuarios</p>
        </div>
      </div>
    </div>

    <div class="main-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Cargando usuarios...</p>
      </div>
      
      <div v-if="error" class="error-alert">
        <i class="fas fa-exclamation-triangle"></i>
        <div>
          <h4>Error</h4>
          <p>{{ error }}</p>
        </div>
        <button @click="fetchUsers" class="btn-retry">
          <i class="fas fa-redo"></i> Reintentar
        </button>
      </div>

      <div v-if="!loading && !error" class="table-wrapper">
        <div class="table-header">
          <div class="search-box">
            <i class="fas fa-search"></i>
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="Buscar por email o ID..."
              @input="filterUsers"
            >
          </div>
          <div class="table-actions">
            <button class="btn-refresh" @click="fetchUsers" title="Refrescar lista">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshing }"></i>
            </button>
            <div class="filter-dropdown">
              <select v-model="roleFilter" @change="filterUsers">
                <option value="all">Todos los roles</option>
                <option value="1">Administradores</option>
                <option value="2">Vendedores</option>
                <option value="3">Almacenistas</option>
              </select>
            </div>
          </div>
        </div>

        <div class="table-container">
          <table class="users-table">
            <thead>
              <tr>
                <th class="col-email">
                  <span>Email</span>
                  <button @click="sortBy('email')" class="sort-btn">
                    <i class="fas fa-sort"></i>
                  </button>
                </th>
                <th class="col-role">
                  <span>Rol</span>
                  <button @click="sortBy('role_id')" class="sort-btn">
                    <i class="fas fa-sort"></i>
                  </button>
                </th>
                <th class="col-actions">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in filteredUsers" :key="user.id">
                <td class="user-email">
                  <i class="fas fa-envelope"></i>
                  <span>{{ user.email }}</span>
                </td>
                <td>
                  <div class="role-badge" :class="getRoleClass(user.role_id)">
                    <i :class="getRoleIcon(user.role_id)"></i>
                    <span>{{ user.role_name }}</span>
                  </div>
                </td>
                <td class="actions-cell">
                  <div class="action-buttons">
                    <button 
                      @click="openModal('edit', user)" 
                      class="btn-action btn-edit"
                      title="Editar usuario"
                    >
                      <i class="fas fa-edit"></i>
                    </button>
                    <button 
                      @click="openDeleteDialog(user)" 
                      class="btn-action btn-delete"
                      title="Eliminar usuario"
                      :disabled="user.role_id === 1"
                    >
                      <i class="fas fa-trash-alt"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="filteredUsers.length === 0" class="empty-state">
            <i class="fas fa-user-slash"></i>
            <h3>No se encontraron usuarios</h3>
            <p>No hay usuarios que coincidan con tu búsqueda</p>
          </div>
        </div>

        <div v-if="filteredUsers.length > 0" class="pagination">
          <button class="pagination-btn" :disabled="currentPage === 1" @click="prevPage">
            <i class="fas fa-chevron-left"></i>
          </button>
          <span class="page-info">Página {{ currentPage }} de {{ totalPages }}</span>
          <button class="pagination-btn" :disabled="currentPage === totalPages" @click="nextPage">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">
            <i :class="modalMode === 'create' ? 'fas fa-user-plus' : 'fas fa-user-edit'"></i>
            <h2>{{ modalMode === 'create' ? 'Crear Nuevo Usuario' : 'Editar Usuario' }}</h2>
          </div>
          <button @click="closeModal" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="saveUser">
            <div class="form-group">
  <label for="nombre">
    <i class="fas fa-user"></i> Nombre Completo
  </label>
  <input 
    type="text" 
    id="nombre" 
    v-model="currentUser.nombre" 
    required
    placeholder="Nombre del empleado"
  >
</div>

<div class="form-group">
  <label for="cedula">
    <i class="fas fa-id-card"></i> Cédula / ID
  </label>
  <input 
    type="text" 
    id="cedula" 
    v-model="currentUser.cedula" 
    required
    placeholder="Documento de identidad"
  >
</div>
            <div class="form-group">
              <label for="email">
                <i class="fas fa-envelope"></i>
                Email
              </label>
              <input 
                type="email" 
                id="email" 
                v-model="currentUser.email" 
                required
                :disabled="modalMode === 'edit'"
                placeholder="ejemplo@correo.com"
              >
            </div>

            <div v-if="modalMode === 'create'" class="form-group">
              <label for="password">
                <i class="fas fa-lock"></i>
                Contraseña
              </label>
              <input 
                type="password" 
                id="password" 
                v-model="currentUser.password" 
                required
                placeholder="••••••••"
              >
            </div>

            <div class="form-group">
              <label for="role">
                <i class="fas fa-user-tag"></i>
                Rol
              </label>
              <div class="role-options">
                <label 
                  v-for="role in roleOptions" 
                  :key="role.value"
                  :class="{ selected: currentUser.role_id === role.value }"
                  class="role-option"
                >
                  <input 
                    type="radio" 
                    name="role" 
                    :value="role.value" 
                    v-model="currentUser.role_id"
                    :disabled="role.value === 1 && modalMode === 'edit'"
                  >
                  <div class="role-content">
                    <i :class="role.icon"></i>
                    <div>
                      <strong>{{ role.name }}</strong>
                      <small>{{ role.description }}</small>
                    </div>
                  </div>
                </label>
              </div>
            </div>

            <div class="form-actions">
              <button 
                type="button" 
                @click="closeModal" 
                class="btn-cancel"
              >
                Cancelar
              </button>
              <button 
                type="submit" 
                class="btn-save"
                :disabled="isSaving"
              >
                <i class="fas" :class="isSaving ? 'fa-spinner fa-spin' : 'fa-save'"></i>
                {{ isSaving ? 'Guardando...' : 'Guardar' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div v-if="showDeleteDialog" class="modal-overlay" @click.self="showDeleteDialog = false">
      <div class="confirm-modal">
        <div class="confirm-icon">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="confirm-content">
          <h3>¿Eliminar usuario?</h3>
          <p>
            Estás a punto de eliminar al usuario 
            <strong>{{ userToDelete?.email }}</strong> (ID: {{ userToDelete?.id }}).
            Esta acción no se puede deshacer.
          </p>
          <div class="confirm-actions">
            <button @click="showDeleteDialog = false" class="btn-cancel">
              Cancelar
            </button>
            <button @click="deleteUser" class="btn-delete-confirm">
              <i class="fas fa-trash-alt"></i>
              Sí, eliminar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '@/axios';

export default {
  name: 'UserManagement',
  data() {
    return {
      users: [],
      filteredUsers: [],
      loading: false,
      refreshing: false,
      error: null,
      searchQuery: '',
      roleFilter: 'all',
      sortField: 'id',
      sortOrder: 'asc',
      currentPage: 1,
      itemsPerPage: 10,
      
      stats: {
        admins: 0,
        sellers: 0,
        warehouses: 0,
        total: 0
      },
      
      isModalOpen: false,
      modalMode: 'create',
      currentUser: {
        id: null,
        nombre: '', // Nuevo
        cedula: '', // Nuevo
        email: '',
        password: '',
        role_id: 2
      },
      isSaving: false,
      
      showDeleteDialog: false,
      userToDelete: null,
      
      roleOptions: [
        { value: 1, name: 'Administrador', icon: 'fas fa-crown', description: 'Acceso completo' },
        { value: 2, name: 'Vendedor', icon: 'fas fa-chart-line', description: 'Gestión de ventas' },
        { value: 3, name: 'Almacenista', icon: 'fas fa-boxes', description: 'Gestión de inventario' }
      ]
    };
  },
  
  computed: {
    totalPages() {
      return Math.ceil(this.filteredUsers.length / this.itemsPerPage);
    },
    
    paginatedUsers() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.filteredUsers.slice(start, end);
    }
  },
  
  mounted() {
    this.fetchUsers();
  },
  
  methods: {
    async fetchUsers() {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('api/admin/users');
        
        let userData;
        if (Array.isArray(response.data)) {
          userData = response.data;
        } else if (response.data && Array.isArray(response.data.users)) {
          userData = response.data.users;
        } else {
          throw new Error('Formato de respuesta incorrecto');
        }

        this.users = userData.map(user => ({
          ...user,
          id: String(user.id)
        }));
        
        this.filterUsers();
        this.calculateStats();
        
      } catch (err) {
        const status = err.response?.status;
        if (status === 403) {
          this.error = 'No tienes permisos de administrador para acceder a esta sección.';
        } else if (status === 401) {
          this.error = 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
          this.$router.push('/login');
        } else {
          this.error = err.response?.data?.msg || 'Error al cargar la lista de usuarios.';
        }
        console.error('Error al obtener usuarios:', err);
      } finally {
        this.loading = false;
        this.refreshing = false;
      }
    },
    
    calculateStats() {
      this.stats = {
        admins: this.users.filter(u => u.role_id === 1).length,
        sellers: this.users.filter(u => u.role_id === 2).length,
        warehouses: this.users.filter(u => u.role_id === 3).length,
        total: this.users.length
      };
    },
    
    filterUsers() {
      let filtered = [...this.users];
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        filtered = filtered.filter(user => 
          user.email.toLowerCase().includes(query) || 
          user.id.toLowerCase().includes(query)
        );
      }
      if (this.roleFilter !== 'all') {
        filtered = filtered.filter(user => user.role_id === parseInt(this.roleFilter));
      }
      filtered.sort((a, b) => {
        let aValue = a[this.sortField];
        let bValue = b[this.sortField];
        if (typeof aValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }
        if (aValue < bValue) return this.sortOrder === 'asc' ? -1 : 1;
        if (aValue > bValue) return this.sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
      this.filteredUsers = filtered;
      this.currentPage = 1;
    },
    
    sortBy(field) {
      if (this.sortField === field) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortField = field;
        this.sortOrder = 'asc';
      }
      this.filterUsers();
    },
    
    getRoleClass(roleId) {
      switch (roleId) {
        case 1: return 'role-admin';
        case 2: return 'role-seller';
        case 3: return 'role-warehouse';
        default: return '';
      }
    },
    
    getRoleIcon(roleId) {
      switch (roleId) {
        case 1: return 'fas fa-crown';
        case 2: return 'fas fa-chart-line';
        case 3: return 'fas fa-boxes';
        default: return 'fas fa-user';
      }
    },
    
    async saveUser() {
  if (this.isSaving) return;
  this.isSaving = true;
  
  try {
    if (this.modalMode === 'create') {
      // Enviar todo el objeto incluyendo nombre y cedula
      await axios.post('/admin/users', this.currentUser);
      alert('Empleado creado con éxito');
    } else {
      // Para editar, enviamos los campos actualizables
      await axios.put(`/admin/users/${this.currentUser.id}`, {
        nombre: this.currentUser.nombre,
        cedula: this.currentUser.cedula,
        role_id: this.currentUser.role_id
      });
      alert('Empleado actualizado');
    }
    this.fetchUsers();
    this.closeModal();
  } catch (err) {
    const errorMsg = err.response?.data?.msg || 'Error en el servidor';
    alert('Error: ' + errorMsg);
  } finally {
    this.isSaving = false;
  }
},
    
    async deleteUser() {
      try {
        await axios.delete(`/admin/users/${this.userToDelete.id}`);
        
        // CORRECCIÓN: Se usa alert nativo
        alert('Éxito: Usuario eliminado correctamente.');
        
        this.fetchUsers();
        this.showDeleteDialog = false;
      } catch (err) {
        const errorMsg = err.response?.data?.msg || 'Error al eliminar el usuario.';
        alert(`Error: ${errorMsg}`);
        console.error('Error al eliminar:', err);
      }
    },
    
   openModal(mode, user = null) {
  this.modalMode = mode;
  if (mode === 'create') {
    this.currentUser = { 
      id: null, 
      nombre: '', 
      cedula: '', 
      email: '', 
      password: '', 
      role_id: 2 
    };
  } else {
    this.currentUser = { 
      id: user.id, 
      nombre: user.nombre || '', 
      cedula: user.cedula || '',
      email: user.email, 
      role_id: user.role_id, 
      password: '' 
    };
  }
  this.isModalOpen = true;
},
    
    closeModal() {
      this.isModalOpen = false;
      this.currentUser = { id: null, email: '', password: '', role_id: 2 };
    },
    
    openDeleteDialog(user) {
      if (user.role_id === 1) {
        alert('Acción no permitida: No se puede eliminar a un administrador principal.');
        return;
      }
      this.userToDelete = user;
      this.showDeleteDialog = true;
    },
    
    prevPage() {
      if (this.currentPage > 1) this.currentPage--;
    },
    
    nextPage() {
      if (this.currentPage < this.totalPages) this.currentPage++;
    }
  }
};
</script>

<style scoped>
.user-management-page {
  min-height: 100vh;
  background: #f5f7fa;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Header */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px 30px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.back-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateX(-3px);
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 2rem;
  margin: 0 0 5px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-subtitle {
  opacity: 0.9;
  margin: 0;
  font-weight: 300;
}

.btn-add-user {
  background: white;
  color: #667eea;
  border: none;
  padding: 12px 24px;
  border-radius: 25px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-add-user:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

/* Stats Cards */
.stats-cards {
  padding: 30px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: white;
  border-radius: 15px;
  padding: 25px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.stat-icon.admin { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); }
.stat-icon.seller { background: linear-gradient(135deg, #4cd964 0%, #5ac8fa 100%); }
.stat-icon.warehouse { background: linear-gradient(135deg, #5ac8fa 0%, #007aff 100%); }
.stat-icon.total { background: linear-gradient(135deg, #ff9500 0%, #ff5e3a 100%); }

.stat-content h3 {
  font-size: 2rem;
  margin: 0;
  color: #2c3e50;
}

.stat-content p {
  margin: 5px 0 0 0;
  color: #7f8c8d;
  font-weight: 500;
}

/* Main Content */
.main-content {
  padding: 0 30px 30px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: white;
  border-radius: 15px;
  margin-top: 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e0e0e0;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-alert {
  background: #ffeaea;
  border-left: 4px solid #ff6b6b;
  padding: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.error-alert i {
  color: #ff6b6b;
  font-size: 1.5rem;
}

.btn-retry {
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  margin-left: auto;
}

/* Table Wrapper */
.table-wrapper {
  background: white;
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  margin-top: 20px;
}

.table-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.search-box {
  flex: 1;
  min-width: 300px;
  position: relative;
}

.search-box i {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #95a5a6;
}

.search-box input {
  width: 100%;
  padding: 12px 15px 12px 45px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: border-color 0.3s;
}

.search-box input:focus {
  outline: none;
  border-color: #667eea;
}

.table-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn-refresh {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.btn-refresh:hover {
  background: #f5f7fa;
  border-color: #667eea;
  color: #667eea;
}

.filter-dropdown select {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
  cursor: pointer;
}

/* Table */
.table-container {
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  background: #f8f9fa;
  position: sticky;
  top: 0;
  z-index: 10;
}

.users-table th {
  padding: 15px 20px;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #eee;
  white-space: nowrap;
}

.sort-btn {
  background: none;
  border: none;
  color: #95a5a6;
  cursor: pointer;
  margin-left: 5px;
  padding: 5px;
}

.sort-btn:hover {
  color: #667eea;
}

.users-table tbody tr {
  border-bottom: 1px solid #eee;
  transition: background-color 0.3s;
}

.users-table tbody tr:hover {
  background-color: #f8f9fa;
}

.users-table td {
  padding: 15px 20px;
  vertical-align: middle;
}

.user-id {
  font-family: 'Courier New', monospace;
  font-weight: 500;
}

.id-badge {
  background: #e8f4ff;
  color: #667eea;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9rem;
}

.user-email {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-email i {
  color: #95a5a6;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
  font-size: 0.9rem;
}

.role-admin {
  background: #ffebee;
  color: #d32f2f;
}

.role-seller {
  background: #e8f5e9;
  color: #2e7d32;
}

.role-warehouse {
  background: #e3f2fd;
  color: #1565c0;
}

.actions-cell {
  width: 120px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-action {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.btn-edit {
  background: #e3f2fd;
  color: #1976d2;
}

.btn-edit:hover {
  background: #1976d2;
  color: white;
}

.btn-delete {
  background: #ffebee;
  color: #d32f2f;
}

.btn-delete:hover:not(:disabled) {
  background: #d32f2f;
  color: white;
}

.btn-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty State */
.empty-state {
  padding: 60px 20px;
  text-align: center;
  color: #95a5a6;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 10px 0;
  color: #7f8c8d;
}

/* Pagination */
.pagination {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.pagination-btn {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.pagination-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-weight: 500;
  color: #2c3e50;
}

/* Modals */
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
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 15px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  animation: modalSlide 0.3s ease;
}

@keyframes modalSlide {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  padding: 25px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-title i {
  color: #667eea;
  font-size: 1.5rem;
}

.modal-title h2 {
  margin: 0;
  font-size: 1.5rem;
}

.modal-close {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: none;
  background: #f5f7fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.modal-close:hover {
  background: #ff6b6b;
  color: white;
}

.modal-body {
  padding: 25px;
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #2c3e50;
}

.form-group input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled {
  background: #f5f7fa;
  cursor: not-allowed;
}

.role-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.role-option {
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.role-option.selected {
  border-color: #667eea;
  background: #f0f7ff;
}

.role-option input {
  display: none;
}

.role-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.role-content i {
  font-size: 1.2rem;
  color: #667eea;
}

.role-content div {
  flex: 1;
}

.role-content strong {
  display: block;
  margin-bottom: 4px;
  color: #2c3e50;
}

.role-content small {
  color: #7f8c8d;
  font-size: 0.85rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 30px;
}

.btn-cancel {
  padding: 12px 24px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-cancel:hover {
  background: #f5f7fa;
}

.btn-save {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s;
}

.btn-save:hover:not(:disabled) {
  background: #5a6fd8;
  transform: translateY(-2px);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Confirm Modal */
.confirm-modal {
  background: white;
  border-radius: 15px;
  width: 100%;
  max-width: 450px;
  animation: modalSlide 0.3s ease;
}

.confirm-icon {
  background: #fff3e0;
  color: #f57c00;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 30px auto 20px;
  font-size: 2rem;
}

.confirm-content {
  padding: 0 30px 30px;
  text-align: center;
}

.confirm-content h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.confirm-content p {
  color: #7f8c8d;
  line-height: 1.6;
  margin-bottom: 25px;
}

.confirm-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.btn-delete-confirm {
  padding: 12px 24px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s;
}

.btn-delete-confirm:hover {
  background: #ff5252;
  transform: translateY(-2px);
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
    padding: 20px;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .btn-add-user {
    width: 100%;
    justify-content: center;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
    padding: 20px;
  }
  
  .main-content {
    padding: 0 20px 20px;
  }
  
  .table-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    min-width: auto;
  }
  
  .users-table th, 
  .users-table td {
    padding: 12px 15px;
  }
  
  .modal {
    max-height: 80vh;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 1.5rem;
  }
  
  .stat-card {
    flex-direction: column;
    text-align: center;
  }
  
  .user-email {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .role-badge {
    flex-direction: column;
    gap: 4px;
    text-align: center;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn-action {
    width: 100%;
  }
  
  .form-actions,
  .confirm-actions {
    flex-direction: column;
  }
  
  .btn-cancel,
  .btn-save,
  .btn-delete-confirm {
    width: 100%;
    justify-content: center;
  }
}

/* Animation for refresh */
.fa-spin {
  animation: fa-spin 1s infinite linear;
}

@keyframes fa-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
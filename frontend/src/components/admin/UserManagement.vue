<template>
  <div class="user-management-page admin-section">
    <button class="btn btn-primary add-button">
   <router-link to="/dashboard-admin">
      <i class="fas fa-arrow-left"></i> Volver al Dashboard Administrativo
    </router-link>
    </button>
 
    
    <h1 class="section-title">Gestión de Usuarios (Roles 1 y 2)</h1>
    
    <button @click="openModal('create')" class="btn btn-primary add-button">
      <i class="fas fa-plus-circle"></i> Agregar Nuevo Usuario
    </button>
    
    <div v-if="loading" class="alert alert-info">Cargando usuarios...</div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="table-container">
      <table class="user-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Rol</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span :class="{'role-admin': user.role_id === 1, 'role-seller': user.role_id === 2}">
                {{ user.role_name }}
              </span>
            </td>
            <td class="action-buttons">
              <button @click="openModal('edit', user)" class="btn btn-secondary">
                <i class="fas fa-edit"></i> Editar
              </button>
              <button @click="confirmDelete(user)" class="btn btn-danger">
                <i class="fas fa-trash-alt"></i> Eliminar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h2>{{ modalMode === 'create' ? 'Crear Nuevo Usuario' : 'Editar Usuario' }}</h2>
        <form @submit.prevent="saveUser">
          
          <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" v-model="currentUser.email" required :disabled="modalMode === 'edit'">
          </div>
          
          <div class="form-group" v-if="modalMode === 'create'">
            <label for="password">Contraseña</label>
            <input type="password" id="password" v-model="currentUser.password" required>
          </div>

          <div class="form-group">
            <label for="role">Rol</label>
            <select id="role" v-model="currentUser.role_id" required>
              <option :value="1">1 (Administrador)</option>
              <option :value="2">2 (Vendedor)</option>
            </select>
          </div>
          
          <div class="modal-actions">
            <button type="submit" class="btn btn-primary" :disabled="isSaving">
              <i class="fas fa-save"></i> {{ isSaving ? 'Guardando...' : 'Guardar' }}
            </button>
            <button type="button" @click="closeModal" class="btn btn-secondary">Cancelar</button>
          </div>
        </form>
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
      loading: false,
      error: null,
      
      isModalOpen: false,
      modalMode: 'create', 
      currentUser: { 
        id: null,
        email: '',
        password: '',
        role_id: 2 
      },
      isSaving: false
    };
  },
  mounted() {
    this.fetchUsers();
  },
  methods: {
    async fetchUsers() {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('/admin/users'); 
        this.users = response.data.users; 
      } catch (err) {
        this.error = 'No se pudo cargar la lista de usuarios. Verifica el endpoint de tu API.';
        console.error('Error al obtener usuarios:', err);
      } finally {
        this.loading = false;
      }
    },

    async saveUser() {
      this.isSaving = true;
      try {
        const dataToSend = { ...this.currentUser };

        if (this.modalMode === 'create') {
          await axios.post('/admin/users', dataToSend);
        } else {
          delete dataToSend.password; 
          await axios.put(`/admin/users/${this.currentUser.id}`, dataToSend);
        }
        
        this.fetchUsers();
        this.closeModal();
      } catch (err) {
        this.error = err.response?.data?.msg || 'Error al guardar el usuario.';
        console.error('Error al guardar:', err);
      } finally {
        this.isSaving = false;
      }
    },

    async deleteUser(userId) {
      this.error = null;
      try {
        await axios.delete(`/admin/users/${userId}`); 
        this.fetchUsers(); 
      } catch (err) {
        this.error = 'Error al eliminar el usuario.';
        console.error('Error al eliminar:', err);
      }
    },

    openModal(mode, user = null) {
      this.modalMode = mode;
      this.error = null;
      if (mode === 'create') {
        this.currentUser = { id: null, email: '', password: '', role_id: 2 };
      } else {
        this.currentUser = { 
          id: user.id, 
          email: user.email, 
          role_id: user.role_id, 
          password: '' 
        };
      }
      this.isModalOpen = true;
    },

    closeModal() {
      this.isModalOpen = false;
    },

    confirmDelete(user) {
      if (confirm(`¿Estás seguro de que quieres eliminar al usuario ${user.email} (ID: ${user.id})?`)) {
        this.deleteUser(user.id);
      }
    }
  }
};
</script>

<style scoped>
/* ------------------------------------------------------------------ */
/* Estilos Globales de la Sección de Administración (Consistencia)    */
/* ------------------------------------------------------------------ */
.admin-section {
  padding: 40px 20px;
  background-color: #f8f9fa; /* Fondo claro */
  font-family: 'Arial', sans-serif;
}

.section-title {
  color: #34495e;
  margin-bottom: 25px;
  font-size: 2em;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
  display: inline-block;
}

/* --- Botón Principal de Acción (Añadir) --- */
.add-button {
  margin-bottom: 20px;
  background-color: #27ae60; /* Verde para Añadir */
  border: none;
  font-weight: bold;
}
.add-button:hover {
  background-color: #2ecc71;
}

/* --- Alertas --- */
.alert {
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}
.alert-info { background-color: #d9edf7; color: #31708f; border: 1px solid #bce8f1; }
.alert-danger { background-color: #f2dede; color: #a94442; border: 1px solid #ebccd1; }


/* ------------------------------------------------------------------ */
/* Estilos de la Tabla (Table Design)                                 */
/* ------------------------------------------------------------------ */
.table-container {
  overflow-x: auto;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.user-table th, .user-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #ecf0f1;
}

.user-table thead {
  background-color: #3498db; /* Azul para el encabezado */
  color: white;
}

.user-table tbody tr:hover {
  background-color: #f5f5f5;
}

/* --- Estilos de Roles --- */
.role-admin {
  font-weight: bold;
  color: #e74c3c; /* Rojo para Admin */
}
.role-seller {
  font-weight: bold;
  color: #27ae60; /* Verde para Vendedor */
}

/* --- Botones de Acción de la Tabla --- */
.action-buttons button {
  margin-right: 8px;
  padding: 8px 12px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.9em;
}
.btn-secondary { background-color: #f39c12; color: white; }
.btn-secondary:hover { background-color: #d35400; }
.btn-danger { background-color: #e74c3c; color: white; }
.btn-danger:hover { background-color: #c0392b; }


/* ------------------------------------------------------------------ */
/* Estilos del Modal (Modal Design)                                   */
/* ------------------------------------------------------------------ */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 30px;
  border-radius: 10px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.modal-content h2 {
  color: #3498db;
  margin-top: 0;
  margin-bottom: 25px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #34495e;
}

.form-group input, .form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-sizing: border-box; /* Incluye padding y borde en el ancho total */
  transition: border-color 0.2s;
}

.form-group input:focus, .form-group select:focus {
  border-color: #3498db;
  outline: none;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
}

.btn-primary { 
  background-color: #3498db; 
  color: white; 
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  font-weight: bold;
}
.btn-primary:hover:not(:disabled) { background-color: #2980b9; }

/* Deshabilitado */
.btn-primary:disabled {
    background-color: #b2c2c2;
    cursor: not-allowed;
}
</style>
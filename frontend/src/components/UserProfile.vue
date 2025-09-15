<template>
  <div class="user-profile-container">
    <div class="profile-header">
      <div class="header-background"></div>
      <div class="header-content">
        <div class="avatar-section">
          <div class="user-avatar">
            <img v-if="profileImageUrl" :src="profileImageUrl" alt="Foto de perfil" class="profile-img" />
            <i v-else class="fas fa-user-circle"></i>
          </div>
          <div class="avatar-upload">
            <input type="file" ref="fileInput" @change="onFileSelected" style="display: none;" accept="image/*" />
            <button class="upload-btn" @click="$refs.fileInput.click()" title="Cambiar foto">
              <i class="fas fa-camera"></i>
            </button>
          </div>
        </div>
        <div class="user-title">
          <h1 class="profile-title">Perfil de Usuario</h1>
          <p class="profile-subtitle">Gestiona tu información personal</p>
        </div>
      </div>
    </div>

    <div class="profile-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">
          <div class="spinner"></div>
        </div>
        <p class="loading-text">Cargando información del usuario...</p>
      </div>

      <div v-if="error && !loading" class="error-state">
        <div class="error-card">
          <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <div class="error-content">
            <h3 class="error-title">Error al cargar perfil</h3>
            <p class="error-message">{{ error }}</p>
            <button @click="retryLoad" class="retry-btn">
              <i class="fas fa-redo-alt"></i>
              Reintentar
            </button>
          </div>
        </div>
      </div>

      <div v-if="selectedFile && !uploading" class="upload-form">
        <p class="upload-text">Archivo seleccionado: <strong>{{ selectedFile.name }}</strong></p>
        <button @click="uploadProfileImage" :disabled="uploading" class="upload-confirm-btn">
          <i class="fas fa-upload"></i> Subir Imagen
        </button>
      </div>

      <div v-if="uploading" class="uploading-state">
        <div class="loading-spinner">
          <div class="spinner"></div>
        </div>
        <p class="loading-text">Subiendo imagen...</p>
      </div>

      <div v-if="user && !loading" class="user-info-section">
        <div class="info-cards">
          <div class="info-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-id-card"></i>
              </div>
              <div class="card-title">
                <h3>Información Personal</h3>
                <p>Datos básicos de tu cuenta</p>
              </div>
              <button class="edit-btn" title="Editar información">
                <i class="fas fa-edit"></i>
              </button>
            </div>
            <div class="card-content">
              <div class="info-item">
                <div class="info-label">
                  <i class="fas fa-envelope"></i>
                  <span>Correo Electrónico</span>
                </div>
                <div class="info-value">{{ user.email }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">
                  <i class="fas fa-user-tag"></i>
                  <span>Rol del Usuario</span>
                </div>
                <div class="info-value">
                  <span class="role-badge" :class="getRoleClass(user.role)">
                    {{ formatRole(user.role) }}
                  </span>
                </div>
              </div>
              <div class="info-item">
                <div class="info-label">
                  <i class="fas fa-calendar-alt"></i>
                  <span>Último Acceso</span>
                </div>
                <div class="info-value">{{ formatDate(new Date()) }}</div>
              </div>
            </div>
          </div>

          <div class="info-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-cog"></i>
              </div>
              <div class="card-title">
                <h3>Configuración</h3>
                <p>Ajustes de tu cuenta</p>
              </div>
            </div>
            <div class="card-content">
              <div class="setting-item">
                <div class="setting-info">
                  <i class="fas fa-bell"></i>
                  <div>
                    <span class="setting-name">Notificaciones</span>
                    <span class="setting-desc">Recibir alertas por email</span>
                  </div>
                </div>
                <div class="toggle-switch">
                  <input type="checkbox" id="notifications" checked>
                  <label for="notifications"></label>
                </div>
              </div>
              <div class="setting-item">
                <div class="setting-info">
                  <i class="fas fa-moon"></i>
                  <div>
                    <span class="setting-name">Modo Oscuro</span>
                    <span class="setting-desc">Cambiar tema de la interfaz</span>
                  </div>
                </div>
                <div class="toggle-switch">
                  <input type="checkbox" id="darkMode">
                  <label for="darkMode"></label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="action-section">
          <div class="action-buttons">
            <button class="primary-btn">
              <i class="fas fa-key"></i>
              Cambiar Contraseña
            </button>
            <button class="secondary-btn">
              <i class="fas fa-download"></i>
              Descargar Datos
            </button>
            <button @click="logout" class="danger-btn">
              <i class="fas fa-sign-out-alt"></i>
              Cerrar Sesión
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// La corrección aquí: importa la instancia `apiClient` desde tu archivo de configuración
import apiClient from '../axios'; 

export default {
  name: 'UserProfile',
  data() {
    return {
      user: null,
      loading: false,
      error: null,
      selectedFile: null,
      profileImageUrl: null,
      uploading: false,
    };
  },
  async mounted() {
    await this.loadUserProfile();
  },
  methods: {
    async loadUserProfile() {
      this.loading = true;
      this.error = null;
      const token = localStorage.getItem('access_token');
      if (!token) {
        this.error = 'No estás autenticado.';
        this.loading = false;
        return;
      }

      try {
        // La corrección: Usa `apiClient` en lugar de `api`
        const response = await apiClient.get('/protected'); 
        
        this.user = response.data.logged_in_as;
        this.profileImageUrl = this.user.profile_image_url;
        
      } catch (error) {
        this.error = 'No se pudo cargar la información del usuario.';
        console.error("Error al cargar perfil de usuario:", error);
      } finally {
        this.loading = false;
      }
    },
    onFileSelected(event) {
      const file = event.target.files[0];
      if (file) {
        this.selectedFile = file;
      }
    },
    async uploadProfileImage() {
      if (!this.selectedFile) {
        alert('Por favor, selecciona un archivo.');
        return;
      }
      const formData = new FormData();
      formData.append('file', this.selectedFile);

      try {
        this.uploading = true;
        
        const response = await apiClient.post('/api/upload_image', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        });
        
        console.log('Imagen subida exitosamente:', response.data.url);
        
        // Actualizar el token en localStorage
        localStorage.setItem('access_token', response.data.access_token);
        
        // Actualizar la URL de la imagen en el estado local del componente
        this.profileImageUrl = response.data.url;
        
        alert('Imagen de perfil actualizada exitosamente!');
        this.selectedFile = null;

    } catch (error) {
        console.error('Error al subir imagen:', error);
        alert('Error al subir la imagen. Por favor, inténtalo de nuevo.');
    } finally {
        this.uploading = false;
    }
    },
    async retryLoad() {
      await this.loadUserProfile();
    },
    logout() {
      sessionStorage.removeItem('access_token');
      localStorage.removeItem('access_token');
      this.$router.push('/login');
    },
    getRoleClass(role) {
      const roleClasses = {
        admin: 'role-admin',
        administrator: 'role-admin',
        user: 'role-user',
        usuario: 'role-user',
        moderator: 'role-moderator',
        moderador: 'role-moderator'
      };
      return roleClasses[role?.toLowerCase()] || 'role-default';
    },
    formatRole(role) {
      const roleNames = {
        admin: 'Administrador',
        administrator: 'Administrador',
        user: 'Usuario',
        usuario: 'Usuario',
        moderator: 'Moderador',
        moderador: 'Moderador'
      };
      return roleNames[role?.toLowerCase()] || role || 'Usuario';
    },
    formatDate(date) {
      return new Intl.DateTimeFormat('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    }
  }
};
</script>

<style scoped>
/* Estilos CSS (sin cambios) */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
/* Estilos sin cambios */
* {
  box-sizing: border-box;
}
.user-profile-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.profile-header {
  position: relative;
  background: white;
  margin: 0 40px 40px 40px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
.header-background {
  height: 120px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  position: relative;
}
.header-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.05)"/><circle cx="50" cy="10" r="0.5" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  opacity: 0.3;
}
.header-content {
  display: flex;
  align-items: center;
  padding: 0 40px 30px 40px;
  margin-top: -40px;
  position: relative;
  z-index: 2;
}
.avatar-section {
  position: relative;
  margin-right: 24px;
}
.user-avatar {
  width: 100px;
  height: 100px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 60px;
  color: #667eea;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border: 4px solid white;
}
.profile-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-upload {
  position: absolute;
  bottom: 8px;
  right: 8px;
}
.upload-btn {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}
.upload-btn:hover {
  transform: scale(1.1);
}
.user-title {
  flex: 1;
}
.profile-title {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.profile-subtitle {
  color: #718096;
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}
.profile-content {
  padding: 0 40px 40px 40px;
}
.loading-state {
  background: white;
  border-radius: 20px;
  padding: 60px 40px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
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
.error-state {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
.error-card {
  display: flex;
  align-items: center;
  text-align: left;
}
.error-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #fed7d7, #feb2b2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #e53e3e;
  margin-right: 24px;
  flex-shrink: 0;
}
.error-content {
  flex: 1;
}
.error-title {
  font-size: 20px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 8px 0;
}
.error-message {
  color: #718096;
  margin: 0 0 20px 0;
  line-height: 1.6;
}
.retry-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}
.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}
.user-info-section {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}
.info-card {
  background: white;
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}
.info-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
}
.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f7fafc;
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
  flex: 1;
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
.edit-btn {
  width: 40px;
  height: 40px;
  background: #f7fafc;
  border: none;
  border-radius: 10px;
  color: #718096;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}
.edit-btn:hover {
  background: #667eea;
  color: white;
  transform: scale(1.05);
}
.card-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f7fafc;
}
.info-item:last-child {
  border-bottom: none;
}
.info-label {
  display: flex;
  align-items: center;
  color: #4a5568;
  font-weight: 600;
}
.info-label i {
  margin-right: 12px;
  width: 20px;
  color: #718096;
}
.info-value {
  color: #2d3748;
  font-weight: 500;
  text-align: right;
}
.role-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.role-admin {
  background: linear-gradient(135deg, #fed7d7, #feb2b2);
  color: #c53030;
}
.role-user {
  background: linear-gradient(135deg, #bee3f8, #90cdf4);
  color: #2b6cb0;
}
.role-moderator {
  background: linear-gradient(135deg, #d6f5d6, #9ae6b4);
  color: #276749;
}
.role-default {
  background: linear-gradient(135deg, #e2e8f0, #cbd5e0);
  color: #4a5568;
}
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f7fafc;
}
.setting-item:last-child {
  border-bottom: none;
}
.setting-info {
  display: flex;
  align-items: center;
  gap: 16px;
}
.setting-info i {
  width: 20px;
  color: #718096;
}
.setting-info div {
  display: flex;
  flex-direction: column;
}
.setting-name {
  color: #2d3748;
  font-weight: 600;
  margin-bottom: 2px;
}
.setting-desc {
  color: #718096;
  font-size: 14px;
}
.toggle-switch {
  position: relative;
}
.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.toggle-switch label {
  display: block;
  width: 52px;
  height: 28px;
  background: #cbd5e0;
  border-radius: 28px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}
.toggle-switch label::before {
  content: '';
  position: absolute;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  background: white;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
.toggle-switch input:checked + label {
  background: linear-gradient(135deg, #667eea, #764ba2);
}
.toggle-switch input:checked + label::before {
  transform: translateX(24px);
}
.action-section {
  background: white;
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}
.action-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.primary-btn, .secondary-btn, .danger-btn {
  padding: 16px 32px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
  flex: 1;
  min-width: 180px;
  justify-content: center;
}
.primary-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}
.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}
.secondary-btn {
  background: #f7fafc;
  color: #4a5568;
  border: 2px solid #e2e8f0;
}
.secondary-btn:hover {
  background: #edf2f7;
  border-color: #cbd5e0;
  transform: translateY(-2px);
}
.danger-btn {
  background: linear-gradient(135deg, #e53e3e, #c53030);
  color: white;
  box-shadow: 0 4px 15px rgba(229, 62, 62, 0.3);
}
.danger-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(229, 62, 62, 0.4);
}
@media (max-width: 768px) {
  .user-profile-container {
    padding: 0;
  }
  .profile-header {
    margin: 0 20px 24px 20px;
    border-radius: 16px;
  }
  .header-content {
    padding: 0 24px 24px 24px;
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  .user-avatar {
    width: 80px;
    height: 80px;
    font-size: 48px;
  }
  .profile-content {
    padding: 0 20px 40px 20px;
  }
  .info-cards {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .info-card {
    padding: 24px;
  }
  .action-buttons {
    flex-direction: column;
  }
  .primary-btn, .secondary-btn, .danger-btn {
    min-width: auto;
    width: 100%;
  }
  .card-header {
    flex-wrap: wrap;
    gap: 12px;
  }
  .edit-btn {
    order: -1;
    margin-left: auto;
  }
}
@media (max-width: 480px) {
  .profile-header {
    margin: 0 12px 16px 12px;
  }
  .profile-content {
    padding: 0 12px 24px 12px;
  }
  .info-card {
    padding: 20px;
    border-radius: 16px;
  }
  .action-section {
    padding: 24px;
    border-radius: 16px;
  }
  .header-content {
    padding: 0 20px 20px 20px;
  }
  .profile-title {
    font-size: 24px;
  }
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .info-value {
    text-align: left;
    width: 100%;
  }
}
</style>
<template>
  <div class="admin-dashboard-page dashboard-page">
    <h1 class="dashboard-title">Panel de Administración</h1>
    <p class="dashboard-welcome-message">Bienvenido, **Administrador**. Desde aquí puedes supervisar y gestionar todos los aspectos del sistema, usuarios, roles, productos y configuraciones.</p>
    
    <nav class="dashboard-nav">
      <ul class="dashboard-nav-list">
        <li class="dashboard-nav-item">
          <router-link to="/admin/users" class="dashboard-nav-link">
            <i class="fas fa-users"></i> Gestión de Usuarios
          </router-link>
        </li>
        <li class="dashboard-nav-item">
          <router-link to="/admin/products" class="dashboard-nav-link">
            <i class="fas fa-box-open"></i> Gestión de Productos
          </router-link>
        </li>
        <li class="dashboard-nav-item">
          <router-link to="/admin/roles" class="dashboard-nav-link">
            <i class="fas fa-user-tag"></i> Gestión de Roles
          </router-link>
        </li>
        <li class="dashboard-nav-item">
          <router-link to="/admin/reports" class="dashboard-nav-link">
            <i class="fas fa-chart-line"></i> Reportes Generales
          </router-link>
        </li>
        <li class="dashboard-nav-item">
          <router-link to="/admin/settings" class="dashboard-nav-link">
            <i class="fas fa-cog"></i> Configuración del Sistema
          </router-link>
        </li>
      </ul>
    </nav>
    
    <button @click="logout" class="dashboard-logout-button">Cerrar Sesión</button>
  </div>
</template>

<script>
export default {
  name: 'AdminDashboard',
  methods: {
    logout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_role_id');
      localStorage.removeItem('user_role_name');
      localStorage.removeItem('profile_image_url');
      this.$router.push('/login');
    }
  }
};
</script>

<style scoped>
/* Estilos base compartidos con SalesDashboard */
.dashboard-page {
  padding: 40px;
  text-align: center;
  min-height: calc(100vh - 60px); /* Ajusta según el tamaño de tu header/footer */
  font-family: 'Arial', sans-serif;
}

.dashboard-title {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 2.5em;
  font-weight: 600;
}

.dashboard-welcome-message {
  color: #555;
  margin-bottom: 40px;
  font-size: 1.1em;
  line-height: 1.6;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.dashboard-nav {
  margin-bottom: 50px;
}

.dashboard-nav-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-wrap: wrap; /* Permite que los elementos se ajusten en pantallas pequeñas */
  justify-content: center;
  gap: 20px; /* Espacio entre los elementos de navegación */
}

.dashboard-nav-item {
  margin: 0; /* Elimina el margin default de list-style */
}

.dashboard-nav-link {
  text-decoration: none;
  color: #3498db;
  font-weight: bold;
  padding: 15px 25px;
  border: 2px solid #3498db;
  border-radius: 8px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 10px; /* Espacio entre icono y texto */
  background-color: #ffffff;
}

.dashboard-nav-link:hover {
  background-color: #3498db;
  color: white;
  transform: translateY(-3px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.dashboard-nav-link i {
  font-size: 1.2em;
}

.dashboard-logout-button {
  padding: 12px 25px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1em;
  font-weight: 600;
  transition: background-color 0.3s ease, transform 0.2s ease;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
}

.dashboard-logout-button:hover {
  background-color: #c0392b;
  transform: translateY(-2px);
}

/* Estilos específicos para AdminDashboard */
.admin-dashboard-page {
  background-color: #e8f0f7; /* Un color de fondo ligeramente diferente */
}
/* Puedes añadir más estilos específicos aquí si quieres un look distinto para admin */
</style>
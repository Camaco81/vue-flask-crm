<template>
  <div class="admin-dashboard">
    <h1>Panel de Administración</h1>
    <p>Bienvenido, "Administrador". Desde aquí puedes supervisar y gestionar usuarios, acceder a reportes y configurar el sistema.</p>
    
    <div class="dashboard-buttons">
      <router-link to="/admin/users" class="dashboard-button">Gestión de Usuarios</router-link>
      
      <router-link to="/admin/general-reports" class="dashboard-button">Reportes Generales</router-link>
      
      <router-link to="settings" class="dashboard-button">Configuración del Sistema</router-link>
    </div>

    <button @click="logout" class="logout-button">Cerrar Sesión</button>
  </div>
</template>

<script>
export default {
  name: 'AdminDashboard',
  methods: {
    logout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      this.$router.push('/login');
    }
  }
}
</script>

<style scoped>
/* Tus estilos CSS anteriores para AdminDashboard.vue se mantienen sin cambios */
.admin-dashboard {
  max-width: 900px;
  margin: 50px auto;
  padding: 30px;
  background-color: #f9f9f9;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  text-align: center;
}

h1 {
  color: #333;
  margin-bottom: 20px;
  font-size: 2.5em;
}

p {
  color: #666;
  font-size: 1.1em;
  margin-bottom: 30px;
}

.dashboard-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.dashboard-button {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 1.2em;
  font-weight: bold;
  transition: background-color 0.3s ease, transform 0.2s ease;
  min-height: 80px;
}

.dashboard-button:hover {
  background-color: #0056b3;
  transform: translateY(-3px);
}

.logout-button {
  padding: 12px 25px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1em;
  font-weight: bold;
  transition: background-color 0.3s ease;
}

.logout-button:hover {
  background-color: #c82333;
}
</style>
<template>
  <div class="admin-dashboard-container">
    <div class="dashboard-header">
      <h1 class="page-title">
        <i class="fas fa-chart-line"></i> Panel de Administración
      </h1>
      <p class="welcome-message">
        Bienvenido, Administrador. Tu centro de control para supervisión, finanzas y configuración.
      </p>
    </div>
    
    <div class="dashboard-buttons">
      <router-link to="/admin/users" class="dashboard-card users-link">
        <div class="card-icon"><i class="fas fa-users-cog"></i></div>
        <div class="card-content">
          <h2 class="card-title">Gestión de Usuarios</h2>
          <p class="card-subtitle">Administra roles, permisos y accesos del personal.</p>
        </div>
      </router-link>
      
      <router-link to="/admin/credits-reports" class="dashboard-card credit-link">
        <div class="card-icon"><i class="fas fa-money-check-alt"></i></div>
        <div class="card-content">
          <h2 class="card-title">Monitoreo de Créditos</h2>
          <p class="card-subtitle">Seguimiento a cuentas por cobrar y deudores.</p>
        </div>
      </router-link>
      
      <router-link to="/admin/general-reports" class="dashboard-card reports-link">
        <div class="card-icon"><i class="fas fa-chart-bar"></i></div>
        <div class="card-content">
          <h2 class="card-title">Reportes Generales</h2>
          <p class="card-subtitle">Analiza ventas, inventario y métricas de rendimiento.</p>
        </div>
      </router-link>
      
      <router-link to="/admin/settings" class="dashboard-card settings-link">
        <div class="card-icon"><i class="fas fa-cog"></i></div>
        <div class="card-content">
          <h2 class="card-title">Configuración del Sistema</h2>
          <p class="card-subtitle">Ajusta tasas de cambio, parámetros de stock y seguridad.</p>
        </div>
      </router-link>
    </div>

    <button @click="logout" class="logout-button">
      <i class="fas fa-sign-out-alt"></i> Cerrar Sesión
    </button>
  </div>
</template>

<script>
// Asegúrate de que Font Awesome 5 Free esté instalado y configurado
export default {
  name: 'AdminDashboard',
  methods: {
    logout() {
      // Usar 'confirm' es una buena práctica para seguridad básica
      if (confirm("¿Estás seguro que deseas cerrar la sesión?")) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_info');
          // Redirige al usuario al login
          this.$router.push('/login');
      }
    }
  }
}
</script>

<style scoped>
/* GENERAL BASE */
.admin-dashboard-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 30px;
  background-color: #f0f4f8; /* Fondo suave */
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  font-family: 'Inter', sans-serif;
}

/* HEADER Y TÍTULOS */
.dashboard-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 2.8em;
  font-weight: 800;
  color: #1e3a8a; /* Azul oscuro corporativo */
  margin-bottom: 10px;
}

.page-title i {
  margin-right: 10px;
  color: #4f46e5;
}

.welcome-message {
  color: #6b7280;
  font-size: 1.1em;
  max-width: 700px;
  margin: 0 auto;
}

/* GRUPO DE BOTONES/TARJETAS (UI/UX DINÁMICA) */
.dashboard-buttons {
  display: grid;
  /* Layout responsivo: 2 columnas en desktop, 1 en móvil */
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 30px;
  margin-bottom: 50px;
}

.dashboard-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 30px;
  background-color: white;
  border-radius: 15px;
  text-decoration: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  border-bottom: 5px solid transparent; /* Base para el efecto de color */
}

/* EFECTO HOVER */
.dashboard-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 3em;
  margin-bottom: 15px;
  width: 70px;
  height: 70px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: 1.4em;
  font-weight: 700;
  color: #333;
  margin-bottom: 5px;
}

.card-subtitle {
  color: #777;
  font-size: 0.95em;
  line-height: 1.4;
}

/* COLORES ESPECÍFICOS POR TAREA */
/* 1. Usuarios (General/Config) */
.users-link .card-icon {
  background: linear-gradient(45deg, #3b82f6, #1d4ed8);
}
.users-link:hover {
  border-bottom-color: #3b82f6;
}

/* 2. Créditos (Finanzas/Alerta) */
.credit-link .card-icon {
  background: linear-gradient(45deg, #ef4444, #b91c1c); /* Rojo de advertencia/finanzas */
}
.credit-link:hover {
  border-bottom-color: #ef4444;
}

/* 3. Reportes (Análisis) */
.reports-link .card-icon {
  background: linear-gradient(45deg, #10b981, #059669); /* Verde de éxito/crecimiento */
}
.reports-link:hover {
  border-bottom-color: #10b981;
}

/* 4. Configuración (Sistema) */
.settings-link .card-icon {
  background: linear-gradient(45deg, #f59e0b, #d97706); /* Amarillo/naranja de configuración */
}
.settings-link:hover {
  border-bottom-color: #f59e0b;
}

/* BOTÓN DE CERRAR SESIÓN */
.logout-button {
  padding: 12px 30px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 1.1em;
  font-weight: 600;
  transition: background-color 0.3s ease, transform 0.2s;
  box-shadow: 0 4px 10px rgba(220, 53, 69, 0.3);
  margin-top: 20px;
}

.logout-button i {
  margin-right: 8px;
}

.logout-button:hover {
  background-color: #c82333;
  transform: translateY(-2px);
}

/* RESPONSIVE */
@media (max-width: 768px) {
  .admin-dashboard-container {
    padding: 20px;
    margin: 20px;
  }
  
  .page-title {
    font-size: 2.2em;
  }
  
  .dashboard-buttons {
    grid-template-columns: 1fr; /* Una sola columna en móvil */
  }
  
  .dashboard-card {
    flex-direction: row; /* Diseño horizontal en móvil */
    text-align: left;
    padding: 20px;
  }
  
  .card-icon {
    margin-right: 15px;
    margin-bottom: 0;
    flex-shrink: 0;
  }
  
  .logout-button {
    width: 100%;
  }
}
</style>
<template>
  <div class="almacenista-dashboard">
    <div class="welcome-card">
      <div class="header-content">
        <h1 class="title">👋 Bienvenido, Almacenista</h1>
        <NotificationBell class="notification-bell-icon" />
      </div>

      <p class="subtitle">Tu función es mantener el inventario al día.</p>
      
      <div class="action-section">
        <h3>Tu Tarea Principal:</h3>
        
        <router-link to="/almacenista/inventory" class="btn-action btn-primary">
          <i class="fas fa-boxes"></i> Gestionar Productos e Inventario
        </router-link>
        
        <router-link to="/almacenista/notifications" class="btn-action btn-secondary-action">
          <i class="fas fa-list-alt"></i> Ver Historial de Alertas
        </router-link>

        <button @click="logout" class="btn-action btn-warning">
          <i class="fas fa-sign-out-alt"></i> Cerrar Sesión
        </button>
      </div>

      <div class="info-note">
        <i class="fas fa-info-circle"></i>
        <p>Desde aquí podrás registrar, editar y eliminar productos del sistema.</p>
      </div>
    </div>
  </div>
</template>

<script>
import NotificationBell from './NotificationBell.vue';

export default {
  name: 'AlmacenistaDashboard',
  components: {
    NotificationBell
  },
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
/* Estilos existentes */
.almacenista-dashboard {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  background-color: #f0f4f8; 
}

.welcome-card {
  background: white;
  border-radius: 12px;
  padding: 30px 40px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 550px; /* Un poco más ancho */
  width: 90%;
  /* 🟢 Necesario para posicionar la campana si estuviera fuera del flujo, 
     pero en este caso es solo para contener el flexbox del header. */
}

.title {
  color: #38a169;
  font-size: 2.2rem;
  font-weight: 700;
  margin: 0; /* Asegura que no haya margen */
}

.subtitle {
  color: #718096;
  font-size: 1.1rem;
  margin-top: 0.5rem;
  margin-bottom: 2.5rem; /* Más espacio después del subtítulo */
}

/* 🟢 AJUSTE ESTÉTICO: CONTENEDOR DE LA CAMPANA */
.header-content {
    display: flex;
    justify-content: space-between; 
    align-items: center;
    margin-bottom: 0.5rem;
}

.notification-bell-icon {
    /* Dar un poco más de relevancia visual a la campana */
    font-size: 1.5rem; 
    cursor: pointer;
    /* Ajusta la alineación vertical con el título */
    padding-top: 5px; 
}


/* 🟢 AJUSTE ESTÉTICO: BOTONES DE ACCIÓN */
.action-section {
  display: flex; 
  flex-direction: column;
  gap: 12px; /* Reducido ligeramente el espacio para compactar */
  align-items: center;
}

.action-section h3 {
  color: #4a5568;
  margin-bottom: 10px; 
  font-size: 1.4rem;
}

.btn-action {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    padding: 15px 30px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1.1rem;
    transition: background-color 0.3s, transform 0.1s, box-shadow 0.3s;
    width: 100%;
    max-width: 350px; /* Aumentado ligeramente el ancho máximo de los botones */
    justify-content: center;
}

/* 1. Botón Principal (Gestionar Inventario) - Verde/Éxito */
.btn-primary {
  background-color: #38a169; 
  color: white;
  box-shadow: 0 4px 10px rgba(56, 161, 105, 0.3);
}

.btn-primary:hover {
  background-color: #2f855a;
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(56, 161, 105, 0.4);
}

/* 2. Botón Funcional Secundario (Historial de Alertas) - Azul/Informativo */
.btn-secondary-action {
  background: none;
  border: 2px solid #4299e1; /* Borde azul */
  color: #4299e1; /* Texto azul */
  padding: 13px 30px; /* Ajuste de padding para compensar el borde */
}

.btn-secondary-action:hover {
  background-color: #4299e1;
  color: white;
  transform: translateY(-1px);
}

/* 3. Botón de Advertencia (Cerrar Sesión) - Rojo/Peligro */
.btn-warning {
  background: none;
  border: 2px solid #e53e3e; /* Borde rojo */
  color: #e53e3e; /* Texto rojo */
  padding: 13px 30px; /* Ajuste de padding para compensar el borde */
  cursor: pointer;
}

.btn-warning:hover {
  background-color: #e53e3e;
  color: white;
  transform: translateY(-1px);
}


/* Nota Informativa (Sin cambios) */
.info-note {
  margin-top: 2rem;
  padding: 15px;
  background-color: #e6fffa;
  border: 1px solid #b2f5ea;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 15px;
  text-align: left;
}

.info-note i {
  color: #38a169;
  font-size: 1.5rem;
}

.info-note p {
  margin: 0;
  color: #4a5568;
  font-size: 0.95rem;
}
</style>
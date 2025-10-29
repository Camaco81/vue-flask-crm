<template>
  <div class="almacenista-dashboard">
    <div class="welcome-card">
      <h1 class="title">👋 Bienvenido, Almacenista</h1>
      <p class="subtitle">Tu función es mantener el inventario al día.</p>
      
      <div class="action-section">
        <h3>Tu Tarea Principal:</h3>
        <router-link to="/almacenista/inventory" class="btn-primary">
          <i class="fas fa-boxes"></i> Gestionar Productos e Inventario
        </router-link>
        
        <button @click="logout" class="btn-secondary logout-btn">
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
// Componente de Almacenista Dashboard
export default {
  name: 'AlmacenistaDashboard',
  methods: {
    // 🚨 Lógica de Cierre de Sesión 🚨
    logout() {
      // Limpia los tokens de autenticación
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info'); 
      // Redirige al usuario a la página de login
      this.$router.push('/login');
    }
  }
}
</script>

<style scoped>
/* Estilos sencillos y limpios */
.almacenista-dashboard {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  background-color: #f0f4f8; /* Fondo suave */
}

.welcome-card {
  background: white;
  border-radius: 12px;
  padding: 30px 40px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 500px;
  width: 90%;
}

.title {
  color: #38a169; /* Verde (asociado a inventario/stock) */
  font-size: 2.2rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.subtitle {
  color: #718096;
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

.action-section {
  display: flex; /* Para organizar los botones verticalmente */
  flex-direction: column;
  gap: 15px; /* Espacio entre los botones */
  align-items: center;
}

.action-section h3 {
  color: #4a5568;
  margin-bottom: 5px; /* Reducido el margen para acercar a los botones */
  font-size: 1.4rem;
}

/* Estilo del botón principal (Gestionar Inventario) */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background-color: #38a169;
  color: white;
  text-decoration: none;
  padding: 15px 30px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1.1rem;
  transition: background-color 0.3s, transform 0.1s;
  box-shadow: 0 4px 10px rgba(56, 161, 105, 0.3);
  width: 100%; /* Ocupa el ancho completo de la sección de acción */
  max-width: 300px; /* Limita el ancho para que no sea gigante */
  justify-content: center;
}

.btn-primary:hover {
  background-color: #2f855a;
  transform: translateY(-2px);
}

/* 🚨 Estilo del botón Cerrar Sesión (Secundario) 🚨 */
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: 2px solid #e53e3e; /* Borde rojo */
  color: #e53e3e; /* Texto rojo */
  padding: 12px 30px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
  max-width: 300px; 
  justify-content: center;
}

.btn-secondary:hover {
  background-color: #e53e3e;
  color: white;
  transform: translateY(-1px);
}

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
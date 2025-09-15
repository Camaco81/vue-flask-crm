<template>
  <div id="app">
    <nav class="main-nav">
      <router-link to="/" class="nav-brand"></router-link>
      <div class="nav-links">
        <router-link v-if="!isAuthenticated" to="/login" class="nav-link"></router-link>
        <router-link v-if="!isAuthenticated" to="/register" class="nav-link"></router-link>
        
        <router-link v-if="isAuthenticated" to="/dashboard" class="nav-link"></router-link>
        <router-link v-if="isAuthenticated" to="/customers" class="nav-link"></router-link>
        <router-link v-if="isAuthenticated" to="/products" class="nav-link"></router-link>
        <router-link v-if="isAuthenticated" to="/profile" class="nav-link"></router-link>
     
      </div>
    </nav>
    <div class="content">
      <router-view/>
    </div>
  </div>
</template>

<script>
export default {
  computed: {
    isAuthenticated() {
      // Verifica si el token existe en el localStorage
      return !!localStorage.getItem('access_token');
    }
  },
  methods: {
    logout() {
      // Lógica de cierre de sesión para limpiar el token y redirigir
      localStorage.removeItem('access_token');
      this.$router.push('/login');
    }
  }
};
</script>

<style>
/* Estilos generales */
body {
  margin: 0;
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}



.nav-brand {
  font-weight: bold;
  color: #ecf0f1;
  text-decoration: none;
  font-size: 1.5rem;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav-link {
  color: #ecf0f1;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}

.nav-link:hover {
  color: #f1c40f;
}

.logout-btn {
  background-color: transparent;
  border: 2px solid #e74c3c;
  color: #e74c3c;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s, color 0.3s;
}

.logout-btn:hover {
  background-color: #e74c3c;
  color: white;
}

.content {
  padding: 2rem;
}

.router-link-active {
  color: #f1c40f;
}
</style>
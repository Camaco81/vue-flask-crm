<template>
  <div>
    <div v-if="!isLoggedIn">
      <h1>Bienvenido a la página principal</h1>
      <p>
        Por favor,
        <router-link to="/login">inicia sesión</router-link>
        o
        <router-link to="/register">regístrate</router-link>
        para continuar.
      </p>
    </div>
    <div v-else>
      <HomeDashboard />
    </div>
  </div>
</template>

<script>
import HomeDashboard from '../components/vendedor/VendedorDashboard.vue';
import { ref, onMounted, onUnmounted } from 'vue';

export default {
  components: {
    HomeDashboard
  },
  setup() {
    const isLoggedIn = ref(false);
    const checkAuth = () => {
      isLoggedIn.value = !!localStorage.getItem('access_token');
    };

    onMounted(() => {
      checkAuth();
      window.addEventListener('storage', checkAuth);
    });

    onUnmounted(() => {
      window.removeEventListener('storage', checkAuth);
    });

    return {
      isLoggedIn
    };
  }
};
</script>
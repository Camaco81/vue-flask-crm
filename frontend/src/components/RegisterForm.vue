<template>
  <form @submit.prevent="register">
    <h2>Registro de Usuario</h2>
    <input type="email" v-model="email" placeholder="Email" required />
    <input type="password" v-model="password" placeholder="Contraseña" required />
    <button type="submit">Registrarse</button>
  </form>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      email: '',
      password: ''
    };
  },
  methods: {
    async register() {
      try {
        await axios.post('http://localhost:5000/register', {
          email: this.email,
          password: this.password
        });
        alert('Registro exitoso. ¡Ahora puedes iniciar sesión!');
        this.$router.push('/login');
      } catch (error) {
        console.error('Error de registro:', error);
        alert('Error en el registro. Este email podría ya estar en uso.');
      }
    }
  }
};
</script>
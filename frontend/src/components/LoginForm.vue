<template>
  <div class="login-container">
    <div class="login-card">
      <h2>Inicia Sesión</h2>
      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <input 
            type="email" 
            v-model="email" 
            placeholder="Email" 
            required 
            class="form-control"
          />
        </div>
        <div class="form-group">
          <input 
            type="password" 
            v-model="password" 
            placeholder="Contraseña" 
            required 
            class="form-control"
          />
        </div>
        <button type="submit" class="btn btn-primary">Acceder</button>
        <p v-if="error" class="error-message">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      email: '',
      password: '',
      error: ''
    };
  },
  methods: {
    async login() {
      this.error = '';
      try {
        const response = await axios.post('http://localhost:5000/login', {
          email: this.email,
          password: this.password
        });
        
        localStorage.setItem('access_token', response.data.access_token);
        this.$router.push('/HomeDashboard');
        
      } catch (error) {
        if (error.response && error.response.data && error.response.data.msg) {
          this.error = error.response.data.msg;
        } else {
          this.error = 'Error al iniciar sesión. Intenta de nuevo.';
        }
      }
    }
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  text-align: center;
}

h2 {
  font-size: 2.2rem;
  margin-bottom: 25px;
  color: #333;
}

.login-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 20px;
}

.form-control {
  width: 100%;
  padding: 12px 15px;
  font-size: 1rem;
  border: 1px solid #ddd;
  border-radius: 5px;
  transition: border-color 0.3s, box-shadow 0.3s;
  box-sizing: border-box; /* Asegura que el padding no afecte el ancho */
}

.form-control:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
  outline: none;
}

.btn {
  padding: 12px 20px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  border: none;
  border-radius: 5px;
  transition: background-color 0.3s, transform 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: #ffffff;
}

.btn-primary:hover {
  background-color: #0056b3;
  transform: translateY(-2px);
}

.error-message {
  margin-top: 15px;
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 10px;
  border-radius: 5px;
}
</style>
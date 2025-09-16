<template>
  <div class="login-container">
    <div class="background-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
    
    <div class="login-card">
      <div class="brand-section">
        <div class="logo">
          <div class="logo-icon">🔐</div>
        </div>
        <h2>Bienvenido de vuelta</h2>
        <p class="subtitle">Accede a tu cuenta para continuar</p>
      </div>
      
      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <div class="input-wrapper">
            <span class="input-icon">📧</span>
            <input 
              type="email"
              v-model="email"
              placeholder="Ingresa tu email"
              required
              class="form-control"
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input 
              type="password"
              v-model="password"
              placeholder="Ingresa tu contraseña"
              required
              class="form-control"
            />
          </div>
        </div>
        
        <button type="submit" class="btn btn-primary">Iniciar Sesión</button>
        
        <div v-if="error" class="error-message">
          <span class="error-icon">⚠️</span>
          {{ error }}
        </div>
        
        <div class="register-link">
          <p>¿No tienes una cuenta? 
            <router-link to="/register" class="register-btn">
              Regístrate aquí
            </router-link>
          </p>
        </div>
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
        this.$router.push('/dashboard');
        
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
/* Estilos extraídos del diseño original que te gustó */
* {
  box-sizing: border-box;
}

.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  animation: float 6s ease-in-out infinite;
}

.circle-1 {
  width: 200px;
  height: 200px;
  top: -50px;
  left: -50px;
  animation-delay: 0s;
}

.circle-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: -75px;
  animation-delay: 2s;
}

.circle-3 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 10%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 45px 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.brand-section {
  text-align: center;
  margin-bottom: 35px;
}

.logo {
  margin-bottom: 20px;
}

.logo-icon {
  font-size: 3rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}

h2 {
  font-size: 2.4rem;
  margin-bottom: 8px;
  color: #2d3748;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.subtitle {
  color: #718096;
  font-size: 1rem;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 24px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 15px;
  z-index: 2;
  font-size: 1.1rem;
  color: #a0aec0;
}

.form-control {
  width: 100%;
  padding: 16px 20px 16px 50px;
  font-size: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.3s ease;
  background-color: #f8fafc;
  color: #2d3748;
}

.form-control:focus {
  border-color: #667eea;
  background-color: #ffffff;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  outline: none;
  transform: translateY(-1px);
}

.btn {
  padding: 16px 24px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  border-radius: 12px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  position: relative;
  overflow: hidden;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  margin-bottom: 20px;
  width: 100%; /* Aseguramos que el botón ocupe todo el ancho */
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 15px;
  padding: 12px 16px;
  color: #e53e3e;
  background: linear-gradient(135deg, #fed7d7, #fbb6b6);
  border: 1px solid #feb2b2;
  border-radius: 8px;
  font-size: 0.9rem;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.register-link {
  text-align: center;
  margin-top: 20px;
}

.register-link p {
  color: #718096;
  margin: 0;
  font-size: 0.95rem;
}

.register-btn {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.register-btn:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* Responsive design */
@media (max-width: 480px) {
  .login-card {
    padding: 35px 25px;
    margin: 10px;
  }
  
  h2 {
    font-size: 2rem;
  }
  
  .form-control {
    padding: 14px 18px 14px 45px;
  }
  
  .btn {
    padding: 14px 20px;
  }
}
</style>
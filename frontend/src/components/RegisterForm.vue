<template>
  <div class="register-container">
    <div class="background-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
    
    <div class="register-card">
      <div class="brand-section">
        <div class="logo">
          <div class="logo-icon">🚀</div>
        </div>
        <h2>Crea tu cuenta</h2>
        <p class="subtitle">Únete a nosotros y comienza tu experiencia</p>
      </div>
      
      <form @submit.prevent="register" class="register-form">
        <div class="form-group">
          <div class="input-wrapper">
            <span class="input-icon">👤</span>
            <input 
              type="text"
              v-model="name"
              placeholder="Nombre completo"
              required
              class="form-control"
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <span class="input-icon">📧</span>
            <input 
              type="email"
              v-model="email"
              placeholder="Ingresa tu email"
              required
              class="form-control"
              :class="{ 'error': emailError }"
            />
          </div>
          <div v-if="emailError" class="field-error">{{ emailError }}</div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input 
              :type="showPassword ? 'text' : 'password'"
              v-model="password"
              placeholder="Crea una contraseña"
              required
              class="form-control"
              :class="{ 'error': passwordError }"
              @input="validatePassword"
            />
            <button 
              type="button" 
              @click="showPassword = !showPassword"
              class="password-toggle"
            >
              {{ showPassword ? '👁️' : '👁️‍🗨️' }}
            </button>
          </div>
          <div v-if="passwordError" class="field-error">{{ passwordError }}</div>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <span class="input-icon">🔐</span>
            <input 
              :type="showConfirmPassword ? 'text' : 'password'"
              v-model="confirmPassword"
              placeholder="Confirma tu contraseña"
              required
              class="form-control"
              :class="{ 'error': confirmPasswordError }"
              @input="validateConfirmPassword"
            />
            <button 
              type="button" 
              @click="showConfirmPassword = !showConfirmPassword"
              class="password-toggle"
            >
              {{ showConfirmPassword ? '👁️' : '👁️‍🗨️' }}
            </button>
          </div>
          <div v-if="confirmPasswordError" class="field-error">{{ confirmPasswordError }}</div>
        </div>
        
        <!-- Password Strength Indicator -->
        <div v-if="password" class="password-strength">
          <div class="strength-label">Fortaleza de contraseña:</div>
          <div class="strength-bar">
            <div 
              class="strength-fill" 
              :class="passwordStrength.class"
              :style="{ width: passwordStrength.width }"
            ></div>
          </div>
          <span class="strength-text" :class="passwordStrength.class">
            {{ passwordStrength.text }}
          </span>
        </div>
        
        <div class="form-options">
          <label class="terms-checkbox">
            <input type="checkbox" v-model="acceptTerms" required>
            <span class="checkmark"></span>
            Acepto los 
            <a href="#" class="terms-link">Términos y Condiciones</a> 
            y la 
            <a href="#" class="terms-link">Política de Privacidad</a>
          </label>
        </div>
        
        <button type="submit" class="btn btn-primary" :disabled="isLoading || !isFormValid">
          <span v-if="!isLoading">Crear Cuenta</span>
          <span v-else class="loading">
            <div class="spinner"></div>
            Creando cuenta...
          </span>
        </button>
        
        <div v-if="error" class="error-message">
          <span class="error-icon">⚠️</span>
          {{ error }}
        </div>
        
        <div v-if="successMessage" class="success-message">
          <span class="success-icon">✅</span>
          {{ successMessage }}
        </div>
        
        <!-- <div class="divider">
          <span>o</span>
        </div>
        
        <div class="social-login">
          <button type="button" class="btn btn-google">
            <span class="social-icon">🔍</span>
            Regístrate con Google
          </button>
        </div> -->
        
        <div class="login-link">
          <p>¿Ya tienes una cuenta? 
            <router-link to="/login" class="login-btn">
              Inicia sesión aquí
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
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      error: '',
      successMessage: '',
      showPassword: false,
      showConfirmPassword: false,
      acceptTerms: false,
      isLoading: false,
      emailError: '',
      passwordError: '',
      confirmPasswordError: ''
    };
  },
  computed: {
    isFormValid() {
      return this.name && 
             this.email && 
             this.password && 
             this.confirmPassword &&
             this.acceptTerms &&
             !this.emailError &&
             !this.passwordError &&
             !this.confirmPasswordError;
    },
    
    passwordStrength() {
      if (!this.password) return { width: '0%', class: '', text: '' };
      
      let score = 0;
      let checks = [];
      
      // Length check
      if (this.password.length >= 8) {
        score += 1;
        checks.push('8+ caracteres');
      }
      
      // Uppercase check
      if (/[A-Z]/.test(this.password)) {
        score += 1;
        checks.push('Mayúscula');
      }
      
      // Lowercase check
      if (/[a-z]/.test(this.password)) {
        score += 1;
        checks.push('Minúscula');
      }
      
      // Number check
      if (/[0-9]/.test(this.password)) {
        score += 1;
        checks.push('Número');
      }
      
      // Special character check
      if (/[^A-Za-z0-9]/.test(this.password)) {
        score += 1;
        checks.push('Símbolo');
      }
      
      if (score <= 2) {
        return { width: '33%', class: 'weak', text: 'Débil' };
      } else if (score <= 3) {
        return { width: '66%', class: 'medium', text: 'Media' };
      } else {
        return { width: '100%', class: 'strong', text: 'Fuerte' };
      }
    }
  },
  
  methods: {
    validateEmail() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.email)) {
        this.emailError = 'Email no válido';
      } else {
        this.emailError = '';
      }
    },
    
    validatePassword() {
      if (this.password.length < 8) {
        this.passwordError = 'La contraseña debe tener al menos 8 caracteres';
      } else {
        this.passwordError = '';
      }
      this.validateConfirmPassword();
    },
    
    validateConfirmPassword() {
      if (this.confirmPassword && this.password !== this.confirmPassword) {
        this.confirmPasswordError = 'Las contraseñas no coinciden';
      } else {
        this.confirmPasswordError = '';
      }
    },
    
    async register() {
      this.error = '';
      this.successMessage = '';
      this.isLoading = true;
      
      // Validate email
      this.validateEmail();
      
      // Validate passwords
      this.validatePassword();
      this.validateConfirmPassword();
      
      if (!this.isFormValid) {
        this.isLoading = false;
        return;
      }
      
      try {
        await axios.post('http://localhost:5000/register', {
          name: this.name,
          email: this.email,
          password: this.password
        });
        
        this.successMessage = '¡Registro exitoso! Redirigiendo al inicio de sesión...';
        
        setTimeout(() => {
          this.$router.push('/login');
        }, 2000);
        
      } catch (error) {
        console.error('Error de registro:', error);
        if (error.response && error.response.data && error.response.data.msg) {
          this.error = error.response.data.msg;
        } else if (error.response && error.response.status === 400) {
          this.error = 'Este email ya está registrado. Intenta con otro email.';
        } else {
          this.error = 'Error en el registro. Por favor, intenta de nuevo.';
        }
      } finally {
        this.isLoading = false;
      }
    }
  },
  
  watch: {
    email() {
      if (this.emailError) {
        this.validateEmail();
      }
    }
  }
};
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.register-container {
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
  right: -50px;
  animation-delay: 0s;
}

.circle-2 {
  width: 150px;
  height: 150px;
  top: 40%;
  left: -75px;
  animation-delay: 2s;
}

.circle-3 {
  width: 120px;
  height: 120px;
  bottom: 10%;
  right: 15%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

.register-card {
  width: 100%;
  max-width: 450px;
  padding: 45px 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-height: 90vh;
  overflow-y: auto;
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

.register-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 20px;
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

.form-control.error {
  border-color: #e53e3e;
  background-color: #fef5f5;
}

.field-error {
  color: #e53e3e;
  font-size: 0.85rem;
  margin-top: 5px;
  margin-left: 15px;
}

.password-toggle {
  position: absolute;
  right: 15px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  color: #a0aec0;
  transition: color 0.3s ease;
  z-index: 2;
  padding: 5px;
}

.password-toggle:hover {
  color: #667eea;
}

.password-strength {
  margin-top: 10px;
  padding: 0 15px;
}

.strength-label {
  font-size: 0.85rem;
  color: #4a5568;
  margin-bottom: 8px;
}

.strength-bar {
  width: 100%;
  height: 6px;
  background-color: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 5px;
}

.strength-fill {
  height: 100%;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.strength-fill.weak {
  background-color: #e53e3e;
}

.strength-fill.medium {
  background-color: #dd6b20;
}

.strength-fill.strong {
  background-color: #38a169;
}

.strength-text {
  font-size: 0.8rem;
  font-weight: 600;
}

.strength-text.weak { color: #e53e3e; }
.strength-text.medium { color: #dd6b20; }
.strength-text.strong { color: #38a169; }

.form-options {
  margin-bottom: 28px;
}

.terms-checkbox {
  display: flex;
  align-items: flex-start;
  cursor: pointer;
  color: #4a5568;
  font-size: 0.9rem;
  line-height: 1.4;
  user-select: none;
}

.terms-checkbox input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 18px;
  height: 18px;
  border: 2px solid #cbd5e0;
  border-radius: 4px;
  margin-right: 12px;
  margin-top: 2px;
  position: relative;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.terms-checkbox input:checked + .checkmark {
  background-color: #667eea;
  border-color: #667eea;
}

.terms-checkbox input:checked + .checkmark::after {
  content: '✓';
  position: absolute;
  top: -2px;
  left: 2px;
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.terms-link {
  color: #667eea;
  text-decoration: none;
  transition: color 0.3s ease;
}

.terms-link:hover {
  color: #764ba2;
  text-decoration: underline;
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
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid #ffffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  padding: 12px 16px;
  color: #e53e3e;
  background: linear-gradient(135deg, #fed7d7, #fbb6b6);
  border: 1px solid #feb2b2;
  border-radius: 8px;
  font-size: 0.9rem;
  animation: slideIn 0.3s ease;
}

.success-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  padding: 12px 16px;
  color: #38a169;
  background: linear-gradient(135deg, #c6f6d5, #9ae6b4);
  border: 1px solid #9ae6b4;
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

.divider {
  text-align: center;
  margin: 25px 0;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e2e8f0;
}

.divider span {
  background: rgba(255, 255, 255, 0.95);
  padding: 0 15px;
  color: #a0aec0;
  font-size: 0.9rem;
  position: relative;
}

.social-login {
  margin-bottom: 25px;
}

.btn-google {
  width: 100%;
  background: #ffffff;
  color: #4a5568;
  border: 2px solid #e2e8f0;
  gap: 12px;
}

.btn-google:hover {
  background: #f8fafc;
  border-color: #cbd5e0;
  transform: translateY(-1px);
}

.social-icon {
  font-size: 1.2rem;
}

.login-link {
  text-align: center;
  margin-top: 20px;
}

.login-link p {
  color: #718096;
  margin: 0;
  font-size: 0.95rem;
}

.login-btn {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.login-btn:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* Responsive design */
@media (max-width: 480px) {
  .register-card {
    padding: 30px 20px;
    margin: 10px;
    max-height: 95vh;
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
  
  .terms-checkbox {
    font-size: 0.85rem;
  }
}

/* Scrollbar styling for webkit browsers */
.register-card::-webkit-scrollbar {
  width: 6px;
}

.register-card::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.register-card::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.register-card::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}
</style>
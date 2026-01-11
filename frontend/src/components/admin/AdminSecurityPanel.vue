<template>
  <div class="admin-panel-container">
    <button @click="goBack" class="back-btn">
        <i class="fas fa-arrow-left">⬅️</i>
      </button>
    <h1 class="page-title">Panel de Administración de Seguridad</h1>
    <!-- <BackButton /> -->

    <div class="card security-card">
      <h2 class="card-header">
        <i class="fas fa-key"></i> Código de Autorización Diario
      </h2>

      <div class="card-content">
        <p class="description">
          Este código de 6 dígitos es requerido por los vendedores para autorizar cualquier **venta a crédito**. 
          El código cambia automáticamente a medianoche (hora del servidor) y solo debe ser visible para los administradores.
        </p>

        <div class="code-display-area">
          <button @click="fetchDailyCode" :disabled="isLoading" class="fetch-btn">
            <span v-if="isLoading">Cargando Código... <i class="fas fa-spinner fa-spin"></i></span>
            <span v-else>Obtener Código Actual</span>
          </button>
          
          <div v-if="securityCode" class="code-result">
            <span class="code-label">CÓDIGO DE HOY ({{ codeDate }})</span>
            <div class="code-value">
              <span class="code-number">{{ securityCode }}</span>
              <button @click="copyCode" class="copy-btn" title="Copiar al portapapeles">
                <i class="fas" :class="[copied ? 'fa-check' : 'fa-copy']"></i>
              </button>
            </div>
            <p v-if="copied" class="copy-message">¡Copiado!</p>
          </div>

          <div v-if="errorMessage" class="alert-box error-alert">
            <p><i class="fas fa-times-circle"></i> {{ errorMessage }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import apiClient from '../../axios';
export default {
  // components: { BackButton }, 
  data() {
    return {
      securityCode: null,
      codeDate: null,
      isLoading: false,
      copied: false,
      errorMessage: null,
    };
  },
  
  methods: {
     goBack() {
      this.$router.go(-1);
    },
    
    
    async fetchDailyCode() {
        this.isLoading = true;
        this.errorMessage = null;
        this.securityCode = null;

        try {
            // 💡 PASO 2: Usar apiClient.get para asegurar autenticación y URL base
            // Axios usa .get, y la respuesta JSON viene directamente en response.data
            const response = await apiClient.get('/api/sales/admin/security-code');

            // Axios maneja automáticamente la verificación de respuesta (no necesitas response.ok)
            // y deserializa el JSON en response.data
            this.securityCode = response.data.security_code;
            this.codeDate = response.data.date;
            
            // Si el interceptor maneja 401, aquí solo llegan errores de red o 403 (Permiso denegado)
        } catch (error) {
            console.error('Error al solicitar código:', error);
            
            // Acceder al mensaje de error específico del backend (si existe)
            const msg = error.response?.data?.msg || 'Error de conexión con el servidor o permiso denegado.';
            this.errorMessage = msg;

            // En caso de 403, el backend debe haber devuelto un mensaje claro
            if (error.response && error.response.status === 403) {
                this.errorMessage = 'Permiso denegado. Solo administradores pueden obtener el código.';
            }

        } finally {
            this.isLoading = false;
        }
    },
    
    copyCode() {
        if (!this.securityCode) return;

        const el = document.createElement('textarea');
        el.value = this.securityCode;
        document.body.appendChild(el);
        el.select();
        // Usar execCommand por restricciones de iFrame
        document.execCommand('copy');
        document.body.removeChild(el);

        this.copied = true;
        setTimeout(() => {
          this.copied = false;
        }, 2000);
    }
  }
};
</script>

<style scoped>
.admin-panel-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  color: #333;
  margin-bottom: 20px;
}

.security-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-top: 20px;
}
.back-btn {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  color: #495057;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
  transform: translateX(-3px);
}

.card-header {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  padding: 15px 20px;
  font-size: 1.5em;
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-content {
  padding: 25px;
}

.description {
  color: #555;
  margin-bottom: 30px;
  line-height: 1.6;
}

.code-display-area {
  text-align: center;
}

.fetch-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1em;
  font-weight: bold;
  transition: background 0.3s, transform 0.1s;
  min-width: 250px;
}

.fetch-btn:hover:not(:disabled) {
  background: #1e7e34;
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(40, 167, 69, 0.4);
}

.fetch-btn:disabled {
  background: #a3d9b0;
  cursor: not-allowed;
}

.code-result {
  margin-top: 30px;
  padding: 20px;
  background: #f1f8ff;
  border: 1px solid #cce5ff;
  border-radius: 10px;
}

.code-label {
  display: block;
  font-size: 0.9em;
  color: #007bff;
  font-weight: 600;
  margin-bottom: 5px;
}

.code-value {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
}

.code-number {
  font-size: 2.5em;
  font-weight: 900;
  color: #333;
  letter-spacing: 10px;
  padding: 5px 0;
  background: #fff;
  border: 1px dashed #ced4da;
  padding: 5px 15px;
  border-radius: 5px;
}

.copy-btn {
  background: #6c757d;
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.copy-btn:hover {
  background: #5a6268;
}

.copy-message {
    color: #28a745;
    font-weight: bold;
    margin-top: 10px;
}

.alert-box {
  padding: 15px;
  border-radius: 8px;
  margin-top: 20px;
  text-align: left;
}

.error-alert {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .code-number {
    font-size: 2em;
    letter-spacing: 6px;
  }
}
</style>
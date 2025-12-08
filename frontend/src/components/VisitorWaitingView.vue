<template>
  <div class="visitor-waiting-container">
    <!-- Fondo decorativo -->
    <div class="decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <!-- Tarjeta principal -->
    <div class="visitor-card">
      <!-- Encabezado con ícono -->
      <div class="header">
        <div class="icon-container">
          <i class="fas fa-user-clock"></i>
        </div>
        <h1 class="title">Esperando Asignación de Rol</h1>
        <p class="subtitle">Tu cuenta está en proceso de verificación</p>
      </div>

      <!-- Contenido informativo -->
      <div class="content">
        <!-- Mensaje informativo -->
        <div class="info-message">
          <div class="message-icon">
            <i class="fas fa-info-circle"></i>
          </div>
          <div class="message-content">
            <h3>Estado de tu cuenta</h3>
            <p>
              Has creado tu cuenta exitosamente. Un administrador debe asignarte un rol 
              (Administrador, Vendedor o Almacenista) antes de que puedas acceder al sistema.
            </p>
            <p class="highlight">
              Por favor, espera a que un administrador revise tu solicitud.
              Este proceso puede tomar de 24 a 48 horas hábiles.
            </p>
          </div>
        </div>

        <!-- Pasos del proceso -->
        <div class="process-steps">
          <h2>Proceso de Activación</h2>
          <div class="steps-container">
            <div class="step">
              <div class="step-number active">1</div>
              <div class="step-content">
                <h4>Registro Completado</h4>
                <p>Tu cuenta ha sido creada exitosamente.</p>
              </div>
            </div>
            
            <div class="step-line"></div>
            
            <div class="step">
              <div class="step-number current">2</div>
              <div class="step-content">
                <h4>Revisión en Proceso</h4>
                <p>Administrador verificando información.</p>
              </div>
            </div>
            
            <div class="step-line"></div>
            
            <div class="step">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4>Activación</h4>
                <p>Asignación de rol y acceso al sistema.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Información adicional -->
        <div class="additional-info">
          <div class="info-box">
            <i class="fas fa-envelope"></i>
            <div class="info-content">
              <h4>Notificación por Correo</h4>
              <p>Recibirás un email cuando tu cuenta sea activada.</p>
            </div>
          </div>
          
          <div class="info-box">
            <i class="fas fa-headset"></i>
            <div class="info-content">
              <h4>¿Necesitas Ayuda?</h4>
              <p>Contacta al administrador del sistema para consultas urgentes.</p>
            </div>
          </div>
        </div>

        <!-- Botón de cerrar sesión -->
        <div class="logout-section">
          <button 
            @click="logout" 
            class="btn-logout"
          >
            <i class="fas fa-sign-out-alt"></i>
            Cerrar Sesión
          </button>
          <p class="logout-note">
            Puedes volver a iniciar sesión más tarde para verificar tu estado.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VisitorWaitingView',
  
  methods: {
    logout() {
      try {
        // Limpiar tokens y datos de usuario
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('userEmail');
        
        // Redirigir a login
        this.$router.push('/login');
        
      } catch (error) {
        console.error('Error al cerrar sesión:', error);
        // Forzar redirección de todas formas
        window.location.href = '/login';
      }
    }
  }
};
</script>

<style scoped>
.visitor-waiting-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.decoration {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -150px;
  right: -150px;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -100px;
  left: -100px;
}

.circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  left: 10%;
}

.visitor-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 700px;
  overflow: hidden;
  z-index: 10;
  position: relative;
  margin: 20px;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  text-align: center;
}

.icon-container {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 36px;
}

.title {
  font-size: 2rem;
  margin-bottom: 10px;
  font-weight: 600;
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  font-weight: 300;
}

.content {
  padding: 40px;
}

.info-message {
  background: #f0f7ff;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 40px;
  display: flex;
  align-items: flex-start;
  border-left: 4px solid #667eea;
}

.message-icon {
  margin-right: 20px;
  color: #667eea;
  font-size: 24px;
  margin-top: 4px;
}

.message-content h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 1.2rem;
}

.message-content p {
  margin: 0 0 10px 0;
  color: #555;
  line-height: 1.6;
}

.message-content .highlight {
  background: #fff3cd;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
  color: #856404;
  font-weight: 500;
  margin-top: 15px;
}

.process-steps {
  margin-bottom: 40px;
}

.process-steps h2 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 1.5rem;
}

.steps-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
  flex: 1;
}

.step-number {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
  margin-bottom: 15px;
}

.step-number.active {
  background: #28a745;
  color: white;
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
}

.step-number.current {
  background: #ffc107;
  color: #856404;
  box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
}

.step-number:not(.active):not(.current) {
  background: #e9ecef;
  color: #6c757d;
}

.step-content {
  text-align: center;
  max-width: 150px;
}

.step-content h4 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 1rem;
}

.step-content p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
}

.step-line {
  position: absolute;
  height: 3px;
  background: #e9ecef;
  top: 25px;
  left: 12.5%;
  right: 12.5%;
  z-index: 1;
}

.additional-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.info-box {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.info-box:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.info-box i {
  color: #667eea;
  font-size: 24px;
  margin-right: 15px;
  margin-top: 5px;
}

.info-content h4 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 1rem;
}

.info-content p {
  margin: 0;
  color: #666;
  font-size: 0.95rem;
  line-height: 1.5;
}

.logout-section {
  text-align: center;
  padding-top: 30px;
  border-top: 1px solid #e9ecef;
}

.btn-logout {
  background: #f8f9fa;
  color: #dc3545;
  border: 2px solid #dc3545;
  padding: 12px 40px;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s ease;
  min-width: 200px;
}

.btn-logout:hover {
  background: #dc3545;
  color: white;
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(220, 53, 69, 0.2);
}

.logout-note {
  margin-top: 15px;
  color: #6c757d;
  font-size: 0.9rem;
  font-style: italic;
}

/* Responsive */
@media (max-width: 768px) {
  .header {
    padding: 30px 20px;
  }
  
  .content {
    padding: 30px 20px;
  }
  
  .title {
    font-size: 1.8rem;
  }
  
  .info-message {
    flex-direction: column;
    text-align: center;
  }
  
  .message-icon {
    margin-right: 0;
    margin-bottom: 15px;
  }
  
  .steps-container {
    flex-direction: column;
    gap: 30px;
  }
  
  .step-line {
    display: none;
  }
  
  .step {
    flex-direction: row;
    width: 100%;
    text-align: left;
  }
  
  .step-number {
    margin-right: 20px;
    margin-bottom: 0;
    flex-shrink: 0;
  }
  
  .step-content {
    text-align: left;
    max-width: none;
  }
  
  .additional-info {
    grid-template-columns: 1fr;
  }
  
  .btn-logout {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .title {
    font-size: 1.5rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .step {
    flex-direction: column;
    text-align: center;
  }
  
  .step-number {
    margin-right: 0;
    margin-bottom: 15px;
  }
  
  .step-content {
    text-align: center;
  }
}
</style>
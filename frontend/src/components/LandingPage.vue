<template>
  <div class="landing-page-wrapper">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    
    <header class="header">
      <div class="container">
        <nav class="nav">
          <router-link to="/" class="logo">
            <div class="logo-container">
              <div class="logo-icon">
                <img src="../assets/logo.png" alt="CRM Pro Logo">
              </div>
              <div class="logo-text">
                <span class="logo-name">CRM</span>
                <span class="logo-pro">Pro</span>
              </div>
            </div>
          </router-link>
          <div class="nav-links">
            <a href="#caracteristicas"><i class="bi bi-star-fill"></i> Características</a>
            <a href="#precios"><i class="bi bi-tag-fill"></i> Precios</a>
            <a href="#"><i class="bi bi-envelope-fill"></i> Contacto</a>
            <router-link to="/login" class="nav-button login-button">
              <i class="bi bi-box-arrow-in-right"></i> Iniciar Sesión
            </router-link>
          </div>
        </nav>
      </div>
    </header>

    <main>
      <section class="hero-section">
        <div class="hero-background">
          <div class="floating-shape shape-1"></div>
          <div class="floating-shape shape-2"></div>
          <div class="floating-shape shape-3"></div>
          <div class="grid-overlay"></div>
        </div>
        <div class="container">
          <div class="hero-content">
            <div class="hero-badge animate-fade-in-up">
              <i class="bi bi-stars"></i> Nuevo: Gestión Inteligente de Inventario
            </div>
            <h1 class="animate-fade-in-up delay-1">Tu Inventario y Clientes, <span class="gradient-text">Simplificados</span></h1>
            <p class="animate-fade-in-up delay-2">CRM Pro es la solución web que te permite registrar, buscar y gestionar tus productos con una interfaz limpia, rápida y potente. ¡Toma el control total!</p>
            <div class="cta-group animate-fade-in-up delay-3">
              <router-link to="/register" class="cta-button cta-primary">
                <i class="bi bi-rocket-takeoff-fill"></i> Comienza Gratis Hoy
              </router-link>
              <a href="#caracteristicas" class="cta-button cta-secondary">
                <i class="bi bi-play-circle-fill"></i> Ver Demo
              </a>
            </div>
            <div class="hero-stats animate-fade-in-up delay-4">
              <div class="stat-item">
                <div class="stat-number">10K+</div>
                <div class="stat-label">Usuarios Activos</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">99.9%</div>
                <div class="stat-label">Uptime</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">4.9★</div>
                <div class="stat-label">Calificación</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="caracteristicas" class="features-section">
        <div class="container">
          <h2 class="section-title animate-fade-in-up">Características Clave del CRM</h2>
          <p class="section-subtitle animate-fade-in-up delay-1">Funcionalidades basadas en lo que has estado construyendo.</p>

          <div class="features-grid">
            <div class="feature-card animate-fade-in-up delay-2">
              <div class="feature-icon-wrapper">
                <i class="feature-icon bi bi-box-seam-fill"></i>
              </div>
              <h3>Gestión Centralizada de Productos</h3>
              <p>Registra, edita y elimina productos de tu inventario con un formulario intuitivo. Soporte para nombre y precio obligatorio.</p>
              <div class="feature-badge">Esencial</div>
            </div>

            <div class="feature-card animate-fade-in-up delay-3">
              <div class="feature-icon-wrapper">
                <i class="feature-icon bi bi-search-heart-fill"></i>
              </div>
              <h3>Búsqueda y Filtrado Instantáneo</h3>
              <p>Encuentra cualquier producto al instante usando el campo de búsqueda. Filtra la lista en tiempo real por nombre.</p>
              <div class="feature-badge">Rápido</div>
            </div>

            <div class="feature-card animate-fade-in-up delay-4">
              <div class="feature-icon-wrapper">
                <i class="feature-icon bi bi-pencil-square"></i>
              </div>
              <h3>Edición con Modal Profesional</h3>
              <p>Actualiza la información de los productos (nombre, precio) a través de una ventana modal limpia y sin recargar la página.</p>
              <div class="feature-badge">Intuitivo</div>
            </div>

            <div class="feature-card animate-fade-in-up delay-5">
              <div class="feature-icon-wrapper">
                <i class="feature-icon bi bi-list-ol"></i>
              </div>
              <h3>Paginación Inteligente</h3>
              <p>Navega a través de grandes inventarios con una paginación clara que muestra el número total de productos y el rango visible.</p>
              <div class="feature-badge">Organizado</div>
            </div>

            <div class="feature-card animate-fade-in-up delay-6">
              <div class="feature-icon-wrapper">
                <i class="feature-icon bi bi-bell-fill"></i>
              </div>
              <h3>Alertas de Éxito y Error</h3>
              <p>Recibe notificaciones visuales (mensajes de éxito y error) al agregar o actualizar productos para una retroalimentación inmediata.</p>
              <div class="feature-badge">Claro</div>
            </div>

            <div class="feature-card animate-fade-in-up delay-7">
              <div class="feature-icon-wrapper">
                <i class="feature-icon bi bi-phone-fill"></i>
              </div>
              <h3>Diseño Web Adaptable</h3>
              <p>Accede y gestiona tu inventario desde cualquier dispositivo: PC, tablet o móvil, con una interfaz que se ajusta perfectamente.</p>
              <div class="feature-badge">Responsive</div>
            </div>
          </div>
        </div>
      </section>

      <section class="demo-section">
        <div class="container">
          <h2 class="section-title animate-fade-in-up">¿Listo para Organizar tu Negocio?</h2>
          <p class="section-subtitle animate-fade-in-up delay-1">Únete a la nueva era de la gestión de productos y enfócate en lo que realmente importa: ¡crecer!</p>
          <router-link to="/register" class="cta-button cta-primary animate-fade-in-up delay-2">
            <i class="bi bi-rocket-takeoff-fill"></i> Probar CRM Pro Ahora
          </router-link>
        </div>
      </section>
    </main>

    <footer class="footer">
      <div class="container">
        <p>
          <span class="logo-name-footer">CRM</span>
          <span class="logo-pro-footer">Pro</span>
          &copy; 2025. Todos los derechos reservados. | Diseñado para la eficiencia.
        </p>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'LandingPage',
};
</script>

<style>
/* Variables de color actualizadas */
:root {
  --primary-gradient-start: #667eea;
  --primary-gradient-end: #764ba2;
  --accent-gradient-start: #f093fb;
  --accent-gradient-end: #f5576c;
  --secondary-color: #10b981;
  --dark-text: #1f2937;
  --light-text: #f9fafb;
  --card-bg: white;
  --card-shadow-light: 0 10px 30px rgba(0, 0, 0, 0.08);
  --card-shadow-hover: 0 20px 50px rgba(0, 0, 0, 0.15);
  --header-bg: rgba(255, 255, 255, 0.95);
}

/* Estilos Generales */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: 'Poppins', sans-serif;
}

body {
  line-height: 1.6;
  color: var(--dark-text);
  background: linear-gradient(135deg, var(--primary-gradient-start) 0%, var(--primary-gradient-end) 100%);
  min-height: 100vh;
}

.landing-page-wrapper {
  overflow-x: hidden;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

h1, h2, h3 {
  font-weight: 700;
  margin-bottom: 0.5em;
  line-height: 1.2;
}

p {
  margin-bottom: 1em;
}

/* --- Encabezado y Navegación --- */
.header {
  background-color: var(--header-bg);
  backdrop-filter: blur(10px);
  padding: 15px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05); /* Ajustado a gris muy suave */
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.08);
}

.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  text-decoration: none;
  transition: transform 0.3s ease;
  padding: 5px 0; /* Padding para el área de clic */
}

/* Estilos del Componente Logo */
.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, var(--primary-gradient-start), var(--primary-gradient-end));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
  overflow: hidden; /* Asegura que la imagen se contenga dentro del icono */
}

.logo-icon img {
  width: 100%; /* La imagen ocupa todo el ancho del contenedor */
  height: 100%; /* La imagen ocupa toda la altura del contenedor */
  object-fit: contain; /* Mantiene la proporción de la imagen y la ajusta */
  padding: 5px; /* Pequeño padding para que el logo no se pegue a los bordes */
}

.logo:hover .logo-icon {
  transform: rotate(5deg) scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

/* Removido el estilo 'logo-icon i' ya que ahora usamos una imagen */
/* .logo-icon i {
  font-size: 1.8rem;
  color: white;
} */

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1;
}

.logo-name {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--primary-gradient-start);
  letter-spacing: -0.5px;
}

.logo-pro {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--secondary-color);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 2px;
}
/* Fin Estilos del Componente Logo */

.nav-links {
  display: flex;
  align-items: center;
}

.nav-links a {
  color: var(--dark-text);
  text-decoration: none;
  margin-left: 25px;
  font-weight: 500;
  transition: color 0.3s ease, transform 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-links a i {
  font-size: 0.9rem;
}

.nav-links a:hover {
  color: var(--primary-gradient-end);
  transform: translateY(-2px);
}

.nav-button {
  padding: 10px 24px;
  border-radius: 25px;
  font-weight: 600;
  margin-left: 25px;
  transition: all 0.3s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
}

.login-button {
  background-color: transparent;
  border: 2px solid var(--primary-gradient-end);
  color: var(--primary-gradient-end);
}

.login-button:hover {
  background-color: var(--primary-gradient-end);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
}

/* --- Sección Principal (Hero) --- */
.hero-section {
  background: linear-gradient(135deg, var(--primary-gradient-start) 0%, var(--primary-gradient-end) 100%);
  color: white;
  padding: 140px 0 100px;
  text-align: center;
  position: relative;
  overflow: hidden;
  min-height: 700px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px);
  background-size: 50px 50px;
  opacity: 0.3;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
  backdrop-filter: blur(20px);
  animation: float 20s infinite ease-in-out;
}

.shape-1 {
  width: 300px;
  height: 300px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 200px;
  height: 200px;
  top: 60%;
  right: 15%;
  animation-delay: 5s;
}

.shape-3 {
  width: 150px;
  height: 150px;
  bottom: 20%;
  left: 60%;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33% { transform: translate(30px, -30px) rotate(120deg); }
  66% { transform: translate(-20px, 20px) rotate(240deg); }
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 10px 24px;
  border-radius: 50px;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 30px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.hero-section h1 {
  font-size: 4.2rem;
  margin-bottom: 30px;
  text-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  font-weight: 800;
  line-height: 1.1;
}

.gradient-text {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-section p {
  font-size: 1.3rem;
  margin-bottom: 45px;
  max-width: 750px;
  margin-left: auto;
  margin-right: auto;
  opacity: 0.95;
  line-height: 1.7;
}

.cta-group {
  display: flex;
  gap: 20px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 60px;
}

.cta-button {
  padding: 18px 40px;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.cta-primary {
  background: linear-gradient(135deg, var(--secondary-color) 0%, #059669 100%);
  color: white;
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
}

.cta-primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 40px rgba(16, 185, 129, 0.5);
}

.cta-secondary {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.cta-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-3px);
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 5px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 0.95rem;
  opacity: 0.9;
  font-weight: 500;
}

/* --- Sección de Características (Features) --- */
.features-section {
  padding: 100px 0;
  background-color: var(--light-text);
  text-align: center;
}

.section-title {
  font-size: 2.8rem;
  color: var(--primary-gradient-end);
  margin-bottom: 20px;
  text-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.section-subtitle {
  font-size: 1.25rem;
  color: #6c757d;
  margin-bottom: 80px;
  max-width: 900px;
  margin-left: auto;
  margin-right: auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 40px;
}

.feature-card {
  background: linear-gradient(135deg, white 0%, #f9fafb 100%);
  padding: 45px 35px;
  border-radius: 24px;
  text-align: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--card-shadow-light);
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  min-height: 280px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-gradient-start), var(--accent-gradient-end));
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s ease;
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.feature-card:hover {
  transform: translateY(-12px) scale(1.02);
  box-shadow: var(--card-shadow-hover);
  border-color: rgba(102, 126, 234, 0.2);
}

.feature-icon-wrapper {
  width: 90px;
  height: 90px;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--primary-gradient-start), var(--primary-gradient-end));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 25px;
  transition: all 0.4s ease;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.feature-card:hover .feature-icon-wrapper {
  transform: rotateY(360deg) scale(1.1);
  background: linear-gradient(135deg, var(--accent-gradient-start), var(--accent-gradient-end));
}

.feature-icon {
  font-size: 2.5rem;
  color: white;
  display: block;
}

.feature-badge {
  position: absolute;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, var(--secondary-color), #059669);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
}

.feature-card h3 {
  margin-bottom: 15px;
  font-size: 1.5rem;
  color: var(--dark-text);
  font-weight: 700;
}

.feature-card p {
  font-size: 1rem;
  color: #6b7280;
  line-height: 1.6;
}

/* --- Sección de Demo --- */
.demo-section {
  padding: 100px 0;
  background: linear-gradient(45deg, var(--primary-gradient-end) 0%, var(--primary-gradient-start) 100%);
  color: white;
  text-align: center;
  box-shadow: inset 0 5px 20px rgba(0, 0, 0, 0.1);
}

.demo-section .section-title {
  color: white;
  text-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.demo-section .section-subtitle {
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 50px;
}

/* --- Footer --- */
.footer {
  background-color: #212529;
  color: var(--light-text);
  padding: 40px 0;
  text-align: center;
  font-size: 0.9rem;
  box-shadow: inset 0 5px 15px rgba(0, 0, 0, 0.2);
}

.footer p {
  margin: 0;
  opacity: 0.8;
}

/* Estilos del Logo en el Footer (para que coincida con la tipografía de la cabecera) */
.logo-name-footer {
  font-weight: 800;
  color: var(--light-text); /* Blanco para contraste */
}

.logo-pro-footer {
  font-weight: 600;
  color: var(--secondary-color);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Animaciones */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  opacity: 0;
  animation: fadeInUp 0.8s ease-out forwards;
}

.delay-1 { animation-delay: 0.2s; }
.delay-2 { animation-delay: 0.4s; }
.delay-3 { animation-delay: 0.6s; }
.delay-4 { animation-delay: 0.8s; }
.delay-5 { animation-delay: 1.0s; }
.delay-6 { animation-delay: 1.2s; }
.delay-7 { animation-delay: 1.4s; }

/* Media Queries para Responsividad */
@media (max-width: 768px) {
  .hero-section h1 {
    font-size: 2.5rem;
  }
  .hero-section p {
    font-size: 1rem;
  }
  .section-title {
    font-size: 2rem;
  }
  .features-grid {
    grid-template-columns: 1fr;
  }
  .nav {
    flex-direction: column;
    align-items: flex-start; /* Alinea el logo a la izquierda en móvil */
  }
  .nav-links {
    margin-top: 15px;
    flex-wrap: wrap;
    justify-content: flex-start; /* Alinea los enlaces a la izquierda en móvil */
  }
  .nav-links a, .nav-button {
    margin: 5px 10px 5px 0;
  }
  .nav-links a:first-child {
    margin-left: 0;
  }
  .hero-stats {
    gap: 30px;
  }
  .stat-number {
    font-size: 2rem;
  }

  /* Ajuste específico para el logo en pantallas medianas */
  .logo-icon {
    width: 45px;
    height: 45px;
    border-radius: 10px;
  }
  .logo-name {
    font-size: 1.4rem;
  }
  .logo-pro {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .hero-section h1 {
    font-size: 2rem;
  }
  .cta-button {
    padding: 12px 25px;
    font-size: 1rem;
  }
  .section-title {
    font-size: 1.8rem;
  }
  .feature-card {
    padding: 25px;
  }
  .feature-icon {
    font-size: 2rem;
  }
  .feature-icon-wrapper {
    width: 70px;
    height: 70px;
  }

  /* Ajuste específico para el logo en pantallas pequeñas */
  .logo-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
  }
  .logo-icon img {
    padding: 3px;
  }
  .logo-name {
    font-size: 1.3rem;
  }
  .logo-pro {
    font-size: 0.75rem;
  }
  .logo-container {
    gap: 8px; /* Reduce el espacio entre el icono y el texto del logo */
  }
}
</style>
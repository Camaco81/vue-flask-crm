<template>
  <div class="dashboard-container">
    <aside class="sidebar">
      <nav class="navigation">
        <ul class="nav-list">
          <li class="nav-item">
            <router-link to="/vendedor/customers" class="nav-link">
              <div class="nav-icon"><i class="fas fa-users"></i></div>
              <span class="nav-text">Clientes</span>
              <div class="nav-indicator"></div>
            </router-link>
          </li>
          
          <li class="nav-item">
            <router-link to="/vendedor/sales" class="nav-link">
              <div class="nav-icon"><i class="fas fa-shopping-cart"></i></div>
              <span class="nav-text">Ventas</span>
              <div class="nav-indicator"></div>
            </router-link>
          </li>
          
          <li class="nav-item">
            <router-link to="/vendedor/profile" class="nav-link">
              <div class="nav-icon"><i class="fas fa-user"></i></div>
              <span class="nav-text">Perfil</span>
              <div class="nav-indicator"></div>
            </router-link>
          </li>
        </ul>
      </nav>

      <div class="user-section">
        <div class="user-info">
          <div class="user-avatar">
            <i class="fas fa-user-circle"></i>
          </div>
          <div class="user-details">
            <span class="user-name">Usuario</span>
            <span class="user-role">Vendedor</span>
          </div>
        </div>
        <button @click="logout" class="logout-btn" title="Cerrar Sesión">
          <i class="fas fa-sign-out-alt"></i>
          <span>Cerrar Sesión</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <header class="content-header">
        <div class="header-content">
          <h1 class="welcome-title">¡Bienvenido!</h1>
          <p class="welcome-subtitle">Tu centro de operaciones de ventas.</p>
        </div>
        <div class="header-actions">
          <button class="action-btn">
            <i class="fas fa-bell"></i>
          </button>
          <button class="action-btn">
            <i class="fas fa-cog"></i>
          </button>
        </div>
      </header>

      <div class="content-body">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon customers">
              <i class="fas fa-users"></i>
            </div>
            <div class="stat-content">
              <h3 class="stat-number">
                <span v-if="loading.customers" class="spinner-small"></span>
                <span v-else>{{ metrics.customers }}</span>
              </h3>
              <p class="stat-label">Clientes Totales</p>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon revenue">
              <i class="fas fa-dollar-sign"></i>
            </div>
            <div class="stat-content">
              <h3 class="stat-number">
                <span v-if="loading.totalRevenue" class="spinner-small"></span>
                <span v-else>${{ metrics.totalRevenue }}</span>
              </h3>
              <p class="stat-label">Ingresos Totales</p>
            </div>
          </div>
          
          </div>

        <div class="quick-actions">
          <h2 class="section-title">Enfoque Rápido</h2>
          <div class="actions-grid">
            
            <router-link to="/vendedor/customers" class="quick-action-card">
              <i class="fas fa-user-plus"></i>
              <span>Agregar Cliente</span>
            </router-link>
            
            <router-link to="/vendedor/sales" class="quick-action-card primary-action"> 
              <i class="fas fa-cash-register"></i> 
              <span>Registrar Venta</span>
            </router-link>
            
            
            
            </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import apiClient from '../../axios';

export default {
    name: 'VendedorDashboard', // Renombrado de HomeDashboard para ser específico
    data() {
        return {
            metrics: {
                customers: 0,
                // Eliminamos 'products'
                totalRevenue: 0, 
            },
            loading: {
                customers: true,
                // Eliminamos 'products'
                totalRevenue: true, 
            },
            errors: {
                customers: null,
                // Eliminamos 'products'
                totalRevenue: null,
            }
        };
    },
    methods: {
        logout() {
            // Usar localStorage o sessionStorage consistentemente. Asumo localStorage por el router/index.js
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_info'); 
            this.$router.push('/login');
        },
        
        // Función para obtener la lista completa de Clientes
        async fetchCustomers() {
            try {
                // Asumimos que esta ruta devuelve una lista completa de clientes que el vendedor puede ver
                const response = await apiClient.get('/api/customers');
                this.metrics.customers = response.data.length;
            } catch (error) {
                console.error("Error al cargar clientes:", error);
                this.errors.customers = "Error al cargar clientes";
            } finally {
                this.loading.customers = false;
            }
        },
        
        // Eliminamos fetchProducts()
        
        // Lógica CONSOLIDADA para Ventas e Ingresos
        async fetchSalesMetrics() {
            try {
                this.loading.totalRevenue = true;
                this.metrics.totalRevenue = 0;

                // Asumimos que esta ruta devuelve SÓLO las ventas del vendedor autenticado
                const response = await apiClient.get('/api/sales');
                const sales = response.data; // Lista de todas las ventas del vendedor

                // Calcular Ingresos Totales
                const totalRevenue = sales.reduce((sum, sale) => {
                    const amount = parseFloat(sale.total_amount) || 0; 
                    return sum + amount;
                }, 0);
                
                this.metrics.totalRevenue = totalRevenue.toFixed(2);

            } catch (error) {
                console.error("Error al cargar métricas de ventas:", error);
                this.errors.totalRevenue = "Error al cargar ingresos";
            } finally {
                this.loading.totalRevenue = false;
            }
        },
        
        fetchDashboardData() {
            this.fetchCustomers();
            // Eliminamos this.fetchProducts();
            this.fetchSalesMetrics(); 
        }
    },
    mounted() {
        this.fetchDashboardData();
    }
};
</script>





<style scoped>
/*
  Los estilos CSS se mantienen igual que en tu código original,
  simplemente se ha añadido un estilo para el spinner de carga.
*/

* {
  box-sizing: border-box;
}

.dashboard-container {
  display: flex;
  height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

/* ===== SIDEBAR ===== */
.sidebar {
  width: 280px;
  background: linear-gradient(180deg, #1a1d29 0%, #2d3748 100%);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
}

.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.05) 0%, transparent 100%);
  pointer-events: none;
}

.logo-section {
  padding: 30px 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  color: #ffffff;
  font-size: 20px;
  font-weight: 700;
}

.logo i {
  font-size: 28px;
  margin-right: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.navigation {
  flex: 1;
  padding: 20px 0;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  margin: 8px 0;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 16px 25px;
  color: #a0aec0;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  border-radius: 0 25px 25px 0;
  margin-right: 15px;
}

.nav-link:hover {
  color: #ffffff;
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.15) 0%, rgba(102, 126, 234, 0.05) 100%);
  transform: translateX(8px);
}

.nav-link.router-link-active {
  color: #ffffff;
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.2) 0%, rgba(102, 126, 234, 0.1) 100%);
  box-shadow: inset 4px 0 0 #667eea;
}

.nav-link.router-link-active .nav-indicator {
  opacity: 1;
  transform: scaleY(1);
}

.nav-icon {
  width: 24px;
  display: flex;
  justify-content: center;
  margin-right: 15px;
  font-size: 18px;
}

.nav-text {
  font-weight: 500;
  font-size: 15px;
}

.nav-indicator {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, #667eea, #764ba2);
  border-radius: 2px;
  opacity: 0;
  transition: all 0.3s ease;
}

.user-section {
  padding: 25px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
}

.user-avatar {
  font-size: 32px;
  color: #667eea;
  margin-right: 12px;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  color: #ffffff;
  font-weight: 600;
  font-size: 16px;
}

.user-role {
  color: #a0aec0;
  font-size: 12px;
  margin-top: 2px;
}

.logout-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #e53e3e, #c53030);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(229, 62, 62, 0.3);
}

.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(229, 62, 62, 0.4);
}

.logout-btn i {
  margin-right: 8px;
}

/* ===== MAIN CONTENT ===== */
.main-content {
  flex: 1;
  background: #f8fafc;
  overflow-y: auto;
  position: relative;
}

.content-header {
  background: white;
  padding: 30px 40px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle {
  color: #718096;
  margin: 0;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  width: 44px;
  height: 44px;
  border: none;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.content-body {
  padding: 40px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  margin-right: 20px;
}

.stat-icon.customers { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-icon.products { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-icon.orders { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.stat-icon.revenue { background: linear-gradient(135deg, #43e97b, #38f9d7); }

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 5px 0;
}

.stat-label {
  color: #718096;
  margin: 0;
  font-weight: 500;
}

/* ===== SPINNER ESTILOS ===== */
.spinner-small {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid #f3f4f6;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.quick-actions {
  margin-top: 20px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 24px 0;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.quick-action-card {
  background: white;
  padding: 30px;
  border-radius: 16px;
  text-decoration: none;
  color: #4a5568;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 2px solid transparent;
}

.quick-action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.15);
  border-color: #667eea;
  color: #667eea;
}

.quick-action-card i {
  font-size: 32px;
  margin-bottom: 16px;
  display: block;
}

.quick-action-card span {
  font-weight: 600;
  font-size: 16px;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .dashboard-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    flex-direction: row;
    overflow-x: auto;
  }
  
  .navigation {
    flex: 1;
  }
  
  .nav-list {
    display: flex;
    gap: 10px;
  }
  
  .user-section {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .content-header {
    padding: 20px;
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .content-body {
    padding: 20px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .welcome-title {
    font-size: 24px;
  }
}

/* Estilo para la acción de registrar venta */
.quick-action-card.primary-action {
  /* Usamos los colores del theme principal para darle más énfasis */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #5a66c8;
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
}

.quick-action-card.primary-action:hover {
  transform: translateY(-8px); /* Más levantado para enfatizar */
  box-shadow: 0 15px 50px rgba(102, 126, 234, 0.5);
  border-color: #ffffff; /* Borde blanco al pasar el mouse */
}

/* Ajuste del icono para que se vea blanco */
.quick-action-card.primary-action i {
    color: white;
}

/* Eliminación de productos en la rejilla de iconos, se mantiene revenue y customers */
.stat-icon.products {
    /* Eliminamos el gradiente, si se mantiene este estilo es inútil, 
       pero se deja para no romper si otros componentes lo usan.
       En este componente, la métrica ya fue eliminada. */
    display: none; 
}
</style>
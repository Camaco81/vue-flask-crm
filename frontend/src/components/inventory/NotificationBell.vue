<template>
  <div class="notification-container">
    <button @click="toggleDropdown" class="notification-btn" :aria-expanded="showDropdown">
      <i class="fas fa-bell"></i>
      <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
    </button>

    <div v-if="showDropdown" class="dropdown-menu">
      <div class="dropdown-header">
        <h4>Notificaciones ({{ unreadCount }} No Leídas)</h4>
        <button @click="markAllAsRead" class="mark-read-btn" v-if="unreadCount > 0">
          Marcar todas como leídas
        </button>
      </div>

      <div v-if="loading" class="loading-state">Cargando...</div>

      <div v-else-if="notifications.length === 0" class="empty-state">
        No tienes notificaciones nuevas.
      </div>

      <div v-else class="notification-list">
        <div 
          v-for="notif in notifications" 
          :key="notif.id" 
          :class="['notification-item', notif.tipo]"
        >
          <div class="icon">
            <i :class="getIcon(notif.tipo)"></i>
          </div>
          <div class="content">
            <p class="message">{{ notif.mensaje }}</p>
            <small class="time">{{ formatTime(notif.created_at) }}</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import notificationService from '@/services/notificationService'; 

export default {
  name: 'NotificationBell',
  data() {
    return {
      notifications: [],
      unreadCount: 0,
      showDropdown: false, 
      loading: false,
    };
  },
  computed: {
    userRole() {
      // 💡 Lógica para obtener el rol del usuario desde localStorage
      const user = JSON.parse(localStorage.getItem('user_info') || '{}');
      
      // Asume: 1=Admin, 2=Vendedor, 3=Almacenista
      if (user.role_id === 1 || user.role_id === 3) return 'almacenista'; 
      
      // Asegúrate de devolver un rol válido o null
      return null; 
    }
  },
  methods: {
    toggleDropdown() {
      this.showDropdown = !this.showDropdown;
      // Cuando se abre, forzar la recarga de notificaciones
      if (this.showDropdown) {
        this.fetchNotifications();
      }
    },
    
    // 🟢 NUEVO: Cierra el dropdown si el clic fue fuera del componente
    closeDropdown(event) {
      if (this.$el && !this.$el.contains(event.target)) {
        this.showDropdown = false;
      }
    },
    
    // Método para cargar las alertas desde el backend
    async fetchNotifications() {
      if (!this.userRole || this.loading) return;
      this.loading = true;
      try {
        const response = await notificationService.getUnreadNotifications(this.userRole);
        
        this.notifications = response.data;
        this.unreadCount = response.data.length;
      } catch (error) {
        console.error("Error al obtener notificaciones:", error);
        this.notifications = [];
        this.unreadCount = 0;
      } finally {
        this.loading = false;
      }
    },

    // Método para marcar como leídas
    async markAllAsRead() {
      try {
        await notificationService.markAllAsRead(this.userRole);
        this.unreadCount = 0;
        this.notifications = [];
        this.showDropdown = false;
      } catch (error) {
        console.error("Error al marcar como leídas:", error);
      }
    },

    // Método para formatear el tiempo
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffInSeconds = (now - date) / 1000;

        const units = [
            { name: "año", seconds: 31536000, rtfUnit: 'year' },
            { name: "mes", seconds: 2592000, rtfUnit: 'month' },
            { name: "día", seconds: 86400, rtfUnit: 'day' },
            { name: "hora", seconds: 3600, rtfUnit: 'hour' },
            { name: "minuto", seconds: 60, rtfUnit: 'minute' },
            { name: "segundo", seconds: 1, rtfUnit: 'second' }
        ];

        for (let i = 0; i < units.length; i++) {
            const unit = units[i];
            const interval = Math.floor(diffInSeconds / unit.seconds);
            if (interval >= 1) {
                if (typeof Intl.RelativeTimeFormat !== 'undefined') {
                    const rtf = new Intl.RelativeTimeFormat('es', { numeric: 'auto' });
                    return rtf.format(-interval, unit.rtfUnit); 
                }
                return `hace ${interval} ${unit.name}${interval > 1 ? 's' : ''}`;
            }
        }
        return 'justo ahora';
    },

    // Método para asignar el icono
    getIcon(tipo) {
        switch (tipo) {
            case 'stock_critico':
                return 'fas fa-exclamation-triangle text-warning'; 
            case 'tendencia_alta':
                return 'fas fa-chart-line text-info'; 
            default:
                return 'fas fa-info-circle text-muted';
        }
    }
  },
  
  mounted() {
    this.fetchNotifications();
    // 🟢 Agregar listener para cerrar al hacer clic fuera
    document.addEventListener('click', this.closeDropdown);
  },
  
  // 🟢 IMPORTANTE: Eliminar el listener al destruir el componente (previene fugas de memoria)
  beforeUnmount() { 
    document.removeEventListener('click', this.closeDropdown);
  }
};
</script>

<style scoped>
/* Estilos necesarios para el layout (Sin cambios) */
.notification-container {
  position: relative;
  display: inline-block;
}

.notification-btn {
  background: none;
  border: none;
  cursor: pointer;
  position: relative;
  padding: 0;
}

.notification-btn i {
  font-size: 1.5rem;
  color: #4a5568;
}

.notification-badge {
  position: absolute;
  top: -5px;
  right: -8px;
  background-color: #e53e3e; /* Rojo */
  color: white;
  border-radius: 50%;
  padding: 2px 6px;
  font-size: 0.7rem;
  font-weight: bold;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  width: 350px; 
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000; 
  margin-top: 10px;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid #edf2f7;
}

.dropdown-header h4 {
  margin: 0;
  font-size: 1rem;
}

.mark-read-btn {
  background: none;
  border: none;
  color: #4299e1; /* Azul */
  font-size: 0.8rem;
  cursor: pointer;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  padding: 10px 15px;
  border-bottom: 1px solid #edf2f7;
  text-align: left;
  gap: 10px;
}

.notification-item .icon {
  font-size: 1.2rem;
  padding-top: 2px;
}

.notification-item .content {
  flex-grow: 1;
}

.message {
  margin: 0;
  font-size: 0.9rem;
  color: #1a202c;
}

.time {
  font-size: 0.75rem;
  color: #718096;
}

.empty-state, .loading-state {
  padding: 15px;
  color: #718096;
  font-style: italic;
}

.text-warning {
    color: #ecc94b; /* Amarillo */
}
.text-info {
    color: #4299e1; /* Azul */
}
</style>
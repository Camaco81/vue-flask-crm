<template>
  <div class="notification-container">
    <button @click="toggleDropdown" class="notification-btn" :aria-expanded="showDropdown">
      <font-awesome-icon icon="fas fa-bell"/>
      <span v-if="notifications.length > 0" class="notification-badge">{{ notifications.length }}</span>
    </button>

    <div v-if="showDropdown" class="dropdown-menu">
      <div class="dropdown-header">
        <h4>Alertas Estacionales Activas ({{ notifications.length }})</h4>
      </div>

      <div v-if="loading" class="loading-state">Cargando...</div>

      <div v-else-if="notifications.length === 0" class="empty-state">
        No hay alertas estacionales activas en este momento.
      </div>

      <div v-else class="notification-list">
        <div 
          v-for="notif in notifications" 
          :key="notif.id" 
          :class="['notification-item', notif.tipo]"
        >
          <div class="icon">
            <font-awesome-icon 
              :icon="getIcon(notif.tipo)" 
              :class="getIconClass(notif.tipo)"
            />
          </div>
          <div class="content">
            <p class="message" v-html="notif.mensaje"></p> 
            <small class="time">{{ formatTime(notif.created_at) }}</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../../axios'; // 🟢 Usando la instancia de Axios importada

export default {
  name: 'NotificationBell',
  data() {
    return {
      notifications: [],
      showDropdown: false, 
      loading: false,
    };
  },
  methods: {
    toggleDropdown() {
      this.showDropdown = !this.showDropdown;
      if (this.showDropdown) {
        this.fetchNotifications();
      }
    },
    
    closeDropdown(event) {
      if (this.$el && !this.$el.contains(event.target)) {
        this.showDropdown = false;
      }
    },
    
    /**
     * 🟢 AJUSTE CLAVE: Consumo directo del endpoint /api/alerts/seasonal usando apiClient (Axios).
     * Se asume que apiClient maneja la URL base y el token JWT automáticamente.
     */
    async fetchNotifications() {
      if (this.loading) return;
      this.loading = true;
      try {
        // 🟢 Reemplazando 'fetch' con 'apiClient.get'
        const response = await apiClient.get('/api/alerts/seasonal');
        
        // Axios envuelve los datos de la respuesta en 'response.data'
        this.notifications = response.data; 
        
      } catch (error) {
        // Axios maneja mejor los errores HTTP, pero el manejo final en el componente es similar
        console.error("Error al obtener alertas estacionales:", error);
        // Mostrar array vacío en caso de error
        this.notifications = []; 
      } finally {
        this.loading = false;
      }
    },

    // Método para formatear el tiempo (Mantenido)
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
                    try {
                        return rtf.format(-interval, unit.rtfUnit);
                    } catch {
                         return `hace ${interval} ${unit.name}${interval > 1 ? 's' : ''}`;
                    }
                }
                return `hace ${interval} ${unit.name}${interval > 1 ? 's' : ''}`;
            }
        }
        return 'justo ahora';
    },

    // Método para asignar el icono (Mantenido)
    getIcon(tipo) {
        switch (tipo) {
            case 'stock_critico_estacional':
                return 'fas fa-exclamation-triangle'; 
            case 'tendencia_alta':
                return 'fas fa-chart-line'; 
            default:
                return 'fas fa-info-circle';
        }
    },
    // Método para asignar la clase de color (Mantenido)
    getIconClass(tipo) {
        switch (tipo) {
            case 'stock_critico_estacional':
                return 'text-danger'; 
            case 'tendencia_alta':
                return 'text-info'; 
            default:
                return 'text-muted';
        }
    }
  },
  
  mounted() {
    this.fetchNotifications();
    document.addEventListener('click', this.closeDropdown);
  },
  
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
.text-warning {
    color: #ecc94b; /* Amarillo */
}
.text-info {
    color: #4299e1; /* Azul */
}

/* Estilos para notificaciones NO LEÍDAS */
.notification-item.unread {
    font-weight: 600; /* Hace que el texto resalte */
    background-color: #f7fafc; /* Fondo ligeramente más claro */
}

/* Estilos para el ítem de notificación de Stock Crítico */
.notification-item.stock_critico {
    border-left: 4px solid #ecc94b; 
}

/* Estilos para el ítem de notificación de Tendencia Alta */
.notification-item.tendencia_alta {
    border-left: 4px solid #4299e1; 
} 
</style>
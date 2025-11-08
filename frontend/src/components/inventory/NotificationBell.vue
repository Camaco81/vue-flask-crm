<template>
  <div class="notification-dropdown">
    <button @click="toggleDropdown" class="notification-btn" :aria-expanded="isDropdownOpen">
      <i class="fas fa-bell"></i>
      <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu">
      <div class="dropdown-header">
        <h4>Notificaciones ({{ notifications.length }})</h4>
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
          :class="['notification-item', { 'unread': !notif.is_read }]"
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
// Asegúrate de que este axios apunte a tu backend
import axios from '@/axios'; 
import moment from 'moment';

export default {
  name: 'NotificationBell',
  data() {
    return {
      notifications: [],
      loading: false,
      isDropdownOpen: false,
      // Suponemos que la API solo devuelve notificaciones no leídas por defecto
    };
  },
  computed: {
    unreadCount() {
      // Si la API no filtra, filtra aquí. Si la API filtra, esto es simple:
      return this.notifications.length; 
    }
  },
  methods: {
    toggleDropdown() {
      this.isDropdownOpen = !this.isDropdownOpen;
      if (this.isDropdownOpen && this.notifications.length === 0) {
        this.fetchNotifications();
      }
    },
    async fetchNotifications() {
      this.loading = true;
      try {
        // Debes crear un endpoint en el backend para esto: GET /api/notifications
        const response = await axios.get('/api/notifications?rol=almacenista&is_read=false');
        this.notifications = response.data;
      } catch (error) {
        console.error("Error al cargar notificaciones:", error);
      } finally {
        this.loading = false;
      }
    },
    async markAllAsRead() {
      try {
        // Debes crear un endpoint PUT o POST en el backend para marcar como leído
        await axios.put('/api/notifications/mark_all_read?rol=almacenista');
        
        // Actualizar el estado local
        this.notifications = [];
        this.isDropdownOpen = false;
      } catch (error) {
        console.error("Error al marcar como leídas:", error);
      }
    },
    getIcon(tipo) {
        switch(tipo) {
            case 'stock_critico':
                return 'fas fa-exclamation-triangle text-warning';
            case 'tendencia_alta':
                return 'fas fa-chart-line text-success';
            default:
                return 'fas fa-info-circle';
        }
    },
    formatTime(timestamp) {
        // Necesitas instalar 'moment' (npm install moment) o usar Day.js
        return moment(timestamp).fromNow();
    }
  },
  mounted() {
    // Cargar inicial o configurar un intervalo para actualizar cada X minutos
    this.fetchNotifications(); 
  }
};
</script>
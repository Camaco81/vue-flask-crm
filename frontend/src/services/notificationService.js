// src/services/notificationService.js (Nuevo archivo recomendado)
import api from '@/axios'; // Asumiendo que '@/axios' es tu instancia configurada de axios

const notificationService = {
  /**
   * Obtiene las notificaciones no leídas para un rol específico.
   * @param {string} rol_destino - Ej: 'almacenista'
   * @returns {Promise<Array>} Lista de notificaciones
   */
  getUnreadNotifications(rol_destino) {
    // La ruta coincide con el endpoint de Flask que arreglamos
    return api.get(`/api/notifications`, {
      params: {
        rol: rol_destino,
        is_read: false 
      }
    });
  },

  /**
   * Marca todas las notificaciones no leídas de un rol como leídas.
   * @param {string} rol_destino - Ej: 'almacenista'
   */
  markAllAsRead(rol_destino) {
    return api.put(`/api/notifications/mark_all_read`, null, {
      params: {
        rol: rol_destino
      }
    });
  }
};

export default notificationService;
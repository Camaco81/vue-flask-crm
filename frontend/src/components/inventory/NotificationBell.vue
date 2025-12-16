Aquí está el código sin espacios en blanco innecesarios, manteniendo toda la funcionalidad y estructura:

```vue
<template>
<div class="notification-container">
<button @click="toggleDropdown" class="notification-btn" :aria-expanded="showDropdown">
<font-awesome-icon icon="fas fa-bell"/>
<span v-if="notifications.length > 0" class="notification-badge">{{ notifications.length }}</span>
</button>
<div v-if="showDropdown" class="dropdown-menu">
<div class="dropdown-header">
<h4>Alertas ({{ notifications.length }} en lista)</h4>
<button 
v-if="notifications.length > 0" 
@click="markAllAsRead" 
class="mark-read-btn"
>
Descartar todas
</button>
</div>
<div v-if="connectionStatus === 'connecting'" class="loading-state">
Conectando a alertas en tiempo real...
</div>
<div v-else-if="notifications.length === 0" class="empty-state">
<font-awesome-icon icon="fas fa-check-circle" class="text-success" style="margin-right: 5px;"/>
Todo en orden. No hay alertas estacionales o de stock bajo pendientes.
</div>
<div v-else class="notification-list">
<div 
v-for="notif in notifications" 
:key="notif.id" 
:class="['notification-item', notif.type]"
>
<div class="icon">
<font-awesome-icon 
:icon="getIcon(notif.type)" 
:class="getIconClass(notif.type)"
/>
</div>
<div class="content">
<p class="message">{{ notif.message }}</p>
<small v-if="notif.summary" class="details-note">{{ notif.summary }}</small>
<small class="time">{{ formatTime(notif.timestamp) }}</small>
</div>
<button @click.stop="markOneAsRead(notif.id)" class="dismiss-btn" aria-label="Descartar alerta">
<font-awesome-icon icon="fas fa-times"/>
</button>
</div>
</div>
</div>
</div>
</template>

<script>
import io from 'socket.io-client';
import apiClient from '../../axios'; 
const SOCKET_URL = apiClient.defaults.baseURL;

export default {
name: 'NotificationBell',
data() {
return {
socket: null,
notifications: [],
showDropdown: false,
connectionStatus: 'connecting',
user: {
id: 'almacenista_unico_cliente_12345',
},
};
},
methods: {
toggleDropdown() {
this.showDropdown = !this.showDropdown;
if (this.showDropdown && this.notifications.length > 0) {
this.markAllAsSeen();
}
},
closeDropdown(event) {
if (this.$el && !this.$el.contains(event.target)) {
this.showDropdown = false;
}
},
markAllAsSeen() {
if (!this.socket || this.notifications.length === 0) return;
const alertIdsToMark = this.notifications.map(n => n.id);
this.socket.emit('mark_as_read', {
user_id: this.user.id,
alert_ids: alertIdsToMark 
});
},
markAllAsRead() {
if (!this.socket || this.notifications.length === 0) return;
this.markAllAsSeen();
this.notifications = []; 
this.showDropdown = false;
},
markOneAsRead(alertId) {
if (!this.socket) return;
this.socket.emit('mark_as_read', {
user_id: this.user.id,
alert_ids: [alertId]
});
this.notifications = this.notifications.filter(n => n.id !== alertId);
},
setupSocketConnection() {
this.socket = io(SOCKET_URL, {
transports: ['websocket', 'polling'],
reconnectionAttempts: 5,
reconnectionDelay: 1000
});
this.socket.on('connect', () => {
this.connectionStatus = 'connected';
console.log('DEBUG: Conectado a WebSockets. Uniéndose a sala...');
this.socket.emit('join_dashboard', { user_id: this.user.id });
});
this.socket.on('disconnect', () => {
this.connectionStatus = 'disconnected';
console.log('DEBUG: Desconectado de WebSockets.');
});
this.socket.on('connect_error', (err) => {
this.connectionStatus = 'disconnected';
console.error('ERROR de conexión WebSocket:', err.message);
});
this.socket.on('new_alerts', (data) => {
console.log('DEBUG: Nuevas alertas recibidas:', data.alerts);
const newAlerts = data.alerts.filter(
alert => !this.notifications.some(existing => existing.id === alert.id)
);
this.notifications = [...newAlerts, ...this.notifications];
});
},
formatTime(timestamp) {
const date = new Date(timestamp * 1000); 
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
getIcon(type) {
switch (type) {
case 'tendencia_alta':
return 'fas fa-chart-line'; 
case 'tendencia_media':
return 'fas fa-bell'; 
case 'promocion_baja':
return 'fas fa-arrow-down'; 
case 'stock_bajo':
case 'stock_critico': 
return 'fas fa-exclamation-triangle'; 
default:
return 'fas fa-info-circle';
}
},
getIconClass(type) {
switch (type) {
case 'tendencia_alta':
return 'text-danger';
case 'tendencia_media':
return 'text-info'; 
case 'promocion_baja':
return 'text-warning';
case 'stock_bajo':
case 'stock_critico':
return 'text-danger'; 
default:
return 'text-muted';
}
}
},
mounted() {
this.setupSocketConnection(); 
document.addEventListener('click', this.closeDropdown);
},
beforeUnmount() { 
if (this.socket) {
this.socket.disconnect();
}
document.removeEventListener('click', this.closeDropdown);
}
};
</script>

<style scoped>
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
background-color: #e53e3e;
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
width: 380px; 
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
color: #4299e1;
font-size: 0.8rem;
cursor: pointer;
transition: opacity 0.2s;
}
.mark-read-btn:hover {
opacity: 0.7;
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
background-color: #f7fafc; 
}
.notification-item:hover {
background-color: #f0f4f7;
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
font-weight: 600;
line-height: 1.3;
}
.details-note {
display: block;
margin-top: 3px;
font-size: 0.75rem;
color: #4a5568;
font-weight: normal;
}
.time {
font-size: 0.75rem;
color: #718096;
}
.empty-state, .loading-state {
padding: 15px;
color: #718096;
font-style: italic;
text-align: center;
}
.dismiss-btn {
background: none;
border: none;
color: #a0aec0;
cursor: pointer;
font-size: 0.8rem;
padding: 0 5px;
align-self: flex-start;
margin-top: 5px;
transition: color 0.2s;
}
.dismiss-btn:hover {
color: #e53e3e;
}
.text-danger {
color: #e53e3e;
}
.text-info {
color: #4299e1;
}
.text-warning {
color: #ecc94b;
}
.text-success {
color: #38a169;
}
.notification-item.tendencia_alta, .notification-item.stock_bajo, .notification-item.stock_critico {
border-left: 4px solid #e53e3e;
} 
.notification-item.tendencia_media {
border-left: 4px solid #4299e1;
}
.notification-item.promocion_baja {
border-left: 4px solid #ecc94b;
}
</style>

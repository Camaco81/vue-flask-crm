// main.js (o main.ts)
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import apiClient from './axios'; 
import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

// Importar Íconos nuevos y existentes (Asegúrate de que estén instalados: npm install @fortawesome/free-solid-svg-icons)
import { 
    faUser, 
    faCreditCard, 
    faBars, 
    faCheckCircle, // (Regulares)
    
    // NUEVOS ÍCONOS PARA EL DASHBOARD
    faUsers, // Clientes
    faShoppingCart, // Ventas
    faUserCircle, // Avatar
    faSignOutAlt, // Cerrar Sesión
    faBell, // Notificaciones
    faCog, // Configuración
    faUserPlus, // Agregar Cliente
    faCashRegister, // Registrar Venta
    faTimes // Ícono de "Cerrar" (X) para el menú móvil
} from '@fortawesome/free-solid-svg-icons';

// Añadir TODOS los íconos a la librería global
library.add(
    faUser, 
    faCreditCard, 
    faBars, 
    faCheckCircle, 
    
    // NUEVOS
    faUsers, 
    faShoppingCart, 
    faUserCircle, 
    faSignOutAlt, 
    faBell, 
    faCog, 
    faUserPlus, 
    faCashRegister,
    faTimes
);

const app = createApp(App);

// Usa la instancia de Axios en toda la aplicación
app.config.globalProperties.$http = apiClient;

// Registrar el componente globalmente
app.component('font-awesome-icon', FontAwesomeIcon);

app.use(router);

app.mount('#app');
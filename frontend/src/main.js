import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import apiClient from './axios'; // Importa la instancia de Axios configurada

const app = createApp(App);

// Usa la instancia de Axios en toda la aplicación
app.config.globalProperties.$http = apiClient;

app.use(router);

app.mount('#app');
import axios from 'axios';
import router from './router'; // Importa el router para manejar la redirección

// Crea una instancia de Axios con la URL base del backend
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL, // O process.env.VUE_APP_API_URL
  headers: {
    'Content-Type': 'application/json'
  }
});


// Interceptor de solicitudes: se ejecuta antes de cada petición
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Interceptor de respuestas: maneja los errores globales, como el 401
apiClient.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    if (error.response && error.response.status === 401) {
      // Si la respuesta es 401 (Unauthorized), significa que el token es inválido o ha expirado.
      // Borra el token, muestra un mensaje y redirige al login.
      localStorage.removeItem('access_token');
      console.error("Token expirado o inválido. Redirigiendo al login.");
      router.push('/login');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
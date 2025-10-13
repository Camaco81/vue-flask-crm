// frontend/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import LandingPage from '@/components/LandingPage.vue';
import HomeView from '../views/HomeView.vue'; // Asumo que HomeView es una página genérica o de landing
import LoginForm from '../components/LoginForm.vue';
import RegisterForm from '../components/RegisterForm.vue';
// import BackButton from '@/components/BackButton.vue'; // No se usa directamente en rutas

// --- Importaciones para el Rol de Administrador ---
import AdminDashboard from '@/components/admin/AdminDashboard.vue';
import UserManagement from '@/components/admin/UserManagement.vue';
import AdminGeneralReports from '@/components/admin/GeneralReports.vue'; // Importa el reporte general para admin

// --- Importaciones para el Rol de Vendedor ---
import VendedorDashboard from '@/components/vendedor/VendedorDashboard.vue';
import VendedorCustomersComponent from '@/components/vendedor/CustomersComponent.vue'; // Componente de clientes para vendedor
import VendedorProductsComponent from '@/components/vendedor/ProductsComponent.vue'; // Componente de productos para vendedor
import VendedorOrdersComponent from '@/components/vendedor/SalesComponent.vue'; // Componente de órdenes/ventas para vendedor
import VendedorAnalyticsComponent from '@/components/vendedor/AnalyticsComponent.vue'; // Componente de analíticas para vendedor
import VendedorUserProfile from '@/components/vendedor/UserProfile.vue'; // Componente de perfil para vendedor

const routes = [
  { path: '/', name: 'LandingPage', component: LandingPage },
  { path: '/home', name: 'Home', component: HomeView }, // Considera si esta ruta es realmente necesaria o si la landing es suficiente
  { path: '/login', name: 'Login', component: LoginForm },
  { path: '/register', name: 'Register', component: RegisterForm },

  // --- RUTAS DEL ADMINISTRADOR (role_id = 1) ---
  { 
    path: '/dashboard', 
    name: 'AdminDashboard', 
    component: AdminDashboard, 
    meta: { requiresAuth: true, requiredRole: 1 } // Solo Administradores
  },
  { 
    path: '/admin/users', 
    name: 'UserManagement', 
    component: UserManagement, 
    meta: { requiresAuth: true, requiredRole: 1 } // Solo Administradores
  },
  { 
    path: '/admin/general-reports', // Renombrado para ser específico de Admin
    name: 'AdminGeneralReports', 
    component: AdminGeneralReports, 
    meta: { requiresAuth: true, requiredRole: 1 } // Solo Administradores
  },

  // --- RUTAS DEL VENDEDOR (role_id = 2) ---
  { 
    path: '/vendedor/vendedor-dasboard', // Ruta principal para el vendedor
    name: 'VendedorDashboard', 
    component: VendedorDashboard, 
    meta: { requiresAuth: true, requiredRole: 2 } // Solo Vendedores
  },
  { 
    path: '/vendedor/customers', // Rutas específicas para el vendedor
    name: 'VendedorCustomers', 
    component: VendedorCustomersComponent, 
    meta: { requiresAuth: true, requiredRole: 2 } // Solo Vendedores
  },
  { 
    path: '/vendedor/products', 
    name: 'VendedorProducts', 
    component: VendedorProductsComponent, 
    meta: { requiresAuth: true, requiredRole: 2 } // Solo Vendedores
  },
  { 
    path: '/vendedor/sales', // Cambiado a 'orders' para ser coherente con el componente OrdersComponent.vue
    name: 'VendedorSales', 
    component: VendedorOrdersComponent, 
    meta: { requiresAuth: true, requiredRole: 2 } // Solo Vendedores
  },
  { 
    path: '/vendedor/analytics', 
    name: 'VendedorAnalytics', 
    component: VendedorAnalyticsComponent, 
    meta: { requiresAuth: true, requiredRole: 2 } // Solo Vendedores
  },
  { 
    path: '/vendedor/profile', // Perfil específico del vendedor
    name: 'VendedorProfile', 
    component: VendedorUserProfile, 
    meta: { requiresAuth: true, requiredRole: 2 } // Solo Vendedores
  },
  // La ruta '/profile' sin prefijo de rol se puede dejar si es un perfil genérico
  // o se reemplaza completamente por '/vendedor/profile' y '/admin/profile'

  // --- RUTA DE PERFIL GENÉRICO (si lo mantienes, para ambos roles o para el que no tenga uno específico) ---
  // Si tanto admin como vendedor tienen su propio 'UserProfile.vue' en sus carpetas,
  // entonces esta ruta genérica no sería necesaria.
  // Si el componente 'UserProfile.vue' de la carpeta 'vendedor' se usa para AMBOS roles,
  // entonces la ruta y el meta.requiredRole deberían ser más flexibles o duplicarse.
  // Por ahora, asumimos que 'vendedor/UserProfile.vue' es el que se usa para el vendedor.

  // --- RUTA POR DEFECTO PARA NO AUTORIZADO (opcional) ---
  // { path: '/unauthorized', name: 'Unauthorized', component: UnauthorizedPage }

  // --- CATCH-ALL (404) ---
  // { path: '/:catchAll(.*)', redirect: '/' } // Redirige cualquier ruta no encontrada a la landing
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiredRole = to.meta.requiredRole;
  const isAuthenticated = localStorage.getItem('access_token');

  // 🌟 LÓGICA DE OBTENCIÓN Y MANEJO DE ERRORES DEL ROL 🌟
  const userInfoString = localStorage.getItem('user_info');
  let userRoleId = null;

  // 1. Verifica que la cadena no sea nula, vacía o la cadena literal "undefined"
  if (userInfoString && userInfoString !== 'undefined') {
    try {
      const user = JSON.parse(userInfoString);
      userRoleId = user.role_id;
    } catch (e) {
      // 2. Si el JSON es inválido (como "undefined"), limpiamos y registramos el error
      console.error("Error al parsear user_info:", e);
      localStorage.removeItem('user_info');
      localStorage.removeItem('access_token');
      // Forzar la no autenticación si la data es corrupta
      return next('/login');
    }
  }

  if (requiresAuth && !isAuthenticated) {
    // Caso 1: Requiere auth y no autenticado
    next('/login');
  } else if (requiresAuth && isAuthenticated && requiredRole && userRoleId !== requiredRole) {
    // Caso 2: Ruta protegida, autenticado, pero el rol no coincide
    console.warn(`Acceso denegado. Ruta: ${to.path}, Rol requerido: ${requiredRole}, Rol del usuario: ${userRoleId}`);

    // 🌟 Lógica de Redirección basada en el Rol Actual 🌟
    if (userRoleId === 1) { // Admin
      next('/dashboard');
    } else if (userRoleId === 2) { // Vendedor
      next('/vendedor/vendedor-dasboard');
    } else {
      // Rol desconocido o nulo: Cerrar sesión forzosamente
      next('/login');
    }
  } else {
    // Caso 3: Todo bien, o ruta pública
    next();
  }
});

export default router;

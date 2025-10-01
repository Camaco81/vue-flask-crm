// frontend/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import LandingPage from '@/components/LandingPage.vue';
import HomeView from '../views/HomeView.vue';
import HomeDashboard from '../components/HomeDashboard.vue';
import AdminDashboard from '@/components/AdminDashboard.vue';
import LoginForm from '../components/LoginForm.vue';
import RegisterForm from '../components/RegisterForm.vue';
import Customers from '../components/CustomersComponent.vue';
import UserProfile from '../components/UserProfile.vue'; // Nuevo
import Products from '../components/ProductsComponent.vue'; // Nuevo
import OrdersComponent from '@/components/OrdersComponent.vue';
import AnalyticsComponent from '@/components/AnalyticsComponent.vue';


const routes = [
  { path: '/', name: 'LandingPage', component: LandingPage },
  { path: '/home', name: 'Home', component: HomeView },
  { path: '/login', name: 'Login', component: LoginForm },
  { path: '/register', name: 'Register', component: RegisterForm },
  { path: '/dashboard', name: 'HomeDashboard', component: HomeDashboard, meta: { requiresAuth: true } },
  { path: '/dashboard-admin', name: 'AdminDashboard', component: AdminDashboard, meta: { requiresAuth: true } },
  { path: '/customers', name: 'Customers', component: Customers, meta: { requiresAuth: true } },
  { path: '/profile', name: 'UserProfile', component: UserProfile, meta: { requiresAuth: true } }, // Ruta protegida
  { path: '/products', name: 'Products', component: Products, meta: { requiresAuth: true } }, // Ruta protegida
  { path: '/orders', name: 'Orders', component: OrdersComponent, meta: { requiresAuth: true } }, // Ruta protegida
  { path: '/analytics', name: 'Analytics', component: AnalyticsComponent, meta: { requiresAuth: true } } // Ruta protegida


];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// --- Guard de navegación para proteger las rutas ---
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiredRole = to.matched.some(record => record.meta.requiresRole) ? to.matched.find(record => record.meta.requiresRole).meta.requiresRole : null;

  const isAuthenticated = localStorage.getItem('access_token');
  const userRoleId = parseInt(localStorage.getItem('user_role_id')); // <--- Usamos el ID del rol

  if (requiresAuth && !isAuthenticated) {
    next('/login'); // No autenticado, redirigir al login
  } else if (requiresAuth && isAuthenticated && requiredRole !== null && userRoleId !== requiredRole) {
    // Autenticado, pero el rol no coincide con el requerido para la ruta
    console.warn(`Intento de acceso denegado a ruta protegida por rol. Rol requerido: ${requiredRole}, Rol del usuario: ${userRoleId}`);
    
    // Redirige a una página de "Acceso Denegado" o a su propio dashboard
    if (userRoleId === 1) { // Si es admin, redirige al dashboard de admin
        next('dashboard-admins'); 
    } else if (userRoleId === 2) { // Si es vendedor, redirige al dashboard de vendedor
        next('dashboard'); 
    } else {
        next('/'); // O a la página de inicio por defecto
    }
    
  } else {
    next(); // Acceso permitido
  }
});

export default router;
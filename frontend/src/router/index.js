// frontend/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import LandingPage from '@/components/LandingPage.vue';
import HomeView from '../views/HomeView.vue';
import HomeDashboard from '../components/HomeDashboard.vue';
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

// Navigation Guard (sin cambios)
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const isAuthenticated = localStorage.getItem('access_token');
  if (requiresAuth && !isAuthenticated) {
    next('/login');
  } else {
    next();
  }
});

export default router;
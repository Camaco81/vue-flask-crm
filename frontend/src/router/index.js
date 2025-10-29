// frontend/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import LandingPage from '@/components/LandingPage.vue';
import HomeView from '../views/HomeView.vue';
import LoginForm from '../components/LoginForm.vue';
import RegisterForm from '../components/RegisterForm.vue';

// --- Importaciones para el Rol de Administrador (role_id = 1) ---
import AdminDashboard from '@/components/admin/AdminDashboard.vue';
import UserManagement from '@/components/admin/UserManagement.vue';
import AdminGeneralReports from '@/components/admin/GeneralReports.vue';

// --- Importaciones para el Rol de Vendedor (role_id = 2) ---
import VendedorDashboard from '@/components/vendedor/VendedorDashboard.vue';
import VendedorCustomersComponent from '@/components/vendedor/CustomersComponent.vue';
// 🚨 Vendedor ya NO gestiona productos, solo los consulta, pero su vista de ventas los necesita
// Dejamos la importación si la vista de ventas la requiere para los selects
import VendedorProductsComponent from '@/components/vendedor/ProductsComponent.vue'; 
import VendedorOrdersComponent from '@/components/vendedor/SalesComponent.vue';
import VendedorUserProfile from '@/components/vendedor/UserProfile.vue';

// --- 🚨 NUEVAS IMPORTACIONES para el Rol de Almacenista (role_id = 3) ---
import AlmacenistaDashboard from '@/components/inventory/AlmacenistaDashboard.vue'; // Nuevo Dashboard de Almacenista
import InventoryManagement from '@/components/inventory/ProductsComponent.vue'; // Gestión de productos/inventario

const routes = [
 { path: '/', name: 'LandingPage', component: LandingPage },
 { path: '/home', name: 'Home', component: HomeView },
 { path: '/login', name: 'Login', component: LoginForm },
 { path: '/register', name: 'Register', component: RegisterForm },

 // --- RUTAS DEL ADMINISTRADOR (role_id = 1) ---
 {
  path: '/dashboard',
  name: 'AdminDashboard',
  component: AdminDashboard,
  meta: { requiresAuth: true, requiredRole: 1 }
 },
 {
  path: '/admin/users',
  name: 'UserManagement',
  component: UserManagement,
  meta: { requiresAuth: true, requiredRole: 1 }
 },
 {
  path: '/admin/general-reports',
  name: 'AdminGeneralReports',
  component: AdminGeneralReports,
  meta: { requiresAuth: true, requiredRole: 1 }
 },

 // --- RUTAS DEL VENDEDOR (role_id = 2) ---
 {
  path: '/vendedor/vendedor-dasboard', // Ruta principal
  name: 'VendedorDashboard',
  component: VendedorDashboard,
  meta: { requiresAuth: true, requiredRole: 2 }
 },
 {
  path: '/vendedor/customers',
  name: 'VendedorCustomers',
  component: VendedorCustomersComponent,
  meta: { requiresAuth: true, requiredRole: 2 }
 },
 {
  path: '/vendedor/products', // El vendedor solo consulta la lista de productos (no gestiona)
  name: 'VendedorProducts',
  component: VendedorProductsComponent,
  meta: { requiresAuth: true, requiredRole: 2 }
 },
 {
  path: '/vendedor/sales',
  name: 'VendedorSales',
  component: VendedorOrdersComponent,
  meta: { requiresAuth: true, requiredRole: 2 }
 },

 {
  path: '/vendedor/profile',
  name: 'VendedorProfile',
  component: VendedorUserProfile,
  meta: { requiresAuth: true, requiredRole: 2 }
 },

 // --- 🚨 NUEVAS RUTAS DEL ALMACENISTA (role_id = 3) ---
 {
  path: '/almacenista/dashboard',
  name: 'AlmacenistaDashboard',
  component: AlmacenistaDashboard,
  meta: { requiresAuth: true, requiredRole: 3 } // Solo Almacenistas
 },
 {
  path: '/almacenista/inventory', // Ruta principal para gestionar productos
  name: 'InventoryManagement',
  component: InventoryManagement,
  meta: { requiresAuth: true, requiredRole: 3 } // Solo Almacenistas
 },

 // --- CATCH-ALL (404) ---
 // { path: '/:catchAll(.*)', redirect: '/' } 
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

 if (userInfoString && userInfoString !== 'undefined') {
  try {
   const user = JSON.parse(userInfoString);
   userRoleId = user.role_id;
  } catch (e) {
   console.error("Error al parsear user_info:", e);
   localStorage.removeItem('user_info');
   localStorage.removeItem('access_token');
   return next('/login');
  }
 }

 if (requiresAuth && !isAuthenticated) {
  // Caso 1: Requiere auth y no autenticado
  next('/login');
 } else if (requiresAuth && isAuthenticated && requiredRole && userRoleId !== requiredRole) {
  // Caso 2: Ruta protegida, autenticado, pero el rol no coincide
  console.warn(`Acceso denegado. Ruta: ${to.path}, Rol requerido: ${requiredRole}, Rol del usuario: ${userRoleId}`);

  // 🚨 Lógica de Redirección basada en el Rol Actual (Actualizada para rol 3) 🚨
  if (userRoleId === 1) { // Admin
   next('/dashboard');
  } else if (userRoleId === 2) { // Vendedor
   next('/vendedor/dashboard'); // Corregido: Usar '/vendedor/dashboard'
  } else if (userRoleId === 3) { // 🚨 Nuevo: Almacenista
   next('/almacenista/dashboard');
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
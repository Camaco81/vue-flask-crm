// src/store/auth.js

import { reactive } from 'vue';

export const authStore = reactive({
  isAuthenticated: false,
  user: null
});
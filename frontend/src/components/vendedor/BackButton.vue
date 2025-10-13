<template>
  <button @click="goBack" class="back-button">
    <span class="icon">⬅️</span>
    Regresar
  </button>
</template>

<script>
export default {
  methods: {
    goBack() {
      // Navega a la página anterior en el historial de navegación
      this.$router.go(-1); 
    }
  }
};
</script>

<style scoped>
.back-button {
  background-color: #667eea;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.3s ease;
}

.back-button:hover {
  background-color: #5667d4;
}

.icon {
  font-size: 1.2rem;
}
</style>
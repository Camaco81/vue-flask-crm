<template>
  <Transition name="modal">
    <!-- El fondo oscuro del modal. Utilizamos props.show, aunque 'show' solo funciona en el template. -->
    <div v-if="props.show" class="modal-mask" @click="$emit('close')">
      <!-- El contenedor central del modal -->
      <div class="modal-wrapper">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="text-xl font-bold text-gray-800">Generación de Código de Cancelación</h3>
            <button class="modal-default-button" @click="$emit('close')">
                &times;
            </button>
          </div>

          <div class="modal-body">
            <p class="text-sm text-gray-600 mb-4">
              Este código alfanumérico único se asociará al crédito y será la clave para gestionar su cancelación en el futuro.
            </p>

            <!-- Display del Código -->
            <div class="p-5 bg-yellow-50 border-2 border-yellow-300 rounded-xl shadow-md text-center mb-6">
              <label class="block text-md font-bold text-yellow-800 mb-2">CÓDIGO ÚNICO DE CANCELACIÓN</label>
              <p class="text-3xl font-mono font-extrabold text-gray-900 select-all tracking-wider">
                {{ cancellationCode }}
              </p>
            </div>
            
            <!-- Botón para Regenerar -->
            <button
              type="button"
              @click="generateInitialCode()"
              class="w-full py-2 px-4 mb-4 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 transition duration-150 flex items-center justify-center"
            >
              <!-- Icono de Actualizar (Lucide-react RefreshCw) -->
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block mr-2">
                <path d="M3 2v6h6"/><path d="M21 12a9 9 0 0 0-9-9c-2.342 0-4.52 1.05-6 2.7l-3-3"/><path d="M21 22v-6h-6"/><path d="M3 12a9 9 0 0 0 9 9c2.342 0 4.52-1.05 6-2.7l3 3"/>
              </svg>
              Regenerar Código
            </button>
          </div>

          <div class="modal-footer">
            <button
              class="w-full py-3 px-4 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 shadow-lg transition duration-150"
              @click="confirmCode"
            >
              Confirmar y Usar Código
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>
<script setup>
import { ref, defineEmits, defineProps, defineExpose } from 'vue';

// Definir las propiedades que el componente puede recibir
// Se asigna a una constante para mejorar la robustez sintáctica y evitar el error de compilación.
const props = defineProps({
  show: {
    type: Boolean,
    required: true
  }
});

// Define los eventos que el componente puede emitir al padre
const emit = defineEmits(['close', 'codeGenerated']);

// Estado local para el código de cancelación
const cancellationCode = ref('');

// Función para generar un código alfanumérico único
const generateCancellationCode = (length = 10) => {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  const charactersLength = characters.length;
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
};

// Generar el código inicial al abrir el modal
const generateInitialCode = () => {
    cancellationCode.value = generateCancellationCode(10);
};

// Función para confirmar y emitir el código al componente padre
const confirmCode = () => {
  if (cancellationCode.value) {
    emit('codeGenerated', cancellationCode.value);
    emit('close');
  }
};

// Exponer la función de inicialización para que el padre pueda llamarla
defineExpose({
    generateInitialCode
});

// Generar el código alfanumérico inicial al cargar el componente
generateInitialCode();

</script>

<style scoped>
/* Estilos Modales - Adaptados para Tailwind pero definidos aquí */
.modal-mask {
  position: fixed;
  z-index: 9998;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  transition: opacity 0.3s ease;
}

.modal-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-container {
  width: 90%;
  max-width: 450px;
  margin: 0px auto;
  padding: 20px 30px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.33);
  transition: all 0.3s ease;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 1rem;
}

.modal-default-button {
  font-size: 2rem;
  line-height: 1;
  color: #a0aec0;
  padding: 0 0.5rem;
  cursor: pointer;
  background: none;
  border: none;
}

/* Transiciones */
.modal-enter-from {
  opacity: 0;
}

.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  -webkit-transform: scale(1.1);
  transform: scale(1.1);
}
</style>
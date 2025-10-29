<template>
  <div class="autocomplete-container">
    <input
      type="text"
      :placeholder="placeholder"
      v-model="searchText"
      @input="handleInput"
      @keydown.down.prevent="moveDown"
      @keydown.up.prevent="moveUp"
      @keydown.enter.prevent="selectHighlighted"
      @focus="showSuggestions = true"
      @blur="handleBlur"
      ref="input"
    />
    
    <div v-if="showSuggestions && filteredItems.length > 0" class="suggestions-list">
      <div 
        v-for="(item, index) in filteredItems" 
        :key="item.id"
        class="suggestion-item"
        :class="{ 'highlighted': index === highlightedIndex }"
        @mousedown.prevent="selectItem(item)"
      >
        {{ item[labelKey] }}
        <span v-if="secondaryLabelKey" class="secondary-label">({{ item[secondaryLabelKey] }})</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AutocompleteSearch',
  props: {
    items: {
      type: Array,
      required: true
    },
    placeholder: {
      type: String,
      default: 'Buscar...'
    },
    labelKey: {
      type: String,
      required: true
    },
    secondaryLabelKey: {
      type: String,
      default: null
    },
    modelValue: {
      type: [String, Number, null],
      default: null
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      searchText: '',
      showSuggestions: false,
      highlightedIndex: -1,
    };
  },
  computed: {
    filteredItems() {
      // Mostrar sugerencias solo si hay al menos 2 caracteres o si no se ha seleccionado nada aún
      if (this.searchText.length < 2 && !this.modelValue) return [];

      const lowerCaseSearch = this.searchText.toLowerCase();
      
      return this.items.filter(item => {
        // Asegurar que la clave principal es un string
        const primaryText = String(item[this.labelKey] || '').toLowerCase();
        const primaryMatch = primaryText.includes(lowerCaseSearch);

        let secondaryMatch = false;
        if (this.secondaryLabelKey) {
            // 🚨 SOLUCIÓN AL ERROR: Convertir el valor a String antes de usar toLowerCase() 🚨
            const secondaryText = String(item[this.secondaryLabelKey] || '').toLowerCase();
            secondaryMatch = secondaryText.includes(lowerCaseSearch);
        }
        
        return primaryMatch || secondaryMatch;
      }).slice(0, 10);
    }
  },
  watch: {
    // Sincronizar el texto del input con el modelValue cuando se selecciona un ítem
    modelValue(newVal) {
      if (!newVal) {
        this.searchText = '';
      } else {
         const selectedItem = this.items.find(item => item.id === newVal);
         if (selectedItem) {
             this.searchText = selectedItem[this.labelKey];
         }
      }
    }
  },
  methods: {
    handleInput() {
      this.highlightedIndex = -1;
      this.showSuggestions = true;
      // Limpiar el modelValue inmediatamente para forzar una nueva selección
      this.$emit('update:modelValue', null); 
    },
    selectItem(item) {
      this.searchText = item[this.labelKey];
      this.$emit('update:modelValue', item.id);
      this.showSuggestions = false;
      this.$refs.input.blur();
    },
    handleBlur() {
        // Usar un pequeño retraso para permitir clics en las sugerencias
        setTimeout(() => {
            this.showSuggestions = false;
            // Si hay texto pero no hay un ítem válido seleccionado (modelValue es null), limpiar
            if (!this.modelValue && this.searchText) {
                this.searchText = '';
            }
        }, 150);
    },
    moveDown() {
      if (this.filteredItems.length === 0) return;
      this.highlightedIndex = (this.highlightedIndex + 1) % this.filteredItems.length;
    },
    moveUp() {
      if (this.filteredItems.length === 0) return;
      this.highlightedIndex = (this.highlightedIndex - 1 + this.filteredItems.length) % this.filteredItems.length;
    },
    selectHighlighted() {
      if (this.highlightedIndex !== -1) {
        this.selectItem(this.filteredItems[this.highlightedIndex]);
      }
    }
  }
}
</script>

<style scoped>
/* Los estilos del AutocompleteSearch.vue que incluiste previamente */
.autocomplete-container {
  position: relative;
  width: 100%;
}

.autocomplete-container input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  background: white;
  border: 1px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 0.5rem 0.5rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  max-height: 250px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 10px 15px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f4f8;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.highlighted {
  background-color: #f0f4f8;
  color: #667eea;
}

.secondary-label {
    font-size: 0.85rem;
    color: #718096;
    margin-left: 10px;
}
</style>
const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true
})

const path = require('path');
// Importar dotenv para cargar manualmente las variables de entorno
const dotenv = require('dotenv');

// Carga manual del archivo .env.development para garantizar que se inyecte
if (process.env.NODE_ENV === 'development') {
  dotenv.config({ 
    path: path.resolve(__dirname, '.env.development') 
  });
}

module.exports = {
  // Aquí puedes tener otras configuraciones de Vue CLI, si las tienes.

  // Esta sección inyecta las variables de entorno en el cliente
  configureWebpack: {
    plugins: [
      // Webpack DefinePlugin es lo que hace que process.env funcione
      new (require('webpack').DefinePlugin)({
        // Asegúrate de que solo VUE_APP_API_URL se inyecte correctamente
        'process.env.VUE_APP_API_URL': JSON.stringify(process.env.VUE_APP_API_URL)
      })
    ]
  },

  // Si estás utilizando el historial de Vue Router
  publicPath: process.env.NODE_ENV === 'production'
    ? '/' // o la ruta de despliegue si es diferente
    : '/', // Dejamos en '/' para desarrollo
};
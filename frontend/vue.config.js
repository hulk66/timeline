const path = require('path');

module.exports = {
  // use this to build
  // assetsDir: '../static',
  // outputDir: '../backend/timeline/templates',
  // ---
  publicPath: '',
  runtimeCompiler: undefined,
  productionSourceMap: undefined,
  parallel: undefined,
  css: undefined,



  devServer: {
    proxy: {
      
      '/albums': {
        target: 'http://localhost:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/photos': {
        target: 'http://localhost:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/admin': {
        target: 'http://localhost:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/inspect': {
        target: 'http://localhost:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/api': {
        target: 'http://localhost:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      }
    }
  },

  "transpileDependencies": [
    "vuetify"
  ]
}

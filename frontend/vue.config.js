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

  configureWebpack:{
    optimization: {
      splitChunks: {
        minSize: 10000,
        maxSize: 250000,
      }
    }
  },

  devServer: {
    disableHostCheck: true,
    proxy: {
      '/albums': {
        target: 'http://127.0.0.1:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/assets': {
        target: 'http://127.0.0.1:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/admin': {
        target: 'http://127.0.0.1:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/inspect': {
        target: 'http://127.0.0.1:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/api': {
        target: 'http://127.0.0.1:5000',
        ws: false,
        changeOrigin: true,
        autoRewrite: true,
      }
    }
    
    
  },

  "transpileDependencies": [
    "vuetify"
  ]
}

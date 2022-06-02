module.exports = {

  // publicPath: process.env.TIMELINE_BASEPATH,

  publicPath: './',
  
  configureWebpack: {
    devtool: "source-map"
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
  transpileDependencies: [
    'vuetify'
  ]
}

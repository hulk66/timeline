let apiHost= process.env.BE_HOST || '127.0.0.1'
let apiPort= process.env.BE_PORT || '5000'
let apiUrl= 'http://'+apiHost+':'+apiPort+"/timeline"

console.log(`Configuring Vue, apiURL:${apiUrl}`)

module.exports = {

  publicPath: './',
  
  configureWebpack: {
    devtool: "source-map"
  },
  
  devServer: {
    disableHostCheck: true,
    proxy: {
      '/albums': {
        target: apiUrl,
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/assets': {
        target: apiUrl,
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/admin': {
        target: apiUrl,
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/inspect': {
        target: apiUrl,
        ws: false,
        changeOrigin: true,
        autoRewrite: true
      },

      '/api': {
        target: apiUrl,
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

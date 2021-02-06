const DYNAMIC_CACHE_NAME = 'apollo-cache-dynamic-v1';
const STATIC_CACHE_NAME = 'apollo-cache-static-v1';

self.addEventListener('install', (event) => {
    // event.waitUntil(
    //     caches.open(STATIC_CACHE_NAME)
    //         .then(cache => {
    //             cache.addAll([
    //                 '/pwa/',
    //                 '/pwa/static/css/login.css',
    //                 '/pwa/static/js/app.js',
    //                 '/pwa/static/vendor/bootstrap/css/bootstrap.min.css',
    //                 '/pwa/static/vendor/dexie/dexie.js',
    //                 '/pwa/static/vendor/vue/vue.js',
    //             ])
    //         })
    // );
});
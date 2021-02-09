const DYNAMIC_CACHE_NAME = 'apollo-cache-dynamic-v1';
const STATIC_CACHE_NAME = 'apollo-cache-static-v1';

const CACHED_URLS = [
    '/pwa/',
    '/pwa/static/css/main.css',
    '/pwa/static/js/app.js',
    '/pwa/static/js/client.js',
    '/pwa/static/vendor/animate.css/animate.min.css',
    '/pwa/static/vendor/bootstrap/css/bootstrap.min.css',
    '/pwa/static/vendor/bootstrap/css/bootstrap.rtl.min.css',
    '/pwa/static/vendor/bootstrap/js/bootstrap.min.js',
    '/pwa/static/vendor/dexie/dexie.min.js',
    '/pwa/static/vendor/image-blob-reduce/image-blob-reduce.min.js',
    '/pwa/static/vendor/notiflix/notiflix-2.7.0.min.css',
    '/pwa/static/vendor/notiflix/notiflix-2.7.0.min.js',
    '/pwa/static/vendor/vue/vue.min.js',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => cache.addAll(CACHED_URLS)));
});

self.addEventListener('fetch', (event) => {
});
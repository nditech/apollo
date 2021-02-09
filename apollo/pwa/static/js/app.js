if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/pwa/serviceworker.js', {scope: '/pwa/'})
        .then(registration => {
            console.log('service worker registered with scope:', registration.scope);
        }).catch(error => {
            console.error('service worker registration failed:', error);
        });
} else {
    console.log('Not found');
}

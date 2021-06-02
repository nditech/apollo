window.isUpdateAvailable = new Promise((resolve, reject) => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/pwa/serviceworker.js', {scope: '/pwa/'})
      .then(registration => {
        registration.onupdatefound = () => {
          const installingWorker = registration.installing;
          installingWorker.onstatechange = () => {
            switch (installingWorker.state) {
              case 'installed':
                if (navigator.serviceWorker.controller) {
                  // update available
                  resolve(true);
                } else {
                  // no update available
                  resolve(false);
                }

                break;
            }
          };
        };
      })
      .catch(error => console.error('service worker registration failed:', error));
  } else {
    console.error('Cannot use service workers');
  }
});

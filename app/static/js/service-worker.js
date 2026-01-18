/**
 * Service Worker for Background Sync
 * Handles background synchronization of attendance data
 */

const CACHE_NAME = 'attendance-app-v1';
const SYNC_TAG = 'attendance-sync';

// Install event - cache essential resources
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll([
                '/',
                '/static/css/style.css',
                '/static/js/offline-sync.js',
                '/offline-confirmation'
            ]);
        })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Background sync event
self.addEventListener('sync', event => {
    if (event.tag === SYNC_TAG) {
        event.waitUntil(syncAttendanceData());
    }
});

// Periodic background sync (if supported)
self.addEventListener('periodicsync', event => {
    if (event.tag === 'attendance-periodic-sync') {
        event.waitUntil(syncAttendanceData());
    }
});

// Message handler for manual sync requests
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SYNC_NOW') {
        syncAttendanceData().then(() => {
            event.ports[0].postMessage({ success: true });
        }).catch(error => {
            event.ports[0].postMessage({ success: false, error: error.message });
        });
    }
});

async function syncAttendanceData() {
    try {
        // Get offline data from localStorage (we need to communicate with the main thread)
        const clients = await self.clients.matchAll();
        
        for (const client of clients) {
            // Send message to client to perform sync
            client.postMessage({
                type: 'BACKGROUND_SYNC_REQUEST'
            });
        }
        
        return Promise.resolve();
    } catch (error) {
        console.error('Background sync failed:', error);
        throw error;
    }
}

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
    // Only handle GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request).then(response => {
            // Return cached version or fetch from network
            return response || fetch(event.request).catch(() => {
                // If both cache and network fail, return offline page for navigation requests
                if (event.request.mode === 'navigate') {
                    return caches.match('/offline-confirmation');
                }
            });
        })
    );
});
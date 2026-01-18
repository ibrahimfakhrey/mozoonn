/**
 * Offline Sync Manager for Attendance System
 * Handles offline storage and automatic synchronization when online
 */

class OfflineSyncManager {
    constructor() {
        this.storageKey = 'attendance_offline_data';
        this.isOnline = navigator.onLine;
        this.syncInProgress = false;
        this.syncInterval = null;
        this.init();
    }

    init() {
        // Listen for online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Update UI on page load
        this.updateConnectionStatus();
        
        // Try to sync any pending data on page load
        if (this.isOnline) {
            this.syncPendingData();
        }
        
        // Set up periodic sync attempts (every 5 minutes when online)
        this.setupPeriodicSync();
    }

    setupPeriodicSync() {
        // Clear any existing interval
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
        
        // Set up periodic sync every 5 minutes
        this.syncInterval = setInterval(() => {
            if (this.isOnline && this.getPendingDataCount() > 0) {
                this.syncPendingData();
            }
        }, 5 * 60 * 1000); // 5 minutes
    }

    handleOnline() {
        this.isOnline = true;
        this.updateConnectionStatus();
        this.syncPendingData();
        this.showNotification('Connection restored! Syncing pending data...', 'success');
    }

    handleOffline() {
        this.isOnline = false;
        this.updateConnectionStatus();
        this.showNotification('You are offline. Submissions will be saved locally and synced when connection is restored.', 'warning');
    }

    updateConnectionStatus() {
        const statusElement = document.getElementById('connection-status');
        const pendingCount = this.getPendingDataCount();
        
        if (statusElement) {
            if (this.isOnline) {
                statusElement.innerHTML = `
                    <span class="badge bg-success">
                        <i class="fas fa-wifi"></i> Online
                    </span>
                    ${pendingCount > 0 ? `<span class="badge bg-warning ms-2">${pendingCount} pending sync</span>` : ''}
                `;
            } else {
                statusElement.innerHTML = `
                    <span class="badge bg-danger">
                        <i class="fas fa-wifi-slash"></i> Offline
                    </span>
                    ${pendingCount > 0 ? `<span class="badge bg-info ms-2">${pendingCount} saved locally</span>` : ''}
                `;
            }
        }
    }

    saveOfflineData(formData, planId, targetDate) {
        const offlineData = this.getOfflineData();
        const timestamp = new Date().toISOString();
        
        const submissionData = {
            id: this.generateId(),
            planId: planId,
            targetDate: targetDate,
            formData: formData,
            timestamp: timestamp,
            synced: false
        };

        offlineData.push(submissionData);
        localStorage.setItem(this.storageKey, JSON.stringify(offlineData));
        
        this.updateConnectionStatus();
        this.showNotification('Attendance saved offline. Will sync when connection is restored.', 'info');
        
        return submissionData.id;
    }

    getOfflineData() {
        const data = localStorage.getItem(this.storageKey);
        return data ? JSON.parse(data) : [];
    }

    getPendingDataCount() {
        return this.getOfflineData().filter(item => !item.synced).length;
    }

    async syncPendingData() {
        if (this.syncInProgress || !this.isOnline) {
            return;
        }

        const pendingData = this.getOfflineData().filter(item => !item.synced);
        if (pendingData.length === 0) {
            return;
        }

        this.syncInProgress = true;
        this.showSyncProgress(true);

        let successCount = 0;
        let failCount = 0;

        for (const item of pendingData) {
            try {
                const success = await this.syncSingleItem(item);
                if (success) {
                    this.markAsSynced(item.id);
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (error) {
                console.error('Sync error:', error);
                failCount++;
            }
        }

        this.syncInProgress = false;
        this.showSyncProgress(false);
        this.updateConnectionStatus();

        if (successCount > 0) {
            this.showNotification(`Successfully synced ${successCount} attendance submissions!`, 'success');
        }
        if (failCount > 0) {
            this.showNotification(`Failed to sync ${failCount} submissions. Will retry later.`, 'warning');
        }
        
        // Register for background sync to retry failed items
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then(registration => {
                return registration.sync.register('attendance-sync');
            });
        }
    }

    async syncSingleItem(item) {
        try {
            const formData = new FormData();
            
            // Add all form data
            for (const [key, value] of Object.entries(item.formData)) {
                formData.append(key, value);
            }

            const response = await fetch(`/plan/${this.getDayFromPlanId(item.planId)}`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Offline-Sync': 'true',
                    'X-Original-Timestamp': item.timestamp
                }
            });

            return response.ok;
        } catch (error) {
            console.error('Failed to sync item:', error);
            return false;
        }
    }

    markAsSynced(itemId) {
        const offlineData = this.getOfflineData();
        const item = offlineData.find(item => item.id === itemId);
        if (item) {
            item.synced = true;
            localStorage.setItem(this.storageKey, JSON.stringify(offlineData));
        }
    }

    clearSyncedData() {
        const offlineData = this.getOfflineData();
        const pendingData = offlineData.filter(item => !item.synced);
        localStorage.setItem(this.storageKey, JSON.stringify(pendingData));
    }

    getDayFromPlanId(planId) {
        // This should match your plan ID to day mapping
        const dayMap = {
            'sunday': 'sunday',
            'monday': 'monday',
            'tuesday': 'tuesday',
            'wednesday': 'wednesday',
            'thursday': 'thursday'
        };
        return dayMap[planId] || 'today';
    }

    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    showSyncProgress(show) {
        let progressElement = document.getElementById('sync-progress');
        
        if (show && !progressElement) {
            progressElement = document.createElement('div');
            progressElement.id = 'sync-progress';
            progressElement.className = 'position-fixed';
            progressElement.style.cssText = 'top: 70px; right: 20px; z-index: 9999;';
            progressElement.innerHTML = `
                <div class="alert alert-info">
                    <div class="d-flex align-items-center">
                        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                        Syncing offline data...
                    </div>
                </div>
            `;
            document.body.appendChild(progressElement);
        } else if (!show && progressElement) {
            progressElement.remove();
        }
    }
}

// Initialize the offline sync manager and make it globally available
const offlineSyncManager = new OfflineSyncManager();
window.offlineSyncManager = offlineSyncManager;

// Override form submission for attendance forms
document.addEventListener('DOMContentLoaded', function() {
    // Look for the attendance form more broadly - it's the form with method="post" that contains attendance data
    const attendanceForm = document.querySelector('form[method="post"]');
    
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', function(e) {
            if (!navigator.onLine) {
                e.preventDefault();
                
                // Collect form data
                const formData = new FormData(this);
                const formDataObj = {};
                for (let [key, value] of formData.entries()) {
                    formDataObj[key] = value;
                }
                
                // Extract plan info from URL or form
                const planId = window.location.pathname.split('/').pop();
                const targetDate = new Date().toISOString().split('T')[0];
                
                // Save offline
                offlineSyncManager.saveOfflineData(formDataObj, planId, targetDate);
                
                // Redirect to offline confirmation page
                window.location.href = '/offline-confirmation';
            }
        });
    }
});
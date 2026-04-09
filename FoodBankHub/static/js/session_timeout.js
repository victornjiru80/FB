/**
 * Simple Session Timeout - Auto logout after 10 minutes of inactivity
 */

class SimpleSessionTimeout {
    constructor() {
        this.sessionTimeout = 600000; // 10 minutes in milliseconds
        this.logoutUrl = '/logout/';
        this.timeoutId = null;
        
        this.init();
    }
    
    init() {
        // Start the session timeout timer
        this.resetTimer();
        
        // Add event listeners for user activity
        this.addActivityListeners();
    }
    
    addActivityListeners() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.resetTimer();
            }, true);
        });
    }
    
    resetTimer() {
        // Clear existing timer
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        
        // Set new logout timer
        this.timeoutId = setTimeout(() => {
            this.logout();
        }, this.sessionTimeout);
    }
    
    logout() {
        // Clear timer
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        
        // Redirect to logout URL
        window.location.href = this.logoutUrl;
    }
}

// Initialize simple session timeout when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize for authenticated users
    if (document.body.classList.contains('authenticated')) {
        new SimpleSessionTimeout();
    }
});

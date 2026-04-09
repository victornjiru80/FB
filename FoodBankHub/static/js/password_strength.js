/**
 * Password Strength Meter for FoodBankHub Registration Forms
 * Provides real-time feedback on password strength
 */

class PasswordStrengthMeter {
    constructor() {
        this.passwordField = document.getElementById('password1');
        this.confirmField = document.getElementById('password2');
        this.strengthMeter = null;
        this.strengthText = null;
        this.requirements = null;
        
        this.init();
    }
    
    init() {
        if (this.passwordField) {
            this.createStrengthMeter();
            this.setupEventListeners();
            this.updateRequirements();
        }
    }
    
    createStrengthMeter() {
        // Create strength meter container
        const meterContainer = document.createElement('div');
        meterContainer.className = 'password-strength-meter mt-2';
        meterContainer.innerHTML = `
            <div class="progress" style="height: 8px;">
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            </div>
            <div class="strength-text mt-1 small"></div>
        `;
        
        // Insert after password field
        this.passwordField.parentNode.insertBefore(meterContainer, this.passwordField.nextSibling);
        
        this.strengthMeter = meterContainer.querySelector('.progress-bar');
        this.strengthText = meterContainer.querySelector('.strength-text');
        
        // Create requirements list
        this.createRequirementsList();
    }
    
    createRequirementsList() {
        const requirementsContainer = document.createElement('div');
        requirementsContainer.className = 'password-requirements mt-2 small text-muted';
        requirementsContainer.innerHTML = `
            <div class="requirements-title mb-2"><strong>Password Requirements:</strong></div>
            <ul class="requirements-list list-unstyled">
                <li class="requirement" data-requirement="length">
                    <i class="fas fa-circle text-muted"></i> At least 8 characters
                </li>
                <li class="requirement" data-requirement="uppercase">
                    <i class="fas fa-circle text-muted"></i> One uppercase letter (A-Z)
                </li>
                <li class="requirement" data-requirement="lowercase">
                    <i class="fas fa-circle text-muted"></i> One lowercase letter (a-z)
                </li>
                <li class="requirement" data-requirement="digit">
                    <i class="fas fa-circle text-muted"></i> One digit (0-9)
                </li>
                <li class="requirement" data-requirement="special">
                    <i class="fas fa-circle text-muted"></i> One special character (!@#$%^&*)
                </li>
                <li class="requirement" data-requirement="no-sequential">
                    <i class="fas fa-circle text-muted"></i> No sequential patterns
                </li>
                <li class="requirement" data-requirement="no-common">
                    <i class="fas fa-circle text-muted"></i> Not a common password
                </li>
            </ul>
        `;
        
        this.passwordField.parentNode.insertBefore(requirementsContainer, this.passwordField.nextSibling.nextSibling);
        this.requirements = requirementsContainer.querySelectorAll('.requirement');
    }
    
    setupEventListeners() {
        // Password field events
        this.passwordField.addEventListener('input', () => {
            this.updateStrength();
            this.updateRequirements();
        });
        
        this.passwordField.addEventListener('focus', () => {
            this.showRequirements();
        });
        
        this.passwordField.addEventListener('blur', () => {
            this.hideRequirements();
        });
        
        // Confirm password field events
        if (this.confirmField) {
            this.confirmField.addEventListener('input', () => {
                this.checkPasswordMatch();
            });
        }
        
        // Skip adding a password toggle for main password here to avoid overlap with UI
    }
    
    // Removed addPasswordToggle to prevent injecting a toggle on the main password field
    
    updateStrength() {
        const password = this.passwordField.value;
        const strength = this.calculateStrength(password);
        const label = this.getStrengthLabel(strength);
        const color = this.getStrengthColor(strength);
        
        // Update progress bar
        this.strengthMeter.style.width = strength + '%';
        this.strengthMeter.className = `progress-bar ${color}`;
        
        // Update text
        this.strengthText.textContent = `Password Strength: ${label}`;
        this.strengthText.className = `strength-text mt-1 small ${color}`;
    }
    
    calculateStrength(password) {
        let score = 0;
        
        // Length contribution (up to 25 points)
        if (password.length >= 8) score += 10;
        if (password.length >= 12) score += 10;
        if (password.length >= 16) score += 5;
        
        // Character variety contribution (up to 40 points)
        if (/[a-z]/.test(password)) score += 10;
        if (/[A-Z]/.test(password)) score += 10;
        if (/\d/.test(password)) score += 10;
        if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score += 10;
        
        // Complexity contribution (up to 35 points)
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 5;
        if (/[a-zA-Z]/.test(password) && /\d/.test(password)) score += 5;
        if (/[a-zA-Z]/.test(password) && /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score += 5;
        if (/\d/.test(password) && /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score += 5;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password) && /\d/.test(password) && /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score += 15;
        
        // Penalties for weak patterns
        if (/(.)\1{2,}/.test(password)) score -= 10;
        if (/(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)/i.test(password)) score -= 15;
        if (/(?:123|234|345|456|567|678|789|012)/.test(password)) score -= 15;
        
        return Math.max(0, Math.min(100, score));
    }
    
    getStrengthLabel(score) {
        if (score >= 80) return 'Very Strong';
        if (score >= 60) return 'Strong';
        if (score >= 40) return 'Moderate';
        if (score >= 20) return 'Weak';
        return 'Very Weak';
    }
    
    getStrengthColor(score) {
        if (score >= 80) return 'bg-success';
        if (score >= 60) return 'bg-info';
        if (score >= 40) return 'bg-warning';
        if (score >= 20) return 'bg-danger';
        return 'bg-danger';
    }
    
    updateRequirements() {
        const password = this.passwordField.value;
        
        // Check each requirement
        const checks = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            digit: /\d/.test(password),
            special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
            'no-sequential': !/(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)/i.test(password),
            'no-common': !['password', '123456', 'qwerty', 'admin', 'letmein'].includes(password.toLowerCase())
        };
        
        // Update requirement indicators
        this.requirements.forEach(req => {
            const requirement = req.dataset.requirement;
            const icon = req.querySelector('i');
            const isMet = checks[requirement];
            
            if (isMet) {
                icon.className = 'fas fa-check-circle text-success';
                req.classList.add('text-success');
            } else {
                icon.className = 'fas fa-circle text-muted';
                req.classList.remove('text-success');
            }
        });
    }
    
    checkPasswordMatch() {
        if (!this.confirmField) return;
        
        const password = this.passwordField.value;
        const confirm = this.confirmField.value;
        
        if (confirm && password !== confirm) {
            this.confirmField.classList.add('is-invalid');
            this.showPasswordMatchError();
        } else {
            this.confirmField.classList.remove('is-invalid');
            this.hidePasswordMatchError();
        }
    }
    
    showPasswordMatchError() {
        let errorDiv = this.confirmField.parentNode.querySelector('.password-match-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'password-match-error invalid-feedback';
            errorDiv.textContent = 'Passwords do not match.';
            this.confirmField.parentNode.appendChild(errorDiv);
        }
        errorDiv.style.display = 'block';
    }
    
    hidePasswordMatchError() {
        const errorDiv = this.confirmField.parentNode.querySelector('.password-match-error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }
    
    showRequirements() {
        if (this.requirements) {
            this.requirements.forEach(req => req.style.display = 'block');
        }
    }
    
    hideRequirements() {
        if (this.requirements && !this.passwordField.value) {
            this.requirements.forEach(req => req.style.display = 'none');
        }
    }
}

// Initialize password strength meter when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new PasswordStrengthMeter();
});

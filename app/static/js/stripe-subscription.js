// Stripe subscription handling
class StripeSubscriptionManager {
    constructor(publishableKey) {
        this.stripe = Stripe(publishableKey);
        this.elements = this.stripe.elements();
        this.cardElement = null;
        this.selectedPlan = null;
        this.plans = {};
        
        this.initializeElements();
        this.setupEventListeners();
    }
    
    initializeElements() {
        // Create card element
        this.cardElement = this.elements.create('card', {
            style: {
                base: {
                    fontSize: '16px',
                    color: '#424770',
                    '::placeholder': {
                        color: '#aab7c4',
                    },
                },
            },
        });
        
        // Handle card errors
        this.cardElement.on('change', ({error}) => {
            const displayError = document.getElementById('card-errors');
            if (error) {
                displayError.textContent = error.message;
            } else {
                displayError.textContent = '';
            }
        });
    }
    
    setupEventListeners() {
        // Plan selection buttons
        document.querySelectorAll('.select-plan-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectPlan(e));
        });
        
        // Payment form submission
        const form = document.getElementById('payment-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handlePayment(e));
        }
    }
    
    selectPlan(event) {
        this.selectedPlan = event.target.dataset.plan;
        
        // Update UI
        document.querySelectorAll('.subscription-plan').forEach(card => {
            card.classList.remove('border-warning');
        });
        document.querySelector(`[data-plan="${this.selectedPlan}"]`).classList.add('border-warning');
        
        // Show payment section
        document.getElementById('payment-section').style.display = 'block';
        
        // Update selected plan info
        const planInfo = this.plans[this.selectedPlan];
        if (planInfo) {
            document.getElementById('selected-plan-info').innerHTML = 
                `<strong>${planInfo.name}</strong><br>${planInfo.features.join(', ')}`;
        }
        
        // Mount card element
        this.cardElement.mount('#card-element');
        
        // Scroll to payment section
        document.getElementById('payment-section').scrollIntoView({behavior: 'smooth'});
    }
    
    async handlePayment(event) {
        event.preventDefault();

        if (!this.selectedPlan) {
            this.showError('Please select a plan first');
            return;
        }

        const {token, error} = await this.stripe.createToken(this.cardElement);

        if (error) {
            document.getElementById('card-errors').textContent = error.message;
        } else {
            this.showLoading(true);

            // Submit form data
            const formData = new FormData(document.getElementById('payment-form'));
            formData.append('plan_type', this.selectedPlan);

            try {
                const response = await fetch(window.location.href, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.client_secret) {
                    // Confirm payment
                    const {error} = await this.stripe.confirmCardPayment(result.client_secret, {
                        payment_method: {
                            card: this.cardElement,
                            billing_details: {
                                name: document.querySelector('[data-user-name]')?.dataset.userName || '',
                            },
                        }
                    });

                    if (error) {
                        this.showError(error.message);
                    } else {
                        // Payment succeeded
                        window.location.href = document.querySelector('[data-success-url]')?.dataset.successUrl || '/';
                    }
                } else {
                    this.showError('Payment setup failed. Please try again.');
                }
            } catch (err) {
                this.showError('Payment processing error. Please try again.');
            } finally {
                this.showLoading(false);
            }
        }
    }
    
    showLoading(loading) {
        const submitBtn = document.getElementById('submit-payment');
        const buttonText = document.getElementById('button-text');
        const spinner = document.getElementById('spinner');
        
        if (loading) {
            submitBtn.disabled = true;
            buttonText.textContent = 'Processing...';
            spinner.style.display = 'inline-block';
        } else {
            submitBtn.disabled = false;
            buttonText.textContent = 'Subscribe Now';
            spinner.style.display = 'none';
        }
    }
    
    showError(message) {
        document.getElementById('card-errors').textContent = message;
    }
    
    setPlansData(plansData) {
        this.plans = plansData;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const stripeKey = document.querySelector('[data-stripe-key]')?.dataset.stripeKey;
    const plansData = document.querySelector('[data-plans]')?.dataset.plans;
    
    if (stripeKey && plansData) {
        try {
            const manager = new StripeSubscriptionManager(stripeKey);
            manager.setPlansData(JSON.parse(plansData));
        } catch (error) {
            console.error('Failed to initialize Stripe:', error);
        }
    }
});

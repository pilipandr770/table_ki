from flask import render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import gettext as _, get_locale
from urllib.parse import urlparse, urljoin
import stripe
from datetime import datetime

from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, SubscriptionForm, ChangePasswordForm, ProfileForm
from app.models import User, Subscription, PlanType, SubscriptionStatus
from app import db

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_approved:
                flash(_('Your account is pending admin approval. Please wait for approval before accessing the system.'), 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            
            # Set language preference in session
            if user.language_preference:
                session['language'] = user.language_preference
            
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.index')
            
            flash(_('Welcome back, %(name)s!', name=user.first_name), 'success')
            return redirect(next_page)
        else:
            flash(_('Invalid email or password.'), 'error')
    
    return render_template('auth/login.html', title=_('Sign In'), form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out successfully.'), 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            language_preference=form.language_preference.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(_('Registration successful! Please select a subscription plan to continue.'), 'success')
        return redirect(url_for('auth.subscribe', user_id=user.id))
    
    return render_template('auth/register.html', title=_('Register'), form=form)

@bp.route('/subscribe/<int:user_id>', methods=['GET', 'POST'])
def subscribe(user_id):
    user = User.query.get_or_404(user_id)
    
    # Only allow the user themselves to subscribe (or admins)
    if current_user.is_authenticated and current_user.id != user_id and not current_user.is_admin():
        flash(_('Access denied.'), 'error')
        return redirect(url_for('main.index'))
    
    # Check if user already has a subscription
    if user.subscription:
        flash(_('You already have a subscription.'), 'info')
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        else:
            return redirect(url_for('auth.login'))
    
    form = SubscriptionForm()
    plans = current_app.config['SUBSCRIPTION_PLANS']
    
    if form.validate_on_submit():
        try:
            # Check if we're in bypass mode
            if current_app.config.get('BYPASS_STRIPE', False):
                # Create a mock subscription for development
                user_subscription = Subscription(
                    user_id=user.id,
                    plan_type=PlanType(form.plan_type.data),
                    stripe_subscription_id=f'dev_sub_{user.id}_{datetime.utcnow().timestamp()}',
                    stripe_customer_id=f'dev_cust_{user.id}',
                    status=SubscriptionStatus.ACTIVE,
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow().replace(year=datetime.utcnow().year + 1)
                )
                db.session.add(user_subscription)
                db.session.commit()
                
                flash(_('Development subscription activated successfully!'), 'success')
                if current_user.is_authenticated:
                    return redirect(url_for('main.dashboard'))
                else:
                    return redirect(url_for('auth.login'))
            
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.get_full_name(),
                metadata={'user_id': user.id}
            )
            
            # Create subscription
            plan_config = plans[form.plan_type.data]
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': plan_config['price_id']}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent'],
            )
            
            # Save subscription to database
            user_subscription = Subscription(
                user_id=user.id,
                plan_type=PlanType(form.plan_type.data),
                stripe_subscription_id=subscription.id,
                stripe_customer_id=customer.id,
                status=SubscriptionStatus.INACTIVE
            )
            db.session.add(user_subscription)
            db.session.commit()
            
            return jsonify({
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'subscription_id': subscription.id
            })
            
        except stripe.error.StripeError as e:
            flash(_('Payment processing error. Please try again.'), 'error')
            current_app.logger.error(f"Stripe error: {str(e)}")
        except Exception as e:
            flash(_('An error occurred. Please try again.'), 'error')
            current_app.logger.error(f"Subscription error: {str(e)}")
    
    return render_template('auth/subscribe.html', title=_('Choose Subscription'), 
                         form=form, plans=plans, user=user)

@bp.route('/subscription-success/<int:user_id>')
def subscription_success(user_id):
    user = User.query.get_or_404(user_id)
    flash(_('Subscription created successfully! Your account is now pending admin approval.'), 'success')
    
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    else:
        return redirect(url_for('auth.login'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not current_user.can_access_system() and not current_user.is_admin():
        flash(_('Access denied. Your account needs admin approval and an active subscription.'), 'error')
        return redirect(url_for('main.index'))
    
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data.strip()
        current_user.last_name = form.last_name.data.strip()
        current_user.language_preference = form.language_preference.data
        
        # Update session language
        session['language'] = form.language_preference.data
        
        db.session.commit()
        flash(_('Profile updated successfully.'), 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', title=_('Profile'), form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not current_user.can_access_system() and not current_user.is_admin():
        flash(_('Access denied. Your account needs admin approval and an active subscription.'), 'error')
        return redirect(url_for('main.index'))
    
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash(_('Password changed successfully.'), 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash(_('Current password is incorrect.'), 'error')
    
    return render_template('auth/change_password.html', title=_('Change Password'), form=form)

@bp.route('/set-language/<language>')
def set_language(language):
    if language in current_app.config['LANGUAGES']:
        session['language'] = language
        
        # Update user preference if logged in
        if current_user.is_authenticated:
            current_user.language_preference = language
            db.session.commit()
    
    return redirect(request.referrer or url_for('main.index'))

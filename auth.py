from authlib.integrations.flask_client import OAuth
from flask import current_app, url_for, session, redirect, request
from models.user import User, db
import os
from urllib.parse import quote_plus, urlencode
import secrets

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    
    # Check if Google OAuth credentials are configured
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    app.logger.info(f"Google OAuth credentials check - Client ID: {'Set' if client_id else 'Not set'}, Client Secret: {'Set' if client_secret else 'Not set'}")
    
    if not client_id or not client_secret:
        app.logger.warning("Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
        return
    
    try:
        oauth.register(
            name='google',
            client_id=client_id,
            client_secret=client_secret,
            access_token_url='https://oauth2.googleapis.com/token',
            access_token_params=None,
            authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
            authorize_params=None,
            api_base_url='https://www.googleapis.com/oauth2/v2/',
            client_kwargs={
                'scope': 'email profile'
            }
        )
        app.logger.info("Google OAuth client registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register Google OAuth client: {str(e)}")
        return

def google_login():
    """Initiate Google OAuth login"""
    try:
        if not oauth.google:
            current_app.logger.error("Google OAuth not configured. Please set up Google OAuth credentials.")
            return redirect(url_for('login_error'))
        
        # Clear any existing session data
        session.pop('oauth_state', None)
        session.pop('oauth_token', None)
        
        # Generate a secure state parameter
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # Use a fixed redirect URI
        if current_app.config.get('DEBUG', False):
            redirect_uri = 'http://localhost:5000/auth/google/callback'
        else:
            redirect_uri = 'https://www.qrprocreator.com/auth/google/callback'
            
        current_app.logger.info(f"Redirecting to Google OAuth with redirect_uri: {redirect_uri}")
        print(f"DEBUG: Redirect URI being used: {redirect_uri}")
        
        # Use authorize_redirect with explicit state parameter
        return oauth.google.authorize_redirect(
            redirect_uri=redirect_uri,
            state=state
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in google_login: {str(e)}")
        return redirect(url_for('login_error'))

def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Verify state parameter
        expected_state = session.get('oauth_state')
        received_state = request.args.get('state')
        
        if not expected_state or not received_state or expected_state != received_state:
            current_app.logger.error(f"State mismatch: expected={expected_state}, received={received_state}")
            session.pop('oauth_state', None)
            return redirect(url_for('login_error'))
        
        # Clear the state from session
        session.pop('oauth_state', None)
        
        # Get the token
        token = oauth.google.authorize_access_token()
        
        # Get user info from Google API
        resp = oauth.google.get('userinfo')
        userinfo = resp.json()
        
        # Extract user information
        google_id = userinfo['id']
        email = userinfo['email']
        first_name = userinfo.get('given_name', '')
        last_name = userinfo.get('family_name', '')
        profile_picture = userinfo.get('picture', '')
        
        # Check if user already exists
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                profile_picture=profile_picture,
                profile_slug=generate_profile_slug(first_name, last_name)
            )
            db.session.add(user)
            db.session.commit()
            
            # Log in the new user with permanent session
            from flask_login import login_user
            session.permanent = True
            login_user(user, remember=True)
            
            # Redirect to profile completion
            return redirect(url_for('complete_profile'))
        
        # User exists, log them in with permanent session
        from flask_login import login_user
        session.permanent = True
        login_user(user, remember=True)
        
        # Check if user is admin and redirect accordingly
        if user.is_admin:
            # Redirect admin users to the main dashboard
            return redirect(url_for('dashboard'))
        else:
            # Redirect regular users to user dashboard
            return redirect(url_for('user_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {str(e)}")
        # Clear any session data on error
        session.pop('oauth_state', None)
        session.pop('oauth_token', None)
        return redirect(url_for('login_error'))

def generate_profile_slug(first_name, last_name):
    """Generate a unique profile slug for the user"""
    base_slug = f"{first_name.lower()}-{last_name.lower()}"
    base_slug = ''.join(c for c in base_slug if c.isalnum() or c == '-')
    
    # Check if slug already exists
    counter = 1
    slug = base_slug
    while User.query.filter_by(profile_slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug 
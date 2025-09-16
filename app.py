from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import qrcode
from io import BytesIO
import base64
import os
from models.user import db, Admin, BusinessCard, Order, User  # Add User import
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from auth import init_oauth, google_login, google_callback

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration for persistent login
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Keep logged in for 30 days
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize OAuth
init_oauth(app)

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.remember_cookie_duration = timedelta(days=30)  # Remember for 30 days
db.init_app(app)

migrate = Migrate(app, db)


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


@login_manager.user_loader
def load_user(user_id):
    # Try to load as Admin first, then as User
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin
    
    user = User.query.get(int(user_id))
    if user:
        return user
    
    return None


@app.before_first_request
def create_tables():
    db.create_all()
    # Create default admin if none exists
    if not Admin.query.first():
        admin = Admin(username='admin', email='admin@example.com')
        admin.set_password('admin')  # Change this password!
        db.session.add(admin)
        db.session.commit()


# Google OAuth routes
@app.route('/auth/google')
def auth_google():
    return google_login()


@app.route('/auth/google/callback')
def auth_google_callback():
    return google_callback()


@app.route('/login_error')
def login_error():
    flash('An error occurred during login. Please try again.', 'error')
    return redirect(url_for('index'))


@app.route('/test_oauth')
def test_oauth():
    """Test route to check OAuth configuration"""
    import os
    from flask import url_for
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = url_for('auth_google_callback', _external=True)
    
    return jsonify({
        'client_id_set': bool(client_id),
        'client_secret_set': bool(client_secret),
        'client_id_length': len(client_id) if client_id else 0,
        'client_secret_length': len(client_secret) if client_secret else 0,
        'redirect_uri': redirect_uri,
        'host_url': request.host_url
    })


@app.route('/complete_profile', methods=['GET', 'POST'])
def complete_profile():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Update user profile with form data
            current_user.profession = request.form.get('profession')
            # Require phone number
            phone_submitted = (request.form.get('phone') or '').strip()
            if not phone_submitted:
                flash('Phone number is required.', 'error')
                return render_template('complete_profile.html')
            current_user.phone = phone_submitted
            current_user.biography = request.form.get('biography')
            current_user.linkedin = request.form.get('linkedin')
            current_user.whatsapp = request.form.get('whatsapp')
            current_user.instagram = request.form.get('instagram')
            
            db.session.commit()
            flash('Profile completed successfully!', 'success')
            
            # Redirect based on admin status
            if current_user.is_admin:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your profile.', 'error')
    
    return render_template('complete_profile.html')


@app.route('/user_dashboard')
@login_required
def user_dashboard():
    # Redirect only pure Admin model users to admin dashboard.
    # User accounts with is_admin=True can still access their user dashboard.
    if isinstance(current_user._get_current_object(), Admin):
        return redirect(url_for('dashboard'))
    
    # Generate QR code for the user
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{request.host_url}pro/{current_user.profile_slug}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR code to base64 for display
    buffered = BytesIO()
    qr_img.save(buffered)
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('user_dashboard.html', qr_code_base64=qr_base64)


@app.route('/pro/<profile_slug>')
def public_profile(profile_slug):
    user = User.query.filter_by(profile_slug=profile_slug).first_or_404()
    
    # Generate QR code for the profile
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{request.host_url}pro/{profile_slug}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR code to base64 for display
    buffered = BytesIO()
    qr_img.save(buffered)
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('public_profile.html', user=user, qr_code_base64=qr_base64)


@app.route('/download_qr/<profile_slug>')
def download_qr(profile_slug):
    user = User.query.filter_by(profile_slug=profile_slug).first_or_404()
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{request.host_url}pro/{profile_slug}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    img_io = BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)
    
    from flask import send_file
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f'qr-{profile_slug}.png')


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if isinstance(current_user._get_current_object(), Admin):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Basic information
            new_first_name = request.form.get('first_name', '').strip()
            new_last_name = request.form.get('last_name', '').strip()
            
            # Update first and last names if they changed
            name_changed = False
            if new_first_name and new_first_name != current_user.first_name:
                current_user.first_name = new_first_name
                name_changed = True
            if new_last_name and new_last_name != current_user.last_name:
                current_user.last_name = new_last_name
                name_changed = True
            
            # Update profile slug if name changed
            if name_changed:
                from auth import generate_profile_slug
                current_user.profile_slug = generate_profile_slug(current_user.first_name, current_user.last_name)
            
            current_user.profession = request.form.get('profession')
            current_user.biography = request.form.get('biography')
            
            # Phone numbers
            current_user.phone = request.form.get('phone')
            current_user.phone_secondary = request.form.get('phone_secondary')
            current_user.phone_third = request.form.get('phone_third')
            current_user.phone_fourth = request.form.get('phone_fourth')
            
            # Location information
            current_user.address = request.form.get('address')
            current_user.location = request.form.get('location')
            
            # Review link
            current_user.review_link = request.form.get('review_link')
            
            # Social media links
            current_user.linkedin = request.form.get('linkedin')
            current_user.whatsapp = request.form.get('whatsapp')
            current_user.instagram = request.form.get('instagram')
            current_user.twitter = request.form.get('twitter')
            current_user.snapchat = request.form.get('snapchat')
            current_user.facebook = request.form.get('facebook')
            current_user.youtube = request.form.get('youtube')
            current_user.tiktok = request.form.get('tiktok')
            
            # Handle photo upload
            photo = request.files.get('photo')
            if photo and photo.filename:
                # Create photos directory if it doesn't exist
                os.makedirs('static/photos', exist_ok=True)
                
                # Generate unique filename
                filename = f"user_{current_user.id}_{int(datetime.utcnow().timestamp())}_{photo.filename}"
                photo_path = f"photos/{filename}"
                
                # Save the photo
                photo.save(f"static/{photo_path}")
                
                # Update user's profile picture
                current_user.profile_picture = photo_path
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
            print(f"Error updating profile: {str(e)}")
    
    return render_template('edit_profile.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    cards = BusinessCard.query.order_by(BusinessCard.created_at.desc()).all()
    return render_template('dashboard.html', cards=cards)


@app.route('/create_card', methods=['GET', 'POST'])
def create_card():
    if request.method == 'POST':
        try:
            unique_id = base64.urlsafe_b64encode(os.urandom(6)).decode('utf-8')

            # Handle photo upload
            photo = request.files.get('photo')
            photo_path = None
            if photo:
                filename = f"{unique_id}_{photo.filename}"
                photo_path = f"photos/{filename}"
                photo.save(f"static/{photo_path}")

            # Create new user
            new_user = BusinessCard(
                name=request.form['name'],
                title=request.form['title'],
                phone_primary=request.form['phone_primary'],
                phone_secondary=request.form.get('phone_secondary'),
                phone_third=request.form.get('phone_third'),
                phone_fourth=request.form.get('phone_fourth'),
                email=request.form['email'],
                address=request.form['address'],
                location=request.form['location'],
                photo_path=photo_path,
                # Social media fields
                instagram=request.form.get('instagram'),
                whatsapp=request.form.get('whatsapp'),
                twitter=request.form.get('twitter'),
                snapchat=request.form.get('snapchat'),
                facebook=request.form.get('facebook'),
                linkedin=request.form.get('linkedin'),
                youtube=request.form.get('youtube'),
                tiktok=request.form.get('tiktok'),
                review_link=request.form.get('review_link'),  # New field
                unique_id=unique_id
            )

            db.session.add(new_user)
            db.session.commit()

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"{request.host_url}card/{unique_id}")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Convert QR code to base64 for display
            buffered = BytesIO()
            qr_img.save(buffered)
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()

            return jsonify({
                'success': True,
                'qr_code': qr_base64,
                'card_url': f"{request.host_url}card/{unique_id}"
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    return render_template('create_card.html')


@app.route('/edit_card/<unique_id>', methods=['GET', 'POST'])
@login_required
def edit_card(unique_id):
    # Get the existing card or return 404 if not found
    card = BusinessCard.query.filter_by(unique_id=unique_id).first_or_404()

    if request.method == 'POST':
        try:
            # Update basic information
            card.name = request.form.get('name')
            card.title = request.form.get('title')
            card.email = request.form.get('email')

            # Handle phone numbers
            card.phone_primary = request.form.get('phone_primary')
            card.phone_secondary = request.form.get('phone_secondary')
            card.phone_third = request.form.get('phone_third')
            card.phone_fourth = request.form.get('phone_fourth')
            card.address = request.form['address']

            # Handle location
            new_location = request.form.get('location')
            if new_location:
                card.location = new_location
            elif not card.location:
                card.location = "Location not specified"

            # Handle social media fields
            card.whatsapp = request.form.get('whatsapp')
            card.instagram = request.form.get('instagram')
            card.facebook = request.form.get('facebook')
            card.linkedin = request.form.get('linkedin')
            card.twitter = request.form.get('twitter')
            card.snapchat = request.form.get('snapchat')
            card.youtube = request.form.get('youtube')
            card.tiktok = request.form.get('tiktok')

            # Handle review link
            card.review_link = request.form.get('review_link')  # New field

            # Handle photo upload if provided
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename:
                    # Delete old photo if it exists
                    if card.photo_path:
                        old_photo_path = os.path.join('static', card.photo_path)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)

                    # Save new photo
                    filename = f"{card.unique_id}_{photo.filename}"
                    photo_path = f"photos/{filename}"
                    os.makedirs(os.path.join('static', 'photos'), exist_ok=True)
                    photo.save(os.path.join('static', photo_path))
                    card.photo_path = photo_path

            # Update the modified timestamp
            card.updated_at = datetime.utcnow()

            # Commit changes to database
            db.session.commit()
            flash('Business card updated successfully!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            # Log the error for debugging
            print(e)
            app.logger.error(f"Error updating card: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the card. Please try again.', 'error')
            return render_template('edit_card.html', card=card)

    # GET request - display the form
    return render_template('edit_card.html', card=card)



@app.route('/delete_card/<unique_id>', methods=['POST'])
@login_required
def delete_card(unique_id):
    card = BusinessCard.query.filter_by(unique_id=unique_id).first_or_404()

    # Delete associated photo if it exists
    if card.photo_path:
        try:
            os.remove(f"static/{card.photo_path}")
        except:
            pass

    db.session.delete(card)
    db.session.commit()
    flash('Card deleted successfully!')
    return redirect(url_for('dashboard'))


@app.route('/form', methods=['GET', 'POST'])
def order_form():
    if request.method == 'POST':
        try:
            # Parse products array from JSON string
            products = json.loads(request.form.get('products[]', '[]'))

            # Create new order object
            new_order = Order(
                # Personal Information
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                business_type=request.form.get('business_type'),

                # Product Information
                products=products,
                purpose=request.form.get('purpose'),
                purpose_details=request.form.get('other_purpose') if request.form.get('purpose') == 'other' else None,

                # Emergency Contacts
                emergency_contact_1=request.form.get('emergency_contact_1'),
                emergency_contact_2=request.form.get('emergency_contact_2'),

                # Social Media Links
                social_media_1=request.form.get('social_media_1'),
                social_media_2=request.form.get('social_media_2'),
                social_media_3=request.form.get('social_media_3'),
                social_media_4=request.form.get('social_media_4'),

                # Feedback Information
                source=request.form.get('source'),
                source_details=request.form.get('source_details') if request.form.get('source') == 'other' else None
            )

            # Add and commit to database
            db.session.add(new_order)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Votre formulaire a été envoyé avec succès!'
            })

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Order form submission error: {str(e)}')
            return jsonify({
                'success': False,
                'error': 'Une erreur est survenue lors de l\'envoi du formulaire.'
            }), 400

    return render_template('form.html')


@app.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect based on user type
        if isinstance(current_user._get_current_object(), Admin):
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('index.html')


# Your existing card view route (no authentication required)
@app.route('/card/<unique_id>')
def view_card(unique_id):
    card = BusinessCard.query.filter_by(unique_id=unique_id).first_or_404()
    return render_template('view_card.html', user=card)


@app.route('/admin/orders')
@login_required
def admin_orders():
    status = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')

    # Base query
    query = Order.query

    # Apply status filter
    if status != 'all':
        query = query.filter(Order.status == status)

    # Apply sorting
    if sort_by == 'created_at':
        query = query.order_by(Order.created_at.desc() if order == 'desc' else Order.created_at.asc())
    elif sort_by == 'name':
        query = query.order_by(Order.name.desc() if order == 'desc' else Order.name.asc())
    elif sort_by == 'status':
        query = query.order_by(Order.status.desc() if order == 'desc' else Order.status.asc())

    # Execute query
    orders = query.all()

    return render_template('orders.html',
                           orders=orders,
                           current_status=status,
                           current_sort=sort_by,
                           current_order=order)


@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'processing', 'completed', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash('Status mis à jour avec succès!', 'success')
    else:
        flash('Status invalide!', 'error')
    return redirect(url_for('admin_orders'))


@app.route('/admin/orders/<int:order_id>/details')
@login_required
def order_details(order_id):
    app.logger.info(f"Received request for order {order_id}")  # Debug log

    try:
        order = Order.query.get_or_404(order_id)

        # Debug prints
        print(f"Found order: {order}")
        print(f"Order attributes: {vars(order)}")

        response_data = {
            'id': order.id,
            'name': order.name,
            'email': order.email,
            'phone': order.phone,
            'business_type': order.business_type,
            'products': order.products,
            'purpose': order.purpose,
            'purpose_details': order.purpose_details,
            'emergency_contact_1': order.emergency_contact_1,
            'emergency_contact_2': order.emergency_contact_2,
            'social_media_1': order.social_media_1,
            'social_media_2': order.social_media_2,
            'social_media_3': order.social_media_3,
            'social_media_4': order.social_media_4,
            'source': order.source,
            'source_details': order.source_details,
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in order_details: {str(e)}")  # Debug print
        app.logger.error(f"Error in order_details: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500


# Admin management routes
@app.route('/admin/manage', methods=['GET', 'POST'])
def admin_manage():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'Alaamin123':
            # Get all users
            users = User.query.all()
            return render_template('admin_manage.html', users=users, authenticated=True)
        else:
            flash('Mot de passe incorrect!', 'error')
            return render_template('admin_manage.html', users=[], authenticated=False)
    
    return render_template('admin_manage.html', users=[], authenticated=False)


@app.route('/admin/toggle_admin/<int:user_id>', methods=['POST'])
def toggle_admin(user_id):
    password = request.form.get('password')
    if password != 'Alaamin123':
        flash('Mot de passe incorrect!', 'error')
        return redirect(url_for('admin_manage'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = "admin" if user.is_admin else "utilisateur"
    flash(f'{user.get_full_name()} est maintenant {status}!', 'success')
    return redirect(url_for('admin_manage'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

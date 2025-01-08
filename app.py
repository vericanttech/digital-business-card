from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import qrcode
from io import BytesIO
import base64
import os
from models.user import db, Admin, BusinessCard, Order  # Remove User from import
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

""""app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False"""

load_dotenv()
print("Database URL:", os.getenv('DATABASE_URL'))
print("Secret Key:", os.getenv('FLASK_SECRET_KEY'))
app = Flask(__name__)
app.config['SECRET_KEY'] = '23eea57342560ce4c7e0a2c9884c1714'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                     'business_cards.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/photos')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db.init_app(app)

migrate = Migrate(app, db)


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


@app.before_first_request
def create_tables():
    db.create_all()
    # Create default admin if none exists
    if not Admin.query.first():
        admin = Admin(username='admin', email='admin@example.com')
        admin.set_password('admin')  # Change this password!
        db.session.add(admin)
        db.session.commit()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Admin.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


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
                address=request.form['address'],  # Add this line here
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
            # If no location provided and no existing location, set a default
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
        return redirect(url_for('dashboard'))
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

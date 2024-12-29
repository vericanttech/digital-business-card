from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import qrcode
from io import BytesIO
import base64
import os
from models.user import db, Admin, BusinessCard  # Remove User from import

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db.init_app(app)


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
            # Generate a unique ID for the user
            unique_id = base64.urlsafe_b64encode(os.urandom(6)).decode('utf-8')

            # Handle photo upload
            photo = request.files.get('photo')
            photo_path = None
            if photo:
                filename = f"{unique_id}_{photo.filename}"
                photo_path = f"photos/{filename}"
                photo.save(f"static/{photo_path}")

            # Get location data
            location = request.form.get('location', '')
            if not location:
                lat = request.form.get('latitude')
                lng = request.form.get('longitude')
                if lat and lng:
                    location = f"{lat}, {lng}"

            # Create new user
            new_user = BusinessCard(
                name=request.form['name'],
                title=request.form['title'],
                phone=request.form['phone'],
                email=request.form['email'],
                location=location,
                photo_path=photo_path,
                instagram=request.form.get('instagram'),
                whatsapp=request.form.get('whatsapp'),
                twitter=request.form.get('twitter'),
                snapchat=request.form.get('snapchat'),
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

            # Return JSON response for AJAX handling
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
    card = BusinessCard.query.filter_by(unique_id=unique_id).first_or_404()

    if request.method == 'POST':
        try:
            # Update basic info
            card.name = request.form['name']
            card.title = request.form['title']
            card.phone = request.form['phone']
            card.email = request.form['email']
            card.location = request.form['location']
            card.instagram = request.form.get('instagram')
            card.whatsapp = request.form.get('whatsapp')
            card.twitter = request.form.get('twitter')
            card.snapchat = request.form.get('snapchat')

            # Handle photo update if provided
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = f"{card.unique_id}_{photo.filename}"
                photo_path = f"photos/{filename}"
                photo.save(f"static/{photo_path}")
                card.photo_path = photo_path

            db.session.commit()
            flash('Card updated successfully!')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f'Error updating card: {str(e)}')

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


if __name__ == '__main__':
    app.run(debug=True)
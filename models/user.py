# models/user.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class BusinessCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    # Multiple phone numbers
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20))
    phone_third = db.Column(db.String(20))
    phone_fourth = db.Column(db.String(20))
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200))
    location = db.Column(db.String(200), nullable=False)
    photo_path = db.Column(db.String(200))

    # Social Media Links
    instagram = db.Column(db.String(100))
    whatsapp = db.Column(db.String(100))
    twitter = db.Column(db.String(100))
    snapchat = db.Column(db.String(100))
    facebook = db.Column(db.String(100))
    linkedin = db.Column(db.String(100))
    youtube = db.Column(db.String(100))
    tiktok = db.Column(db.String(100))

    unique_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Personal Information
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    business_type = db.Column(db.String(20), nullable=False)  # 'business' or 'individual'

    # Product Information
    products = db.Column(db.JSON, nullable=False)  # Store as JSON array
    purpose = db.Column(db.String(100), nullable=False)
    purpose_details = db.Column(db.Text)  # For additional details

    # Emergency Contacts
    emergency_contact_1 = db.Column(db.String(20), nullable=False)
    emergency_contact_2 = db.Column(db.String(20))  # Optional

    # Social Media Links
    social_media_1 = db.Column(db.String(200))
    social_media_2 = db.Column(db.String(200))
    social_media_3 = db.Column(db.String(200))
    social_media_4 = db.Column(db.String(200))

    # Feedback Information
    source = db.Column(db.String(50), nullable=False)  # How they heard about us
    source_details = db.Column(db.Text)  # Additional details about source

    # Status and Timestamps
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Order {self.id} by {self.name}>'
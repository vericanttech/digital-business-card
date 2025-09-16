# Digital Business Card Creator

A Flask web application for creating and managing digital business cards with QR code sharing functionality. Features multilingual support (English/French) and comprehensive user management.

## Features

- **Multi-language Support**: English and French interface
- **User Authentication**: Secure login and registration system
- **Profile Management**: Complete user profile setup with personal and professional information
- **Digital Business Cards**: Create and customize digital business cards
- **QR Code Generation**: Generate QR codes for easy sharing
- **Social Media Integration**: Support for LinkedIn, WhatsApp, Instagram links
- **Admin Dashboard**: Comprehensive admin panel for user and card management
- **Mobile-Responsive Design**: Optimized for all device sizes
- **vCard Download**: Export contact information as vCard
- **Print-Friendly QR Codes**: High-quality QR codes for printing
- **Database Migration**: Alembic-based database migrations
- **User Orders**: Track and manage user orders

## Installation

1. Clone the repository
```bash
git clone https://github.com/vericanttech/digital-business-card.git
cd digital-business-card
```

2. Create a virtual environment and activate it
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Initialize the database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. Run the application
```bash
python app.py
```

6. Access the application
- Open your browser and go to `http://localhost:5000`
- Register a new account or use admin credentials

## Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
FLASK_SECRET_KEY=your-secret-key-here
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
DATABASE_URL=sqlite:///business_cards.db
```

**Required Environment Variables:**
- `FLASK_SECRET_KEY`: A secret key for Flask sessions (generate a random string)
- `GOOGLE_MAPS_API_KEY`: Your Google Maps API key for location features
- `DATABASE_URL`: Database connection string (defaults to SQLite)

## Project Structure

```
digital-business-card/
├── app.py                 # Main Flask application
├── auth.py               # Authentication routes
├── models/
│   └── user.py           # User model and database schema
├── migrations/           # Database migration files
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── static/
│   ├── css/              # Stylesheets (including Tailwind CSS)
│   ├── js/               # JavaScript files
│   ├── images/           # Static images and icons
│   └── photos/           # User uploaded photos
├── templates/
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── complete_profile.html  # Profile completion (French)
│   ├── Dashboard.html    # Main dashboard
│   ├── create_card.html  # Card creation
│   ├── edit_card.html    # Card editing
│   ├── edit_profile.html # Profile editing
│   ├── view_card.html    # Card viewing
│   ├── admin_manage.html # Admin management
│   ├── user_dashboard.html # User dashboard
│   ├── public_profile.html # Public profile view
│   └── qr_code.html      # QR code display
├── requirements.txt      # Python dependencies
└── .gitignore           # Git ignore rules
```

## Usage

### For Users
1. **Registration**: Create an account with your email and password
2. **Profile Setup**: Complete your profile with personal and professional information
3. **Create Business Card**: Design your digital business card with custom information
4. **Generate QR Code**: Create a QR code for easy sharing
5. **Share**: Share your QR code or direct link with contacts

### For Administrators
1. **Admin Login**: Access the admin dashboard
2. **User Management**: View and manage all registered users
3. **Card Management**: Monitor and manage all business cards
4. **Order Tracking**: Track user orders and activity

### Language Support
- **English**: Default interface language
- **French**: Complete French localization available
- Switch languages through the interface

## API Endpoints

- `GET /` - Landing page
- `GET /login` - Login page
- `POST /login` - User authentication
- `GET /register` - Registration page
- `POST /register` - User registration
- `GET /dashboard` - User dashboard
- `GET /admin` - Admin dashboard
- `GET /profile/complete` - Profile completion (French)
- `POST /profile/complete` - Submit profile data
- `GET /card/create` - Create business card
- `POST /card/create` - Save business card
- `GET /card/<id>` - View business card
- `GET /card/<id>/qr` - Generate QR code

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

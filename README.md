# Digital Business Card Creator

A Flask web application for creating and managing digital business cards with QR code sharing functionality.

## Features

- Create digital business cards with personal and professional information
- Generate QR codes for easy sharing
- Support for social media links
- Google Maps integration for location
- Admin dashboard for managing cards
- Mobile-responsive design
- vCard download option
- Print-friendly QR codes

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/digital-business-card.git
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

4. Create an admin user
```bash
python create_admin.py
```

5. Run the application
```bash
python app.py
```

## Environment Setup

Make sure to set up the following before running:

1. Google Maps API key
2. Flask secret key
3. Database configuration (if not using SQLite)

## Project Structure

```
digital-business-card/
├── app.py
├── models/
│   └── user.py
├── static/
│   ├── css/
│   ├── js/
│   └── photos/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── create_card.html
│   ├── edit_card.html
│   └── view_card.html
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
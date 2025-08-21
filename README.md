# InterSpark - Flask Migration

A Flask-based web application connecting students with meaningful internship and volunteer opportunities. This project has been migrated from React/TypeScript to Python Flask with Jinja2 templating.

## 🌟 Features

- **Student Portal**: Create profiles, browse opportunities, and connect with organizations
- **Organization Portal**: Post opportunities, find talented students, manage applications
- **Responsive Design**: Mobile-friendly interface using Tailwind CSS
- **User Authentication**: Secure login/signup for both students and organizations
- **Opportunity Management**: Full CRUD operations for internships and volunteer positions
- **Search & Filter**: Advanced filtering for opportunities and talent search
- **Profile Management**: Comprehensive user profiles with skills and interests

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd /Users/prathyet/Websites/InterSpark
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python run.py
   ```

4. **Open your browser** and navigate to `http://localhost:5000`

## 🔐 Demo Accounts

### Students
- **Email**: alex@example.com, **Password**: password123
- **Email**: taylor@example.com, **Password**: password123

### Organizations
- **Email**: contact@techstart.org, **Password**: orgpassword123
- **Email**: info@greenearthinitiative.org, **Password**: orgpassword123

## 📁 Project Structure

```
InterSpark/
├── app.py                 # Main Flask application
├── run.py                # Application runner with setup
├── requirements.txt      # Python dependencies
├── interspark.db        # SQLite database (auto-created)
├── templates/           # Jinja2 templates
│   ├── base.html       # Base template with navigation
│   ├── home.html       # Landing page
│   ├── login.html      # Login page
│   ├── signup.html     # Registration page
│   ├── dashboard.html  # User dashboard
│   ├── profile.html    # Profile management
│   ├── opportunities.html      # Opportunity listings
│   ├── opportunity_details.html # Detailed opportunity view
│   ├── talent_search.html      # Student search for orgs
│   └── create_opportunity.html # Create new opportunity
└── static/             # Static files (CSS, JS, images)
    └── style.css       # Custom CSS styles
```

## 🗄️ Database Schema

The application uses SQLite with the following main models:

### User Model
- Handles both students and organizations
- Fields: id, name, email, password_hash, phone, location, user_type
- Student-specific: school, grade, bio, interests, availability
- Organization-specific: description, website, logo

### Opportunity Model
- Stores internship and volunteer opportunities
- Fields: id, title, organization_id, location, type, category, date, hours, deadline
- Additional: description, responsibilities, requirements, benefits

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLAlchemy with SQLite
- **Frontend**: Jinja2 templates
- **Styling**: Tailwind CSS (CDN)
- **Icons**: Font Awesome
- **Authentication**: Flask sessions with Werkzeug password hashing

## 🔄 Migration Details

This project was successfully migrated from:
- **From**: React/TypeScript with Vite, React Router, TailwindCSS
- **To**: Python Flask with Jinja2, SQLAlchemy, TailwindCSS

### Key Migration Changes:

1. **Frontend**: React components → Jinja2 templates
2. **Routing**: React Router → Flask routes
3. **State Management**: React state → Flask sessions
4. **Data**: TypeScript interfaces → SQLAlchemy models
5. **Styling**: Maintained TailwindCSS for consistency

## 📄 API Endpoints

### Authentication
- `GET/POST /login` - User login
- `GET/POST /signup` - User registration
- `GET /logout` - User logout

### Main Pages
- `GET /` - Home page
- `GET /dashboard` - User dashboard
- `GET /profile` - User profile management
- `POST /profile` - Update profile

### Opportunities
- `GET /opportunities` - List all opportunities
- `GET /opportunity/<id>` - Opportunity details
- `GET/POST /create_opportunity` - Create new opportunity (organizations only)

### Talent Search
- `GET /talent` - Search for students (organizations)

## 🚀 Deployment

For production deployment:

1. **Set environment variables**:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY='your-production-secret-key'
   export DATABASE_URL='your-production-database-url'
   ```

2. **Use a production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn app:app
   ```

3. **Configure a reverse proxy** (nginx, Apache, etc.)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🎯 Future Enhancements

- Email notifications for applications
- File upload for profiles and opportunities
- Advanced search filters
- Real-time messaging between students and organizations
- Mobile app development
- Integration with external job boards

---

**Built with ❤️ using Python Flask**

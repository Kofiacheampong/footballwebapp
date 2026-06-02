# ⚽ Football Stats Web App

A comprehensive football statistics dashboard that displays real-time data from Europe's top 5 leagues (Premier League, La Liga, Serie A, Bundesliga, and Ligue 1). Built with Flask and powered by the API-Football API.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### 📊 League Standings
- Live standings for all top 5 European leagues
- Team statistics including wins, draws, losses, goals for/against
- Historical data by season

### 🎯 Player Statistics
- **Top Scorers**: Track leading goal scorers across all leagues
- **Top Assists**: Monitor assist leaders
- **Player Comparison**: Compare two players side-by-side with detailed stats
- Comprehensive player profiles with photos, physical stats, and performance metrics

### 🔄 Real-Time Data
- Integration with API-Football for up-to-date statistics
- Redis caching for improved performance
- Automatic cache invalidation

### 🎨 Modern UI
- Responsive design that works on all devices
- Clean and intuitive interface
- League logos and team badges
- Professional styling with custom CSS/SCSS

### 🔧 Technical Features
- PostgreSQL database for data persistence
- Redis caching layer
- Celery for background task processing
- Health check endpoints for monitoring
- Prometheus metrics support
- Docker containerization
- Kubernetes deployment manifests

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- API-Football API key ([Get one here](https://rapidapi.com/api-sports/api/api-football))

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/Kofiacheampong/footballwebapp.git
cd footballwebapp
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API key and database credentials
```

5. **Initialize database**
```bash
flask init-db
```

6. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` to view the app.

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

## 🌐 Deployment on Render

### Quick Deploy
1. Fork this repository
2. Sign up at [Render.com](https://render.com)
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and deploy all services

### Manual Configuration
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed step-by-step instructions.

## 📁 Project Structure

```
footballwebapp/
├── app.py                  # Main Flask application
├── stats_data.py          # API integration and data fetching
├── database.py            # Database models and configuration
├── config.py              # Configuration management
├── celery_app.py          # Celery worker configuration
├── gunicorn_config.py     # Production WSGI configuration
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment blueprint
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Local development orchestration
├── static/               # Static assets (CSS, JS, images)
├── templates/            # Jinja2 HTML templates
├── tests/                # Test suite
├── k8s/                  # Kubernetes manifests
├── monitoring/           # Prometheus & Grafana configs
└── scripts/              # Database initialization scripts
```

## 🔑 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `API_KEY` | API-Football API key | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Yes | `sqlite:///football_stats.db` |
| `REDIS_URL` | Redis connection URL | No | - |
| `FLASK_ENV` | Environment (development/production) | No | `development` |
| `SECRET_KEY` | Flask secret key for sessions | Yes (prod) | Auto-generated |

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## 📊 API Endpoints

### Public Endpoints
- `GET /` - Home page with league selection
- `GET /league/<league_name>` - League standings and stats
- `GET /top-scorer` - Top scorers across all leagues
- `GET /top-assists` - Top assist providers
- `GET /player_comparison` - Compare two players

### Health & Monitoring
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with system metrics
- `GET /metrics` - Prometheus metrics

## 🔒 Security Features

- HTTPS enforcement in production
- Security headers (CSP, HSTS, X-Frame-Options)
- Rate limiting on API endpoints
- SQL injection protection via SQLAlchemy ORM
- XSS protection through template escaping
- CSRF protection for forms

## 🐛 Known Issues & Limitations

- API-Football has rate limits (check your plan)
- Some historical data may be incomplete
- Player search requires exact name matching

## 🛠️ Technologies Used

- **Backend**: Flask, SQLAlchemy, Celery
- **Database**: PostgreSQL
- **Caching**: Redis
- **Frontend**: HTML5, CSS3/SCSS, JavaScript
- **API**: API-Football (RapidAPI)
- **Deployment**: Docker, Render, Kubernetes (optional)
- **Monitoring**: Prometheus, Grafana

## 📈 Performance Optimizations

- Redis caching with 5-minute TTL
- Database query optimization with indexes
- Lazy loading of images
- CDN for static assets (in production)
- Gzip compression
- Connection pooling

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Kofi Acheampong**
- GitHub: [@Kofiacheampong](https://github.com/Kofiacheampong)
- Portfolio: [Your Portfolio URL]

## 🙏 Acknowledgments

- [API-Football](https://www.api-football.com/) for providing the football data API
- Flask and Python community for excellent documentation
- All contributors who help improve this project

## 📞 Support

For support, email your-email@example.com or open an issue on GitHub.

---

⭐ Star this repository if you find it helpful!

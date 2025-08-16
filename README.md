# Wellness at Work - Eye Tracking Wellness Application

[![CI/CD](https://github.com/wellness-ai/wellness-at-work/actions/workflows/ci.yml/badge.svg)](https://github.com/wellness-ai/wellness-at-work/actions/workflows/ci.yml)
[![Security](https://github.com/wellness-ai/wellness-at-work/actions/workflows/security.yml/badge.svg)](https://github.com/wellness-ai/wellness-at-work/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive, production-grade eye-tracking application designed to promote workplace wellness through real-time blink monitoring and data analytics. Built with cross-platform desktop support, cloud synchronization, and GDPR compliance.

## 🌟 Features

### Desktop Application
- **Real-time Eye Tracking**: MediaPipe-powered blink detection with configurable sensitivity
- **Cross-Platform**: Native support for Windows and macOS
- **Modern UI**: PyQt6-based interface with system tray integration
- **Performance Monitoring**: Real-time CPU, memory, and energy impact tracking
- **Offline Support**: Local data storage with automatic cloud synchronization
- **Google OAuth2**: Secure authentication with automatic token refresh

### Cloud Backend
- **RESTful API**: Flask-based backend with JWT authentication
- **Cloud Storage**: Google Cloud Storage (GCS) default, AWS S3 legacy support
- **Data Synchronization**: Automatic sync with local fallback & conflict resolution
- **GDPR Compliance**: Complete user data rights implementation
- **Security**: Comprehensive security measures and audit logging

### Web Dashboard
- **Modern React UI**: Responsive design with Tailwind CSS
- **Real-time Analytics**: Interactive charts and data visualization
- **User Management**: Profile settings and privacy controls
- **Data Export**: CSV/JSON export functionality
- **Mobile Responsive**: Optimized for all device sizes

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Desktop App   │    │  Cloud Backend  │    │  Web Dashboard  │
│   (PyQt6)       │    │   (Flask)       │    │   (React)       │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Eye Tracker │ │    │ │ REST API    │ │    │ │ Data Viz    │ │
│ │ (MediaPipe) │ │    │ │ (JWT Auth)  │ │    │ │ (Charts)    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Auth (OAuth)│ │    │ │ SQlite/JSON | │    │ │ User Mgmt   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Local DB    │ │    │ │ GCS/S3      │ │    │ │ Analytics   │ │
│ │ (SQLite)    │ │    │ │ (Storage)   │ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Google OAuth2 Credentials**
- *(Optional)* **AWS Account** (legacy S3 support)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/wellness-ai/wellness-at-work.git
   cd wellness-at-work
   ```

2. **Install Desktop Application**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   # Ensure matplotlib is installed for desktop analytics and packaging
   pip install matplotlib==3.9.2
   
   # Set up Google OAuth credentials
   cp configs/credentials.json.example configs/credentials.json
   # Edit configs/credentials.json with your Google OAuth2 credentials
   # For GCS set in .env: CLOUD_PROVIDER=gcs, GCS_BUCKET=your-bucket, GCS_CREDENTIALS_FILE=configs/credentials.json
   ```

3. **Install Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Install Web Dashboard**
   ```bash
   cd web_dashboard
   npm install
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your API configuration
   ```

### Configuration

1. **Google OAuth2 Setup**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Google+ API
   - Create OAuth2 credentials
   - Download and place in `configs/credentials.json`

2. **Cloud Storage Configuration**
   - Create GCS bucket for data storage (recommended)
   - Place service account JSON in `configs/credentials.json`
   - Set env: `CLOUD_PROVIDER=gcs`, `GCS_BUCKET=<bucket>`, `GCS_CREDENTIALS_FILE=configs/credentials.json`
   - *(Optional legacy)* Create S3 bucket & set `CLOUD_PROVIDER=aws` plus AWS_* vars

3. **Database Setup**
   ```bash
   cd backend
   flask db upgrade
   flask db seed  # Optional: seed with sample data
   ```

### Running the Application

1. **Start Backend**
   ```bash
   cd backend
   flask run
   ```

2. **Start Web Dashboard**
   ```bash
   cd web_dashboard
   npm start
   ```

3. **Start Desktop Application**
   ```bash
   python src/desktop_app/main.py
   # To run in headless mode (for CI/dev only):
   python src/desktop_app/main.py --headless
   ```

## 📊 Usage

### Desktop Application

1. **First Launch**
   - Click "Sign in with Google"
   - Grant necessary permissions
   - Configure tracking settings

2. **Daily Use**
   - Application runs in system tray
   - Real-time blink tracking
   - Automatic data synchronization
   - Performance monitoring

3. **Settings**
   - Adjust blink sensitivity
   - Configure sync intervals

## 📦 Packaging & Distribution (Desktop)

Bundle the PyQt6 desktop application using PyInstaller. The spec file is hardened to exclude secrets and unnecessary test modules. Ensure you have not added credentials.json to the bundle.

### Windows
```powershell
pyinstaller --noconfirm --clean wellness_app.spec
```

### macOS
```bash
pyinstaller --noconfirm --clean wellness_app.spec
```

### Linux
```bash
pyinstaller --noconfirm --clean wellness_app.spec
```

Artifacts will appear under `dist/WellnessAI.exe` and `dist/WellnessAI_dist/`. Create the runtime `data/` directory beside the executable on first run; it is not bundled.

#### Troubleshooting Desktop Packaging
- If the packaged app fails to start or exits immediately:
   - Ensure `matplotlib` is installed in your Python environment before building.
   - Remove any old `dist/` and `build/` folders before rebuilding.
   - Check `logs/wellness_ai.log` for sentinel and error messages.
   - If you see a missing module error (e.g., `No module named 'matplotlib'`), run `pip install matplotlib==3.9.2` and rebuild.
- Headless mode is only available for development/CI and is disabled in packaged builds unless explicitly enabled with `--headless`.
- Only one executable (`WellnessAI.exe`) is produced; any previous workaround EXEs are removed.

### Minimal CI Matrix Snippet (GitHub Actions)
Add to a workflow (e.g. `.github/workflows/package.yml`) after secrets and cache setup:
```yaml
name: desktop-package
on: [workflow_dispatch]
jobs:
   build:
      strategy:
         matrix:
            os: [ubuntu-latest, windows-latest, macos-latest]
      runs-on: ${{ matrix.os }}
      steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
            with:
               python-version: '3.11'
         - name: Install deps
            run: |
               pip install --upgrade pip
               pip install -r requirements.txt
               pip install matplotlib==3.9.2
         - name: Package desktop app
            run: pyinstaller --noconfirm --clean wellness_app.spec
         - name: Archive artifact
            uses: actions/upload-artifact@v4
            with:
               name: WellnessAI-${{ matrix.os }}
               path: dist/WellnessAI_dist/**
```

> NOTE: Do not commit or embed `configs/credentials.json` in the bundle. Provide credentials at runtime via environment variables or secure secret mount.

### Web Dashboard

1. **Login**
   - Use Google OAuth2 authentication
   - Access from any device

2. **Dashboard**
   - View real-time metrics
   - Historical data analysis
   - Performance trends

3. **Analytics**
   - Detailed blink patterns
   - Session analysis
   - Export capabilities

## 🔧 Development

### Project Structure

```
wellness-at-work/
├── src/
│   ├── desktop_app/          # PyQt6 desktop application
│   │   ├── auth.py           # Google OAuth2 authentication
│   │   ├── ui.py             # User interface components
│   │   ├── sync.py           # Data synchronization
│   │   ├── metrics.py        # Performance monitoring
│   │   └── core/
│   │       └── eye_tracker.py # MediaPipe eye tracking
│   ├── patch_manager/        # Application update system
│   └── reviewer/             # Code quality tools
├── backend/                  # Flask REST API
│   ├── app.py               # Main application
│   ├── models.py            # Database models
│   └── storage.py           # GCS / AWS S3 dual-provider integration
├── web_dashboard/           # React web application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts
│   │   └── hooks/           # Custom hooks
│   └── public/              # Static assets
├── configs/                 # Configuration files
├── data/                    # Local data storage
├── docs/                    # Documentation
├── tests/                   # Test suites
└── .github/                 # CI/CD workflows
```

### Development Setup

1. **Install Development Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   npm install --prefix web_dashboard
   ```

2. **Run Tests**
   ```bash
   # Python tests (includes GCS/S3 fallback & API tests)
   python -m pytest tests/
   
   # JavaScript tests
   npm test --prefix web_dashboard
   
   # Integration tests
   python tests/integration_tests.py
   ```

3. **Code Quality**
   ```bash
   # Python linting
   flake8 src/ backend/ tests/
   black src/ backend/ tests/
   
   # JavaScript linting
   npm run lint --prefix web_dashboard
   npm run format --prefix web_dashboard
   ```

4. **Security Scanning**
   ```bash
   # Run security review
   python src/reviewer/plugin.py src/ --type security
   
   # Dependency scanning
   safety check
   npm audit --prefix web_dashboard
   ```

## 🚀 Deployment

### Production Deployment

1. **AWS Infrastructure**
   ```bash
   # Deploy using Terraform
   cd infrastructure
   terraform init
   terraform plan
   terraform apply
   ```

2. **Docker Deployment**
   ```bash
   # Build and deploy containers
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Desktop Distribution**
   ```bash
   # Windows
   pyinstaller --onefile --windowed src/desktop_app/main.py
   
   # macOS
   pyinstaller --onefile --windowed src/desktop_app/main.py
   ```

### CI/CD Pipeline

The project includes comprehensive CI/CD pipelines:

- **Automated Testing**: Unit, integration, and security tests
- **Code Quality**: Linting, formatting, and security scanning
- **Build Automation**: Cross-platform builds and packaging
- **Deployment**: Automated deployment to staging and production

## 🔒 Security & Privacy

### Security Features

- **OAuth2 Authentication**: Secure Google authentication
- **JWT Tokens**: Stateless API authentication
- **Data Encryption**: AES-256 encryption at rest and in transit
- **Input Validation**: Comprehensive input sanitization
- **Rate Limiting**: Protection against abuse
- **Audit Logging**: Complete activity tracking

### GDPR Compliance

- **Data Minimization**: Only necessary data collected
- **User Consent**: Explicit consent management
- **Right to Access**: Complete data export functionality
- **Right to Deletion**: Complete data removal capability
- **Data Portability**: Standard format data export
- **Privacy by Design**: Built-in privacy controls

### Privacy Controls

- **Local Processing**: Eye tracking data processed locally
- **Anonymization**: Optional data anonymization
- **Consent Management**: Granular consent controls
- **Data Retention**: Configurable retention policies

### Storage & Fallback Hardening

- **Primary Cloud**: Google Cloud Storage (GCS) used when `CLOUD_PROVIDER=gcs` and bucket credentials available.
- **Automatic Fallback**: On any cloud upload failure events are committed to SQLite and appended to `data/local.json` ensuring no data loss.
- **Credential Isolation**: Service account JSON loaded only from path specified via `GOOGLE_APPLICATION_CREDENTIALS` / `GCS_CREDENTIALS_FILE`; file not embedded in source.
- **Least Privilege**: Service account should have `storage.objectAdmin` limited to the configured bucket only; no project-wide admin roles.
- **Integrity**: Each blink event stored as immutable JSON object (`events/<user>/<uuid>.json`) enabling audit and replay.
- **Graceful Degradation**: Analytics endpoints continue operating from DB/local cache if cloud unavailable.
- **GDPR Alignment**: Fallback files participate in the same deletion routines ensuring user erasure requests purge both cloud and local copies.

## 📈 Monitoring & Analytics

### Application Monitoring

- **Performance Metrics**: CPU, memory, and energy usage
- **Error Tracking**: Comprehensive error logging
- **User Analytics**: Usage patterns and trends
- **Health Checks**: Application health monitoring

### Data Analytics

- **Blink Patterns**: Individual and aggregate analysis
- **Session Analytics**: Work session insights
- **Trend Analysis**: Long-term pattern recognition
- **Wellness Insights**: Health and productivity correlations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

### Code Standards

- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ESLint, Prettier, JSDoc
- **Testing**: 90%+ code coverage
- **Documentation**: Comprehensive docstrings and READMEs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Security Documentation](docs/SECURITY.md)
- [API Documentation](docs/api/README.md)
- [User Guide](docs/user/README.md)

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/wellness-ai/wellness-at-work/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wellness-ai/wellness-at-work/discussions)
- **Email**: support@wellness.ai

### Community

- **Discord**: [Wellness.ai Community](https://discord.gg/wellness-ai)
- **Twitter**: [@WellnessAI](https://twitter.com/WellnessAI)
- **Blog**: [Wellness.ai Blog](https://wellness.ai/blog)

## 🙏 Acknowledgments

- **MediaPipe**: Eye tracking technology
- **PyQt6**: Desktop application framework
- **React**: Web application framework
- **Flask**: Backend API framework
- **AWS**: Cloud infrastructure
- **Open Source Community**: All contributors and maintainers

## 📊 Project Status

- **Version**: 1.1.0
- **Status**: Production Ready
- **Last Updated**: August 2025
- **Next Release**: Q4 2025

---

**Made with ❤️ by the Wellness.ai Team**

*Promoting workplace wellness through intelligent eye tracking technology.* 

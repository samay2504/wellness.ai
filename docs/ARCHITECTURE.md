# Wellness at Work - System Architecture

## Overview

Wellness at Work is a comprehensive eye-tracking application designed to promote workplace wellness through real-time blink monitoring and data analytics. The system consists of three main components:

1. **Desktop Application** - Cross-platform PyQt6 application for real-time eye tracking
2. **Cloud Backend** - Flask-based REST API with AWS infrastructure
3. **Web Dashboard** - React-based web interface for data visualization

## System Architecture

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
│ │ Auth (OAuth)│ │    │ │ PostgreSQL  │ │    │ │ User Mgmt   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Local DB    │ │    │ │ AWS S3      │ │    │ │ Analytics   │ │
│ │ (SQLite)    │ │    │ │ (Storage)   │ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AWS Cloud     │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │ RDS/Postgres│ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │ S3 Bucket   │ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │ CloudFront  │ │
                    │ └─────────────┘ │
                    └─────────────────┘
```

## Component Details

### 1. Desktop Application

#### Core Components

**Eye Tracker (`src/desktop_app/core/eye_tracker.py`)**
- **Technology**: MediaPipe Face Mesh, OpenCV
- **Functionality**: Real-time face detection and blink counting
- **Performance**: Optimized for 30 FPS with configurable thresholds
- **Threading**: Runs in separate thread to prevent UI blocking

**Authentication (`src/desktop_app/auth.py`)**
- **Technology**: Google OAuth2, keyring for secure storage
- **Features**: 
  - Secure token storage using system keychain
  - Automatic token refresh
  - User consent management
  - GDPR compliance

**User Interface (`src/desktop_app/ui.py`)**
- **Technology**: PyQt6 with modern styling
- **Components**:
  - Login screen with Google OAuth
  - Dashboard with real-time metrics
  - System tray integration
  - Performance monitoring widgets

**Data Synchronization (`src/desktop_app/sync.py`)**
- **Local Storage**: SQLite database with JSON backup
- **Cloud Sync**: AWS S3 integration with offline buffering
- **Features**:
  - Automatic background synchronization
  - Conflict resolution
  - Data compression
  - Retry mechanisms

**Performance Monitoring (`src/desktop_app/metrics.py`)**
- **Technology**: psutil for system metrics
- **Metrics**: CPU usage, memory consumption, energy impact
- **Real-time**: Continuous monitoring with configurable intervals

#### Data Models

```python
@dataclass
class User:
    id: str
    name: str
    email: str
    consent: bool = False

@dataclass
class BlinkEvent:
    id: str
    user_id: str
    timestamp: float
    count: int
    session_id: str
    device_id: str

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    energy_impact: str
    timestamp: float
```

### 2. Cloud Backend

#### API Architecture

**Framework**: Flask with SQLAlchemy ORM
**Authentication**: JWT-based with OAuth2 integration
**Database**: PostgreSQL on AWS RDS
**Storage**: AWS S3 for blob data

#### Key Endpoints

```
POST   /api/auth/register     - User registration
POST   /api/auth/login        - User authentication
POST   /api/auth/refresh      - Token refresh
GET    /api/user/profile      - User profile
PUT    /api/user/profile      - Update profile

POST   /api/events/blink      - Create blink event
GET    /api/events/blink      - Retrieve blink events
GET    /api/events/summary    - Event summaries

POST   /api/sync/upload       - Upload events
GET    /api/sync/status       - Sync status
POST   /api/sync/force        - Force sync

GET    /api/gdpr/export       - Data export
DELETE /api/gdpr/delete       - Data deletion
```

#### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    consent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blink events table
CREATE TABLE blink_events (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    timestamp DOUBLE PRECISION NOT NULL,
    count INTEGER NOT NULL,
    session_id VARCHAR(50) NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    synced BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync history table
CREATE TABLE sync_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    timestamp DOUBLE PRECISION NOT NULL,
    events_synced INTEGER NOT NULL,
    events_failed INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Web Dashboard

#### Technology Stack

- **Frontend**: React 18 with TypeScript
- **State Management**: React Query for server state
- **Styling**: Tailwind CSS with Headless UI
- **Charts**: Chart.js with react-chartjs-2
- **HTTP Client**: Axios with interceptors
- **Forms**: React Hook Form with validation

#### Key Features

- **Real-time Data Visualization**: Live charts and metrics
- **User Management**: Profile settings and preferences
- **Data Analytics**: Historical trends and insights
- **Export Functionality**: CSV/JSON data export
- **Responsive Design**: Mobile-friendly interface

## Data Flow

### 1. Eye Tracking Flow

```
Camera Input → MediaPipe Face Mesh → Blink Detection → Event Creation → Local Storage → Cloud Sync
```

1. **Capture**: OpenCV captures video frames
2. **Detection**: MediaPipe processes frames for facial landmarks
3. **Analysis**: EAR (Eye Aspect Ratio) calculation and blink detection
4. **Storage**: Events stored locally in SQLite
5. **Sync**: Background process uploads to cloud

### 2. Authentication Flow

```
User Login → Google OAuth2 → Token Storage → JWT Generation → API Access
```

1. **OAuth**: User authenticates with Google
2. **Token Storage**: Credentials stored securely using keyring
3. **JWT**: Backend generates JWT for API access
4. **Refresh**: Automatic token refresh before expiration

### 3. Synchronization Flow

```
Local Events → Batch Collection → S3 Upload → Database Update → Status Report
```

1. **Collection**: Unsynced events gathered from local database
2. **Batching**: Events grouped for efficient upload
3. **Upload**: Data sent to AWS S3 with metadata
4. **Update**: Database records marked as synced
5. **Reporting**: Sync status and metrics recorded

## Security Architecture

### Authentication & Authorization

- **OAuth2**: Google authentication for user identity
- **JWT**: Stateless authentication for API access
- **Keyring**: Secure credential storage using system keychain
- **HTTPS**: All communications encrypted in transit

### Data Protection

- **Encryption**: Data encrypted at rest and in transit
- **Access Control**: Role-based permissions
- **Audit Logging**: Comprehensive activity tracking
- **GDPR Compliance**: User data rights and deletion

### Privacy Features

- **Local Processing**: Eye tracking data processed locally
- **Consent Management**: Explicit user consent for data collection
- **Data Minimization**: Only necessary data collected
- **Right to Deletion**: Complete data removal capability

## Performance Considerations

### Desktop Application

- **Threading**: Eye tracking runs in separate thread
- **Memory Management**: Efficient data structures and cleanup
- **CPU Optimization**: Configurable FPS limits and processing
- **Battery Impact**: Energy-aware processing modes

### Cloud Infrastructure

- **Caching**: Redis for session and data caching
- **CDN**: CloudFront for static asset delivery
- **Load Balancing**: Application Load Balancer for high availability
- **Auto-scaling**: ECS/Fargate for dynamic scaling

### Database Optimization

- **Indexing**: Strategic indexes on frequently queried columns
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Optimized SQL queries with proper joins
- **Partitioning**: Large tables partitioned by date

## Deployment Architecture

### Development Environment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local Dev     │    │   Docker Compose│    │   Local Testing │
│   Desktop App   │    │   Backend API   │    │   Web Dashboard │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Production Environment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Actions│    │   AWS ECS       │    │   AWS S3 + CF   │
│   CI/CD Pipeline│    │   Backend API   │    │   Web Dashboard │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AWS RDS       │
                    │   PostgreSQL    │
                    └─────────────────┘
```

## Monitoring & Observability

### Application Monitoring

- **Logging**: Structured logging with correlation IDs
- **Metrics**: Application and business metrics collection
- **Tracing**: Distributed tracing for request flows
- **Alerting**: Proactive alerting for issues

### Infrastructure Monitoring

- **CloudWatch**: AWS service monitoring
- **Health Checks**: Application health endpoints
- **Performance**: Response time and throughput metrics
- **Availability**: Uptime and error rate tracking

## Scalability Considerations

### Horizontal Scaling

- **Stateless Design**: Application instances can be scaled horizontally
- **Database Sharding**: User data can be sharded by user ID
- **CDN Distribution**: Global content delivery
- **Load Balancing**: Traffic distribution across instances

### Vertical Scaling

- **Resource Optimization**: Efficient memory and CPU usage
- **Database Optimization**: Query optimization and indexing
- **Caching Strategy**: Multi-level caching (application, database, CDN)
- **Connection Pooling**: Efficient resource utilization

## Future Enhancements

### Planned Features

1. **Microservices Architecture**: Break down monolithic backend
2. **Real-time Notifications**: WebSocket-based live updates
3. **Advanced Analytics**: Machine learning insights
4. **Mobile Application**: Native mobile apps
5. **Integration APIs**: Third-party wellness platform integration

### Technical Improvements

1. **C++ Optimization**: Convert critical eye tracking to C++
2. **Edge Computing**: Local AI processing capabilities
3. **Blockchain**: Decentralized data storage option
4. **IoT Integration**: Smart device connectivity
5. **AR/VR Support**: Extended reality platforms

## Conclusion

The Wellness at Work architecture provides a robust, scalable, and secure foundation for eye-tracking wellness applications. The modular design allows for easy maintenance, testing, and future enhancements while ensuring compliance with privacy regulations and providing excellent user experience across all platforms. 
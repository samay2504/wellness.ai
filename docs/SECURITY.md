# Security Documentation - Wellness at Work

## Overview

This document outlines the security architecture, policies, and implementation details for the Wellness at Work application. The system is designed with security-first principles to protect user data and ensure compliance with privacy regulations.

## Security Architecture

### Defense in Depth

The application implements a multi-layered security approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Input Val.  │  │ Auth & Auth │  │ Session Management  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Transport Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    HTTPS    │  │   TLS 1.3   │  │ Certificate Pinning │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Network Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Firewall  │  │   WAF       │  │ DDoS Protection     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   IAM       │  │ Encryption  │  │ Security Groups     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Authentication & Authorization

### OAuth2 Implementation

**Google OAuth2 Flow:**
1. **Authorization Request**: User initiates login via Google
2. **Consent Screen**: User grants permissions to the application
3. **Authorization Code**: Google returns authorization code
4. **Token Exchange**: Application exchanges code for access/refresh tokens
5. **Token Storage**: Tokens stored securely using system keyring
6. **JWT Generation**: Backend generates JWT for API access

**Security Features:**
- **PKCE (Proof Key for Code Exchange)**: Prevents authorization code interception
- **State Parameter**: Prevents CSRF attacks
- **Nonce Validation**: Ensures token freshness
- **Scope Limitation**: Minimal required permissions

### JWT Implementation

**Token Structure:**
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "email": "user@example.com",
    "iat": 1640995200,
    "exp": 1640998800,
    "jti": "unique_token_id"
  },
  "signature": "HMACSHA256(base64UrlEncode(header) + '.' + base64UrlEncode(payload), secret)"
}
```

**Security Measures:**
- **Short Expiration**: 1-hour access tokens
- **Refresh Tokens**: Long-lived refresh tokens with rotation
- **Token Blacklisting**: Invalidated tokens tracked in database
- **Signature Verification**: HMAC-SHA256 with strong secret

### Authorization Model

**Role-Based Access Control (RBAC):**
```python
class UserRole(Enum):
    USER = "user"           # Basic user permissions
    ADMIN = "admin"         # Administrative access
    ANALYST = "analyst"     # Data analysis permissions

class Permission(Enum):
    READ_OWN_DATA = "read_own_data"
    WRITE_OWN_DATA = "write_own_data"
    READ_ALL_DATA = "read_all_data"
    MANAGE_USERS = "manage_users"
    EXPORT_DATA = "export_data"
```

## Data Protection

### Encryption

**Data at Rest:**
- **Database**: AES-256 encryption for PostgreSQL RDS
- **File Storage**: S3 server-side encryption (SSE-S3)
- **Local Storage**: SQLite database encryption using SQLCipher
- **Backup Files**: Encrypted JSON backups with AES-256

**Data in Transit:**
- **HTTPS/TLS 1.3**: All API communications
- **Certificate Pinning**: Prevents MITM attacks
- **HSTS Headers**: Enforces HTTPS-only connections
- **Secure Cookies**: HttpOnly, Secure, SameSite flags

**Key Management:**
- **AWS KMS**: Encryption key management
- **Key Rotation**: Automatic key rotation every 90 days
- **Access Logging**: All key usage logged and monitored

### Data Classification

**Public Data:**
- Application metadata
- Public documentation
- Anonymous usage statistics

**Internal Data:**
- System logs
- Performance metrics
- Configuration files

**Confidential Data:**
- User authentication tokens
- Personal health data
- Session information

**Restricted Data:**
- Encryption keys
- Admin credentials
- Security audit logs

### Data Handling

**Data Minimization:**
- Only collect necessary data for functionality
- Anonymize data where possible
- Implement data retention policies
- Regular data cleanup procedures

**Data Validation:**
```python
class BlinkEventValidator:
    def validate_event(self, event: BlinkEvent) -> bool:
        # Validate timestamp (within reasonable range)
        if not (0 < event.timestamp < time.time() + 3600):
            return False
        
        # Validate blink count (reasonable range)
        if not (0 <= event.count <= 1000):
            return False
        
        # Validate user ID format
        if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', event.user_id):
            return False
        
        return True
```

## Privacy & GDPR Compliance

### User Rights Implementation

**Right to Access:**
```python
@app.route('/api/gdpr/export', methods=['GET'])
@jwt_required
def export_user_data():
    user_id = get_jwt_identity()
    
    # Collect all user data
    user_data = {
        'profile': get_user_profile(user_id),
        'blink_events': get_user_events(user_id),
        'sync_history': get_sync_history(user_id),
        'consent_history': get_consent_history(user_id)
    }
    
    # Generate export file
    export_file = generate_export_file(user_data)
    
    return send_file(export_file, as_attachment=True)
```

**Right to Deletion:**
```python
@app.route('/api/gdpr/delete', methods=['DELETE'])
@jwt_required
def delete_user_data():
    user_id = get_jwt_identity()
    
    # Anonymize user data
    anonymize_user_data(user_id)
    
    # Delete from cloud storage
    delete_cloud_data(user_id)
    
    # Log deletion for audit
    log_data_deletion(user_id)
    
    return jsonify({'message': 'Data deleted successfully'})
```

**Right to Rectification:**
```python
@app.route('/api/user/profile', methods=['PUT'])
@jwt_required
def update_user_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate input data
    if not validate_profile_data(data):
        return jsonify({'error': 'Invalid data'}), 400
    
    # Update user profile
    update_profile(user_id, data)
    
    # Log changes for audit
    log_profile_update(user_id, data)
    
    return jsonify({'message': 'Profile updated successfully'})
```

### Consent Management

**Consent Tracking:**
```python
class ConsentManager:
    def record_consent(self, user_id: str, consent_type: str, granted: bool):
        consent_record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            timestamp=datetime.utcnow(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(consent_record)
        db.session.commit()
    
    def get_consent_status(self, user_id: str, consent_type: str) -> bool:
        latest_consent = ConsentRecord.query.filter_by(
            user_id=user_id,
            consent_type=consent_type
        ).order_by(ConsentRecord.timestamp.desc()).first()
        
        return latest_consent.granted if latest_consent else False
```

## Security Monitoring

### Logging & Auditing

**Security Event Logging:**
```python
class SecurityLogger:
    def log_auth_event(self, event_type: str, user_id: str, success: bool, details: dict):
        log_entry = SecurityLog(
            event_type=event_type,
            user_id=user_id,
            success=success,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details=json.dumps(details),
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    
    def log_data_access(self, user_id: str, data_type: str, action: str):
        self.log_auth_event(
            event_type="data_access",
            user_id=user_id,
            success=True,
            details={
                "data_type": data_type,
                "action": action,
                "resource": request.path
            }
        )
```

**Audit Trail:**
- All authentication events logged
- Data access and modifications tracked
- Consent changes recorded
- Security incidents documented
- Regular audit report generation

### Threat Detection

**Anomaly Detection:**
```python
class SecurityMonitor:
    def detect_suspicious_activity(self, user_id: str, action: str) -> bool:
        # Check for unusual login patterns
        recent_logins = self.get_recent_logins(user_id, hours=24)
        if len(recent_logins) > 10:
            return True
        
        # Check for unusual data access patterns
        recent_access = self.get_recent_data_access(user_id, hours=1)
        if len(recent_access) > 100:
            return True
        
        # Check for failed authentication attempts
        failed_attempts = self.get_failed_auth_attempts(user_id, hours=1)
        if len(failed_attempts) > 5:
            return True
        
        return False
```

**Rate Limiting:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login implementation
    pass
```

## Infrastructure Security

### AWS Security Configuration

**IAM Policies:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::wellness-ai-data/user/${aws:userid}/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/UserID": "${aws:userid}"
        }
      }
    }
  ]
}
```

**Security Groups:**
- **Application Load Balancer**: Allow HTTPS (443) from internet
- **ECS Tasks**: Allow HTTP (80) from ALB only
- **RDS Database**: Allow PostgreSQL (5432) from ECS tasks only
- **Redis Cache**: Allow Redis (6379) from ECS tasks only

**VPC Configuration:**
- Private subnets for application and database tiers
- Public subnets only for load balancers
- NAT gateways for outbound internet access
- VPC Flow Logs enabled for network monitoring

### Container Security

**Docker Security:**
```dockerfile
# Use minimal base image
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Switch to non-root user
USER appuser

# Run application
CMD ["python", "app.py"]
```

**Security Scanning:**
- Automated vulnerability scanning in CI/CD
- Container image scanning with Trivy
- Dependency vulnerability checks
- License compliance verification

## Incident Response

### Security Incident Classification

**Severity Levels:**
1. **Critical**: Data breach, unauthorized access to sensitive data
2. **High**: Failed authentication attempts, suspicious activity
3. **Medium**: Configuration issues, performance degradation
4. **Low**: Minor security warnings, informational events

### Response Procedures

**Immediate Response (0-1 hour):**
1. Assess incident scope and impact
2. Isolate affected systems if necessary
3. Notify security team and management
4. Begin evidence collection and preservation

**Short-term Response (1-24 hours):**
1. Implement containment measures
2. Conduct initial investigation
3. Communicate with stakeholders
4. Prepare incident report

**Long-term Response (1-30 days):**
1. Complete thorough investigation
2. Implement corrective measures
3. Update security policies and procedures
4. Conduct post-incident review

### Communication Plan

**Internal Communication:**
- Security team notifications
- Management updates
- Technical team coordination
- Legal and compliance consultation

**External Communication:**
- User notifications (if required)
- Regulatory reporting (if applicable)
- Public disclosure (if necessary)
- Vendor coordination

## Security Testing

### Automated Testing

**Security Test Suite:**
```python
class SecurityTests(unittest.TestCase):
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious_input = "'; DROP TABLE users; --"
        response = self.client.post('/api/auth/login', json={
            'email': malicious_input,
            'password': 'password'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_xss_prevention(self):
        """Test XSS prevention"""
        malicious_input = "<script>alert('xss')</script>"
        response = self.client.post('/api/user/profile', json={
            'name': malicious_input
        })
        self.assertNotIn('<script>', response.get_data(as_text=True))
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        response = self.client.post('/api/user/profile', json={
            'name': 'test'
        })
        self.assertEqual(response.status_code, 401)  # Missing CSRF token
```

**Penetration Testing:**
- Regular automated security scans
- Manual penetration testing quarterly
- Vulnerability assessment reports
- Remediation tracking

### Code Security

**Static Analysis:**
- SonarQube for code quality and security
- Bandit for Python security issues
- ESLint security rules for JavaScript
- Dependency vulnerability scanning

**Dynamic Analysis:**
- OWASP ZAP for web application testing
- Burp Suite for API security testing
- Custom security test automation
- Continuous security monitoring

## Compliance

### GDPR Compliance

**Data Protection Principles:**
1. **Lawfulness**: Clear legal basis for data processing
2. **Fairness**: Transparent data processing practices
3. **Purpose Limitation**: Data used only for specified purposes
4. **Data Minimization**: Only necessary data collected
5. **Accuracy**: Data kept accurate and up-to-date
6. **Storage Limitation**: Data retained only as long as necessary
7. **Integrity and Confidentiality**: Appropriate security measures
8. **Accountability**: Demonstrable compliance

**User Rights Implementation:**
- Right to be informed
- Right of access
- Right to rectification
- Right to erasure
- Right to restrict processing
- Right to data portability
- Right to object
- Rights related to automated decision making

### SOC 2 Compliance

**Trust Service Criteria:**
- **Security**: Protection against unauthorized access
- **Availability**: System availability for operation
- **Processing Integrity**: System processing is complete and accurate
- **Confidentiality**: Information designated as confidential is protected
- **Privacy**: Personal information is collected, used, retained, and disclosed in conformity with commitments

## Security Training

### Developer Security Training

**Topics Covered:**
- Secure coding practices
- OWASP Top 10 vulnerabilities
- Authentication and authorization
- Data protection and privacy
- Incident response procedures

**Training Schedule:**
- Initial security training for new developers
- Annual security refresher training
- Security awareness campaigns
- Regular security updates and alerts

### User Security Awareness

**Security Guidelines:**
- Strong password requirements
- Multi-factor authentication usage
- Phishing awareness
- Data handling best practices
- Incident reporting procedures

## Conclusion

The Wellness at Work application implements comprehensive security measures to protect user data and ensure compliance with privacy regulations. The security architecture follows industry best practices and is designed to evolve with emerging threats and regulatory requirements.

Regular security assessments, monitoring, and updates ensure the application remains secure and compliant in an ever-changing threat landscape. 
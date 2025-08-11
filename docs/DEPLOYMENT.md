# Deployment Guide - Wellness at Work

This guide provides comprehensive instructions for deploying the Wellness at Work application across different environments and platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Backend Deployment](#backend-deployment)
4. [Web Dashboard Deployment](#web-dashboard-deployment)
5. [Desktop Application Distribution](#desktop-application-distribution)
6. [Production Checklist](#production-checklist)
7. [Monitoring & Maintenance](#monitoring--maintenance)

## Prerequisites

### Required Accounts & Services

- **AWS Account** with appropriate permissions
- **Google Cloud Console** account for OAuth2
- **GitHub** account for CI/CD
- **Domain name** (optional but recommended)

### Required Tools

- **Docker** and **Docker Compose**
- **Terraform** (for infrastructure as code)
- **AWS CLI** configured
- **Node.js 18+** and **npm**
- **Python 3.11+** and **pip**

## Environment Setup

### 1. AWS Infrastructure Setup

#### Using Terraform (Recommended)

```bash
# Clone the infrastructure repository
git clone https://github.com/wellness-ai/infrastructure.git
cd infrastructure

# Initialize Terraform
terraform init

# Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your configuration

# Plan and apply
terraform plan
terraform apply
```

#### Manual Setup

1. **Create VPC and Security Groups**
   ```bash
   # Create VPC
   aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications ResourceType=vpc,Tags=[{Key=Name,Value=wellness-vpc}]
   
   # Create security groups
   aws ec2 create-security-group --group-name wellness-backend-sg --description "Backend security group"
   aws ec2 create-security-group --group-name wellness-frontend-sg --description "Frontend security group"
   ```

2. **Set up RDS PostgreSQL**
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier wellness-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --master-username admin \
     --master-user-password your-secure-password \
     --allocated-storage 20 \
     --vpc-security-group-ids sg-xxxxxxxxx
   ```

3. **Create S3 Bucket**
   ```bash
   aws s3 mb s3://wellness-ai-data
   aws s3api put-bucket-encryption \
     --bucket wellness-ai-data \
     --server-side-encryption-configuration '{
       "Rules": [
         {
           "ApplyServerSideEncryptionByDefault": {
             "SSEAlgorithm": "AES256"
           }
         }
       ]
     }'
   ```

### 2. Google OAuth2 Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google+ API

2. **Create OAuth2 Credentials**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Configure authorized redirect URIs:
     - `http://localhost:3000/auth/callback` (development)
     - `https://yourdomain.com/auth/callback` (production)

3. **Download Credentials**
   - Download the JSON file
   - Place it in `configs/credentials.json`

## Backend Deployment

### Option 1: Docker Deployment

```bash
# Build the Docker image
docker build -t wellness-backend:latest backend/

# Run with environment variables
docker run -d \
  --name wellness-backend \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  wellness-backend:latest
```

### Option 2: AWS ECS Deployment

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name wellness-backend
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
   ```

2. **Push Image**
   ```bash
   docker tag wellness-backend:latest your-account.dkr.ecr.us-east-1.amazonaws.com/wellness-backend:latest
   docker push your-account.dkr.ecr.us-east-1.amazonaws.com/wellness-backend:latest
   ```

3. **Create ECS Service**
   ```bash
   # Create task definition
   aws ecs register-task-definition --cli-input-json file://task-definition.json
   
   # Create service
   aws ecs create-service \
     --cluster wellness-cluster \
     --service-name wellness-backend \
     --task-definition wellness-backend:1 \
     --desired-count 2
   ```

### Option 3: AWS Lambda Deployment

```bash
# Install serverless framework
npm install -g serverless

# Deploy
cd backend
serverless deploy
```

## Web Dashboard Deployment

### Option 1: AWS S3 + CloudFront

1. **Build the Application**
   ```bash
   cd web_dashboard
   npm run build
   ```

2. **Deploy to S3**
   ```bash
   aws s3 sync build/ s3://wellness-web-bucket --delete
   ```

3. **Create CloudFront Distribution**
   ```bash
   aws cloudfront create-distribution \
     --distribution-config file://cloudfront-config.json
   ```

### Option 2: Vercel Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd web_dashboard
vercel --prod
```

### Option 3: Netlify Deployment

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd web_dashboard
netlify deploy --prod --dir=build
```

## Desktop Application Distribution

### Windows Distribution

#### Option 1: PyInstaller Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed \
  --add-data "configs/credentials.json;configs/" \
  --icon=assets/icon.ico \
  --name="Wellness at Work" \
  src/desktop_app/main.py
```

#### Option 2: MSIX Package

```bash
# Install MSIX packaging tools
pip install msix-packaging

# Create MSIX package
msix-packaging create \
  --input-dir dist/Wellness\ at\ Work \
  --output-file WellnessAtWork.msix \
  --identity "Wellness.ai.WellnessAtWork" \
  --version "1.0.0.0"
```

### macOS Distribution

#### Option 1: .app Bundle

```bash
# Build .app bundle
pyinstaller --onefile --windowed \
  --add-data "configs/credentials.json:configs/" \
  --icon=assets/icon.icns \
  --name="Wellness at Work" \
  src/desktop_app/main.py

# Create .app bundle
mkdir -p "Wellness at Work.app/Contents/MacOS"
mkdir -p "Wellness at Work.app/Contents/Resources"
cp dist/Wellness\ at\ Work "Wellness at Work.app/Contents/MacOS/"
cp assets/icon.icns "Wellness at Work.app/Contents/Resources/"
```

#### Option 2: TestFlight Distribution

1. **Code Signing**
   ```bash
   # Create certificate
   security create-certificate \
     --certificate wellness-cert.p12 \
     --private-key wellness-key.p12 \
     --password your-password
   
   # Sign application
   codesign --force --sign "Developer ID Application: Wellness.ai" \
     "Wellness at Work.app"
   ```

2. **Create DMG**
   ```bash
   # Install create-dmg
   brew install create-dmg
   
   # Create DMG
   create-dmg \
     --volname "Wellness at Work" \
     --window-pos 200 120 \
     --window-size 600 300 \
     --icon-size 100 \
     --icon "Wellness at Work.app" 175 120 \
     --hide-extension "Wellness at Work.app" \
     --app-drop-link 425 120 \
     "Wellness at Work.dmg" \
     "Wellness at Work.app"
   ```

3. **Upload to App Store Connect**
   - Use Xcode or Application Loader
   - Follow Apple's guidelines for TestFlight distribution

## Production Checklist

### Security Checklist

- [ ] All secrets and API keys are properly configured
- [ ] HTTPS is enabled for all endpoints
- [ ] CORS is properly configured
- [ ] Rate limiting is implemented
- [ ] Input validation is in place
- [ ] SQL injection protection is active
- [ ] XSS protection is implemented
- [ ] CSRF protection is enabled

### Performance Checklist

- [ ] Database indexes are optimized
- [ ] CDN is configured for static assets
- [ ] Caching is implemented
- [ ] Load balancing is configured
- [ ] Auto-scaling is enabled
- [ ] Monitoring and alerting are set up

### GDPR Compliance Checklist

- [ ] Data encryption is enabled
- [ ] User consent management is implemented
- [ ] Data export functionality is working
- [ ] Data deletion functionality is working
- [ ] Privacy policy is updated
- [ ] Cookie consent is implemented

### Testing Checklist

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Performance tests pass
- [ ] User acceptance tests pass
- [ ] Cross-browser testing is complete

## Monitoring & Maintenance

### Application Monitoring

1. **Set up AWS CloudWatch**
   ```bash
   # Create CloudWatch dashboard
   aws cloudwatch put-dashboard \
     --dashboard-name WellnessAtWork \
     --dashboard-body file://dashboard.json
   ```

2. **Configure Alerts**
   ```bash
   # Create alarm for high CPU usage
   aws cloudwatch put-metric-alarm \
     --alarm-name "High CPU Usage" \
     --alarm-description "CPU usage is high" \
     --metric-name CPUUtilization \
     --namespace AWS/ECS \
     --statistic Average \
     --period 300 \
     --threshold 80 \
     --comparison-operator GreaterThanThreshold
   ```

### Log Management

1. **Set up ELK Stack**
   ```bash
   # Deploy Elasticsearch
   docker run -d --name elasticsearch \
     -p 9200:9200 \
     -e "discovery.type=single-node" \
     elasticsearch:7.17.0
   
   # Deploy Logstash
   docker run -d --name logstash \
     -p 5044:5044 \
     logstash:7.17.0
   
   # Deploy Kibana
   docker run -d --name kibana \
     -p 5601:5601 \
     kibana:7.17.0
   ```

### Backup Strategy

1. **Database Backups**
   ```bash
   # Enable automated backups in RDS
   aws rds modify-db-instance \
     --db-instance-identifier wellness-db \
     --backup-retention-period 7 \
     --preferred-backup-window "03:00-04:00"
   ```

2. **S3 Data Backups**
   ```bash
   # Enable versioning
   aws s3api put-bucket-versioning \
     --bucket wellness-ai-data \
     --versioning-configuration Status=Enabled
   
   # Set up lifecycle policy
   aws s3api put-bucket-lifecycle-configuration \
     --bucket wellness-ai-data \
     --lifecycle-configuration file://lifecycle.json
   ```

### Update Strategy

1. **Blue-Green Deployment**
   ```bash
   # Deploy new version to green environment
   aws ecs update-service \
     --cluster wellness-cluster \
     --service wellness-backend-green \
     --task-definition wellness-backend:2
   
   # Switch traffic
   aws elbv2 modify-listener \
     --listener-arn arn:aws:elasticloadbalancing:... \
     --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
   ```

2. **Rollback Plan**
   ```bash
   # Rollback to previous version
   aws ecs update-service \
     --cluster wellness-cluster \
     --service wellness-backend \
     --task-definition wellness-backend:1
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check security group rules
   - Verify connection string
   - Check RDS status

2. **Authentication Issues**
   - Verify OAuth2 credentials
   - Check redirect URIs
   - Validate JWT configuration

3. **Performance Issues**
   - Monitor CloudWatch metrics
   - Check database query performance
   - Review application logs

### Support Resources

- **Documentation**: [docs/](docs/)
- **GitHub Issues**: [Issues](https://github.com/wellness-ai/wellness-at-work/issues)
- **Community**: [Discord](https://discord.gg/wellness-ai)
- **Email Support**: support@wellness.ai

---

**Note**: This deployment guide should be updated regularly as the application evolves. Always test deployments in a staging environment before applying to production. 
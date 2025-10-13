# Production Deployment Guide - AWS & Google Cloud

## 🌍 Redis in Development vs Production

### Development (Your Current Setup)
- **Redis**: Local Docker container
- **Database**: Local PostgreSQL
- **Frontend**: Electron (desktop app)
- **Backend**: Local Django server

### Production (Target Setup)
- **Redis**: AWS ElastiCache or Google Cloud Memorystore
- **Database**: AWS RDS or Google Cloud SQL
- **Frontend**: Web application (React)
- **Backend**: AWS ECS or Google Cloud Run

---

## 🚀 AWS Deployment

### **1. Infrastructure Setup**

#### **VPC Configuration**
```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet --vpc-id vpc-12345 --cidr-block 10.0.1.0/24
aws ec2 create-subnet --vpc-id vpc-12345 --cidr-block 10.0.2.0/24
```

#### **Security Groups**
```bash
# Web tier security group
aws ec2 create-security-group --group-name web-tier --description "Web tier security group"

# Database tier security group
aws ec2 create-security-group --group-name db-tier --description "Database tier security group"
```

### **2. Database Setup (RDS)**

#### **PostgreSQL Instance**
```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name scrimgg-db-subnet-group \
  --db-subnet-group-description "Subnet group for Scrim.GG database" \
  --subnet-ids subnet-12345 subnet-67890

# Create PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier scrimgg-prod-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 13.7 \
  --master-username scrimgg \
  --master-user-password YourSecurePassword123 \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-12345 \
  --db-subnet-group-name scrimgg-db-subnet-group
```

### **3. Redis Setup (ElastiCache)**

#### **Redis Cluster**
```bash
# Create Redis subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name scrimgg-redis-subnet-group \
  --cache-subnet-group-description "Subnet group for Scrim.GG Redis" \
  --subnet-ids subnet-12345 subnet-67890

# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id scrimgg-redis-cluster \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --cache-subnet-group-name scrimgg-redis-subnet-group \
  --security-group-ids sg-12345
```

### **4. Application Deployment (ECS)**

#### **Docker Configuration**
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "scrimgg.wsgi:application"]
```

#### **ECS Task Definition**
```json
{
  "family": "scrimgg-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "scrimgg-backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/scrimgg:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DJANGO_SETTINGS_MODULE",
          "value": "scrimgg.settings.production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:scrimgg/database"
        }
      ]
    }
  ]
}
```

---

## ☁️ Google Cloud Deployment

### **1. Infrastructure Setup**

#### **VPC Network**
```bash
# Create VPC
gcloud compute networks create scrimgg-vpc --subnet-mode custom

# Create subnets
gcloud compute networks subnets create web-subnet \
  --network scrimgg-vpc \
  --range 10.0.1.0/24 \
  --region us-central1

gcloud compute networks subnets create db-subnet \
  --network scrimgg-vpc \
  --range 10.0.2.0/24 \
  --region us-central1
```

#### **Firewall Rules**
```bash
# Web tier firewall
gcloud compute firewall-rules create allow-web \
  --network scrimgg-vpc \
  --allow tcp:80,tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --target-tags web-tier

# Database tier firewall
gcloud compute firewall-rules create allow-db \
  --network scrimgg-vpc \
  --allow tcp:5432 \
  --source-tags web-tier \
  --target-tags db-tier
```

### **2. Database Setup (Cloud SQL)**

#### **PostgreSQL Instance**
```bash
# Create PostgreSQL instance
gcloud sql instances create scrimgg-prod-db \
  --database-version POSTGRES_13 \
  --tier db-f1-micro \
  --region us-central1 \
  --network scrimgg-vpc \
  --no-assign-ip

# Create database
gcloud sql databases create scrimgg --instance scrimgg-prod-db

# Create user
gcloud sql users create scrimgg \
  --instance scrimgg-prod-db \
  --password YourSecurePassword123
```

### **3. Redis Setup (Memorystore)**

#### **Redis Instance**
```bash
# Create Redis instance
gcloud redis instances create scrimgg-redis \
  --size 1 \
  --region us-central1 \
  --network scrimgg-vpc \
  --redis-version redis_6_x
```

### **4. Application Deployment (Cloud Run)**

#### **Docker Configuration**
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "scrimgg.wsgi:application"]
```

#### **Cloud Run Deployment**
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/your-project/scrimgg
gcloud run deploy scrimgg-backend \
  --image gcr.io/your-project/scrimgg \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DJANGO_SETTINGS_MODULE=scrimgg.settings.production
```

---

## 🔧 Configuration Management

### **Environment Variables**
```bash
# Production settings
export DJANGO_SETTINGS_MODULE=scrimgg.settings.production
export DATABASE_URL=postgresql://user:pass@host:5432/db
export REDIS_URL=redis://host:6379/0
export SECRET_KEY=your-secret-key
export DEBUG=False
export ALLOWED_HOSTS=your-domain.com
```

### **Secrets Management**
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name scrimgg/database \
  --description "Database credentials for Scrim.GG" \
  --secret-string '{"username":"scrimgg","password":"YourSecurePassword123"}'

# Google Secret Manager
gcloud secrets create database-credentials \
  --data-file=credentials.json
```

---

## 📊 Monitoring & Logging

### **AWS CloudWatch**
```bash
# Create log group
aws logs create-log-group --log-group-name /aws/ecs/scrimgg-backend

# Create log stream
aws logs create-log-stream \
  --log-group-name /aws/ecs/scrimgg-backend \
  --log-stream-name scrimgg-backend-stream
```

### **Google Cloud Logging**
```bash
# Enable logging
gcloud logging logs create scrimgg-backend-logs
```

---

## 🔒 Security Considerations

### **SSL/TLS**
- Use AWS Certificate Manager or Google Cloud SSL
- Enable HTTPS redirect
- Configure secure headers

### **Database Security**
- Use VPC peering
- Enable encryption at rest
- Regular security updates

### **Application Security**
- Environment variable secrets
- Regular dependency updates
- Security headers configuration

---

## 💰 Cost Optimization

### **AWS Cost Optimization**
- Use reserved instances for predictable workloads
- Enable auto-scaling
- Monitor CloudWatch costs

### **Google Cloud Cost Optimization**
- Use committed use discounts
- Enable auto-scaling
- Monitor billing alerts

---

## 🚀 Deployment Checklist

### **Pre-Deployment**
- [ ] Code reviewed and tested
- [ ] Database migrations ready
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Domain DNS configured

### **Deployment**
- [ ] Infrastructure provisioned
- [ ] Database created and migrated
- [ ] Redis instance created
- [ ] Application deployed
- [ ] Load balancer configured
- [ ] SSL certificates installed

### **Post-Deployment**
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Logs accessible
- [ ] Performance baseline established
- [ ] Backup strategy implemented

---

## 📞 Support & Troubleshooting

### **Common Issues**
1. **Database Connection**: Check VPC configuration
2. **Redis Connection**: Verify security groups
3. **SSL Issues**: Check certificate configuration
4. **Performance**: Monitor resource usage

### **Debug Commands**
```bash
# Check application logs
aws logs describe-log-streams --log-group-name /aws/ecs/scrimgg-backend

# Check database connectivity
psql -h your-db-host -U scrimgg -d scrimgg

# Check Redis connectivity
redis-cli -h your-redis-host ping
```

---

**Ready for production deployment! Follow this guide step by step.** 🚀

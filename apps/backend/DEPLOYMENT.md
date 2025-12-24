# Deployment Guide - Genesis Backend with Vertex AI

Complete guide for deploying the Genesis backend to production using Google Cloud.

## 📋 Pre-Deployment Checklist

- [ ] Google Cloud project created
- [ ] Vertex AI API enabled
- [ ] Service account created with appropriate permissions
- [ ] Supabase PostgreSQL database configured
- [ ] Redis (Upstash) account set up
- [ ] Environment variables configured
- [ ] All tests passing (`python test_vertex_ai.py --test-all`)
- [ ] API endpoints tested locally

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                   │
│                 (Separate deployment)                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Cloud Run)                │
│  ┌────────────────────────────────────────────────────┐ │
│  │  API Routes (/v1/*)                               │ │
│  │  - /content/* (Vertex AI content generation)       │ │
│  │  - /guardrails/* (Safety validation)               │ │
│  │  - /embeddings/* (Vector embeddings)               │ │
│  │  - /blog/* (Blog generation)                       │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Core Services                                     │ │
│  │  - VertexAI LLM (google-cloud-aiplatform)         │ │
│  │  - InputGuardrails (Safety layer)                 │ │
│  │  - TextChunker (Text splitting)                   │ │
│  │  - LocalEmbeddings (sentence-transformers)        │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  LangGraph Workflows                              │ │
│  │  - ContentGenerationAgent (3-node pipeline)       │ │
│  │  - BlogGraph (blog generation)                    │ │
│  │  - MultiAgentGraph (orchestration)                │ │
│  └────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┬────────────┐
         │           │           │            │
         ▼           ▼           ▼            ▼
    ┌────────┐  ┌───────┐  ┌─────────┐  ┌─────────┐
    │Vertex  │  │Cloud  │  │Supabase │  │Upstash  │
    │AI LLM  │  │Storage│  │PostgreSQL Redis     │
    └────────┘  └───────┘  └─────────┘  └─────────┘
```

## 🚀 Deployment Options

### Option 1: Google Cloud Run (Recommended)

Cloud Run is ideal for FastAPI applications - serverless, auto-scaling, pay-per-use.

#### 1.1 Setup GCP Project

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

#### 1.2 Create Service Account

```bash
# Create service account
gcloud iam service-accounts create genesis-backend \
  --display-name="Genesis Backend Service"

# Grant Vertex AI access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:genesis-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Grant basic roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:genesis-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/editor"

# Create and download key
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=genesis-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

#### 1.3 Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### 1.4 Build and Deploy

```bash
# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/genesis-backend

# Deploy to Cloud Run
gcloud run deploy genesis-backend \
  --image gcr.io/YOUR_PROJECT_ID/genesis-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars=GCP_PROJECT_ID=YOUR_PROJECT_ID,SUPABASE_URL=YOUR_SUPABASE_URL,SUPABASE_KEY=YOUR_KEY,UPSTASH_REDIS_REST_URL=YOUR_REDIS_URL,UPSTASH_REDIS_REST_TOKEN=YOUR_TOKEN \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --service-account genesis-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Option 2: Docker + Cloud Run with GitHub Actions

#### 2.1 Create `.github/workflows/deploy.yml`

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
    paths:
      - 'apps/backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          export_default_credentials: true
      
      - name: Configure Docker
        run: |
          gcloud auth configure-docker gcr.io
      
      - name: Build and Push
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/genesis-backend:${{ github.sha }} apps/backend/
          docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/genesis-backend:${{ github.sha }}
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy genesis-backend \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/genesis-backend:${{ github.sha }} \
            --platform managed \
            --region us-central1 \
            --set-env-vars=GCP_PROJECT_ID=${{ secrets.GCP_PROJECT_ID }},SUPABASE_URL=${{ secrets.SUPABASE_URL }},SUPABASE_KEY=${{ secrets.SUPABASE_KEY }} \
            --memory 2Gi \
            --cpu 2
```

#### 2.2 Add Secrets to GitHub

Go to repository Settings → Secrets and add:
- `GCP_SA_KEY` - Service account JSON (base64 encoded)
- `GCP_PROJECT_ID` - Your GCP project ID
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `UPSTASH_REDIS_REST_URL` - Redis URL
- `UPSTASH_REDIS_REST_TOKEN` - Redis token

### Option 3: Google Compute Engine (Traditional VPS)

#### 3.1 Create VM Instance

```bash
gcloud compute instances create genesis-backend \
  --zone=us-central1-a \
  --machine-type=n1-standard-2 \
  --boot-disk-size=50GB \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

#### 3.2 SSH and Setup

```bash
# SSH into VM
gcloud compute ssh genesis-backend --zone=us-central1-a

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip docker.io nginx

# Clone repository
git clone https://github.com/your-org/genesis.git
cd genesis/apps/backend

# Install Python packages
pip install -r requirements.txt
```

#### 3.3 Setup Systemd Service

```bash
sudo tee /etc/systemd/system/genesis-backend.service > /dev/null <<EOF
[Unit]
Description=Genesis Backend
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/genesis/apps/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
Environment="GCP_PROJECT_ID=YOUR_PROJECT_ID"
Environment="SUPABASE_URL=YOUR_SUPABASE_URL"
Environment="SUPABASE_KEY=YOUR_KEY"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start genesis-backend
sudo systemctl enable genesis-backend
```

## 🔐 Environment Configuration

### Required Variables

```bash
# GCP
GCP_PROJECT_ID=your-project-id                    # Required

# Database
SUPABASE_URL=https://your-project.supabase.co    # Required
SUPABASE_KEY=your-anon-key                        # Required

# Redis/Caching
UPSTASH_REDIS_REST_URL=https://...               # Optional
UPSTASH_REDIS_REST_TOKEN=...                     # Optional

# Credentials (Cloud Run uses service account)
GOOGLE_APPLICATION_CREDENTIALS=...               # Handled by service account
```

### Cloud Run Secrets

Use Google Cloud Secret Manager:

```bash
# Create secrets
echo -n "your-supabase-url" | gcloud secrets create SUPABASE_URL --data-file=-
echo -n "your-supabase-key" | gcloud secrets create SUPABASE_KEY --data-file=-
echo -n "your-redis-url" | gcloud secrets create UPSTASH_REDIS_URL --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding SUPABASE_URL \
  --member=serviceAccount:genesis-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Reference in deployment:
# --set-env-vars SUPABASE_URL=/secret:SUPABASE_URL
```

## 📊 Monitoring & Logging

### Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=genesis-backend" \
  --format=json \
  --limit=50

# Create log filter
gcloud logging sinks create error-sink \
  logging.googleapis.com/projects/YOUR_PROJECT_ID/logs/errors \
  --log-filter='severity=ERROR resource.type=cloud_run_revision'
```

### Cloud Monitoring

```bash
# Create dashboard
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

Dashboard example (`dashboard.json`):
```json
{
  "displayName": "Genesis Backend",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Latency",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\""
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Requests",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\""
                }
              }
            }]
          }
        }
      }
    ]
  }
}
```

## 🧪 Testing Deployment

### Health Check

```bash
curl https://genesis-backend-YOUR_ID.run.app/v1/health

# Expected response:
# {"status":"ok"}
```

### API Test

```bash
curl -X POST "https://genesis-backend-YOUR_ID.run.app/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a short poem",
    "safety_level": "moderate",
    "conversation_history": []
  }'
```

### Performance Test

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 https://genesis-backend-YOUR_ID.run.app/v1/health/redis
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Example `.github/workflows/main.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r apps/backend/requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          cd apps/backend
          python test_vertex_ai.py --test-guardrails
          python test_vertex_ai.py --test-chunking
          python test_vertex_ai.py --test-embeddings
  
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Cloud Run
        # ... (deployment steps from Option 2)
```

## 📈 Scaling Considerations

### Horizontal Scaling (Cloud Run)

Cloud Run automatically scales based on traffic:
- Minimum instances: 0 (scale down to save costs)
- Maximum instances: 1000 (adjustable)
- Concurrency per instance: 80 requests

```bash
# Adjust concurrency
gcloud run deploy genesis-backend \
  --concurrency 200 \
  --region us-central1
```

### Database Scaling (Supabase)

```sql
-- Enable connection pooling
-- In Supabase: Database → Connection Pooling → Enable

-- Add indexes for faster queries
CREATE INDEX CONCURRENTLY idx_content_embeddings_content_id 
  ON content_embeddings(content_id);
```

### Caching Strategy

```python
# Use Redis for caching
from core.upstash_redis import UpstashRedisClient

redis = UpstashRedisClient.get_instance()

# Cache embeddings
cache_key = f"embedding:{text_hash}"
cached = redis.get(cache_key)
if cached:
    return json.loads(cached)
```

## 🚨 Troubleshooting Deployment

### Cloud Run Issues

```bash
# Check deployment status
gcloud run services describe genesis-backend --region us-central1

# View real-time logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=genesis-backend" \
  --follow
```

### Authentication Issues

```bash
# Test service account
gcloud auth activate-service-account --key-file=service-account-key.json

# List roles
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:genesis-backend*"
```

### Performance Issues

```bash
# Check resource usage
gcloud monitoring time-series list \
  --filter='resource.type=cloud_run_revision AND metric.type=run.googleapis.com/request_count'

# Increase memory/CPU
gcloud run deploy genesis-backend \
  --memory 4Gi \
  --cpu 4 \
  --region us-central1
```

## 🔒 Security Checklist

- [ ] Service account has minimum required permissions
- [ ] Secrets stored in Cloud Secret Manager (not environment variables)
- [ ] CORS configured for frontend domain only
- [ ] API endpoints protected with authentication (add later)
- [ ] Database connection uses SSL/TLS
- [ ] Input validation via guardrails enabled
- [ ] Rate limiting configured (Cloud Armor)
- [ ] Logging and monitoring set up
- [ ] Regular backups enabled (Supabase automatic)

## 📚 Useful Commands

```bash
# Deploy with latest code
gcloud run deploy genesis-backend \
  --source . \
  --region us-central1

# Get service URL
gcloud run services describe genesis-backend --region us-central1 --format='value(status.url)'

# Stream logs
gcloud logging tail -n 50 --follow \
  "resource.type=cloud_run_revision AND resource.labels.service_name=genesis-backend"

# Scale down to zero for cost savings
gcloud run deploy genesis-backend \
  --min-instances 0 \
  --region us-central1
```

## 💰 Cost Estimation

### Cloud Run (Estimated Monthly)

- **Compute**: $0.00004/CPU-second, $0.0000025/GB-second
- **Requests**: $0.40 per 1M requests
- **Storage**: ~$0.02/GB
- Example (100k requests/day, 2CPU, 2GB): ~$50/month

### Vertex AI (Estimated Monthly)

- **Input tokens**: $0.075/1M tokens (Gemini 2.0 Flash)
- **Output tokens**: $0.30/1M tokens
- Example (1M input + 500k output/day): ~$12/month

### Database (Supabase, Estimated Monthly)

- **Storage**: $0.125/GB
- **Bandwidth**: $0.09/GB
- Example (10GB storage, 100GB bandwidth): ~$10/month

**Total Estimated Monthly Cost**: $50-100

## 🎓 Next Steps

1. Set up GCP project and service account
2. Configure Supabase database
3. Deploy to Cloud Run
4. Set up monitoring and logging
5. Configure CI/CD pipeline
6. Enable auto-scaling
7. Monitor costs and performance
8. Set up alerting for errors

## 📞 Support

For deployment issues:
1. Check [Cloud Run Documentation](https://cloud.google.com/run/docs)
2. Review [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
3. Check [Backend README](./BACKEND_README.md)
4. View Cloud Logging for error details

# deploy_gcp.ps1
# Automates deployment of Genesis Backend and Frontend to Google Cloud Run

Write-Host " Genesis GCP Deployment Script" -ForegroundColor Cyan
Write-Host "================================="

# 1. Configuration
$ProjectId = if ($args[0]) { $args[0] } else { Read-Host "Enter your Google Cloud Project ID" }

if (-not $ProjectId) {
    Write-Error "Project ID is required."
    exit 1
}

$Region = "us-central1"
$BackendServiceName = "genesis-backend"
$FrontendServiceName = "genesis-frontend"

# Check gcloud
if (-not (Get-Command "gcloud" -ErrorAction SilentlyContinue)) {
    Write-Error "Google Cloud SDK (gcloud) is not installed."
    exit 1
}

# Set Project
Write-Host "`nSetting GCP Project to $ProjectId..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable Services
Write-Host "Enabling required services..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com

# 2. Deploy Backend
Write-Host "Deploying Backend..." -ForegroundColor Cyan

# Check if .env exists to read secrets
if (Test-Path "apps/backend/.env") {
    Write-Host "Reading env vars from apps/backend/.env..."
    # Simplified reading - in production use Secret Manager
    # For now, we will ask user to confirm deployment with env vars from file?
    # Actually, let's just use the build command which builds remotely
}

Write-Host "Building and Deploying Backend to Cloud Run..."
# We use gcloud run deploy --source . which handles build+deploy in one step using Cloud Build
Set-Location "apps/backend"
gcloud run deploy $BackendServiceName `
    --source . `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2
    # Add --set-env-vars here if you want to push local .env vars, but usually better to set in Console or Secret Manager

if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend deployment failed."
    exit 1
}

# Get Backend URL
$BackendUrl = gcloud run services describe $BackendServiceName --region $Region --format 'value(status.url)'
Write-Host "Backend Deployed at: $BackendUrl" -ForegroundColor Green
Set-Location "../.."

# 3. Deploy Frontend
# Write-Host "Deploying Frontend..." -ForegroundColor Cyan
#
# # We need to pass the NEXT_PUBLIC_API_URL to the frontend build
# Write-Host "Using Backend URL for Frontend: $BackendUrl"
# 
# Set-Location "apps/frontend"
# # Next.js requires build args for public env vars
# gcloud run deploy $FrontendServiceName `
#     --source . `
#     --platform managed `
#     --region $Region `
#     --allow-unauthenticated `
#     --memory 1Gi `
#     --set-env-vars NEXT_PUBLIC_BACKEND_URL=$BackendUrl
# 
# if ($LASTEXITCODE -ne 0) {
#     Write-Error "Frontend deployment failed."
#     exit 1
# }
# 
# $FrontendUrl = gcloud run services describe $FrontendServiceName --region $Region --format 'value(status.url)'
# Write-Host "Frontend Deployed at: $FrontendUrl" -ForegroundColor Green
# Set-Location "../.."

Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "Backend: $BackendUrl"
# Write-Host "Frontend: $FrontendUrl"
Write-Host "IMPORTANT: Go to GCP Console and configure your secrets (SUPABASE_URL, etc.) for the Backend service if you haven't done so via Secret Manager or flags."

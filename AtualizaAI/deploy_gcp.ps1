# Deploy Script for Flose AI Platform to GCP
# v4.2 - Debugging and Robust Tagging

$env_file = ".env"
if (-Not (Test-Path $env_file)) {
    Write-Error ".env file not found!"
    exit 1
}

$env_lines = Get-Content $env_file
$PROJECT_ID = (($env_lines | Select-String "GCP_PROJECT_ID=").ToString().Split("=")[1]).Trim()
$GEMINI_KEY = (($env_lines | Select-String "GEMINI_API_KEY=").ToString().Split("=")[1]).Trim()
$TG_TOKEN = (($env_lines | Select-String "TELEGRAM_BOT_TOKEN=").ToString().Split("=")[1]).Trim()
$MASTER_KEY = (($env_lines | Select-String "MASTER_KEY=").ToString().Split("=")[1]).Trim()

$REGION = "us-central1"
$REPO_NAME = "flose-repo"
$IMAGE_NAME = "flose-ai-platform"
# Use curly braces to ensure variables are parsed correctly in PowerShell
$FULL_IMAGE_PATH = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"

Write-Host "--- DETALHES DO DEPLOY ---"
Write-Host "Projeto: $PROJECT_ID"
Write-Host "Regiao: $REGION"
Write-Host "Imagem: $FULL_IMAGE_PATH"
Write-Host "--------------------------"

# 1. APIs
Write-Host "Habilitando APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com --project=$PROJECT_ID --quiet

# 2. Artifact Registry
Write-Host "Verificando Repositorio..."
$repo_exists = gcloud artifacts repositories describe $REPO_NAME --location=$REGION --project=$PROJECT_ID 2>$null
if (-Not $repo_exists) {
    gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION --project=$PROJECT_ID --quiet
}

# 3. Secret Manager
function Set-GCP-Secret-v2($Name, $Value) {
    $exists = gcloud secrets list --filter="name ~ $Name" --project=$PROJECT_ID --format="value(name)"
    if (-Not $exists) {
        gcloud secrets create $Name --replication-policy="automatic" --project=$PROJECT_ID --quiet
    }
    $tempFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tempFile, $Value)
    gcloud secrets versions add $Name --data-file=$tempFile --project=$PROJECT_ID --quiet
    Remove-Item $tempFile
}

Set-GCP-Secret-v2 "GEMINI_API_KEY" $GEMINI_KEY
Set-GCP-Secret-v2 "TELEGRAM_BOT_TOKEN" $TG_TOKEN
Set-GCP-Secret-v2 "MASTER_KEY" $MASTER_KEY

# 4. Build
Write-Host "Enviando Build (Ignore configurado)..."
# gcloud uses .gcloudignore automatically
gcloud builds submit --tag "$FULL_IMAGE_PATH" . --project=$PROJECT_ID

# 5. IAM Permissions
Write-Host "Configurando IAM..."
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
$SERVICE_ACCOUNT = "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding GEMINI_API_KEY --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" --project=$PROJECT_ID --quiet
gcloud secrets add-iam-policy-binding TELEGRAM_BOT_TOKEN --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" --project=$PROJECT_ID --quiet
gcloud secrets add-iam-policy-binding MASTER_KEY --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" --project=$PROJECT_ID --quiet

# 6. Cloud Run Deploy
Write-Host "Deploying to Cloud Run (On-Demand / Eco Mode)..."
gcloud run deploy $IMAGE_NAME `
    --image "$FULL_IMAGE_PATH" `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --project=$PROJECT_ID `
    --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID" `
    --cpu 2 `
    --memory 2Gi `
    --min-instances 0 `
    --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest,TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest,MASTER_KEY=MASTER_KEY:latest"

# 7. Configurar Webhook do Telegram
Write-Host "Configurando Webhook do Telegram..."
$SERVICE_URL = gcloud run services describe $IMAGE_NAME --platform managed --region $REGION --project=$PROJECT_ID --format="value(status.url)"
$WEBHOOK_URL = "${SERVICE_URL}/telegram_webhook"

# Chamada simples para o Telegram registrar o webhook
Invoke-RestMethod -Uri "https://api.telegram.org/bot${TG_TOKEN}/setWebhook?url=${WEBHOOK_URL}"

Write-Host "--- DEPLOY Eco-Mode COMPLETADO ---" -ForegroundColor Green
Write-Host "Webhook URL: $WEBHOOK_URL"

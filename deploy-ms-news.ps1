# PowerShell script to deploy Microsoft News RSS MCP Server to Azure Container Apps
# Follows the same pattern as deploy-to-aca.ps1
# Prerequisites: Azure CLI installed and logged in (az login)

# Configuration variables — can be set via environment variables or use defaults
if ([string]::IsNullOrWhiteSpace($env:RESOURCE_GROUP)) {
    $RESOURCE_GROUP = "rg-mcp-server"
} else {
    $RESOURCE_GROUP = $env:RESOURCE_GROUP
}

if ([string]::IsNullOrWhiteSpace($env:LOCATION)) {
    $LOCATION = "eastus"
} else {
    $LOCATION = $env:LOCATION
}

if ([string]::IsNullOrWhiteSpace($env:ACR_NAME)) {
    $ACR_NAME = "acrmcpserver$(Get-Random -Minimum 1000 -Maximum 9999)"
} else {
    $ACR_NAME = $env:ACR_NAME
}

if ([string]::IsNullOrWhiteSpace($env:CONTAINER_APP_NAME)) {
    $CONTAINER_APP_NAME = "ms-news-mcp-server"
} else {
    $CONTAINER_APP_NAME = $env:CONTAINER_APP_NAME
}

if ([string]::IsNullOrWhiteSpace($env:CONTAINER_APP_ENV)) {
    $CONTAINER_APP_ENV = "mcp-server-env"
} else {
    $CONTAINER_APP_ENV = $env:CONTAINER_APP_ENV
}

if ([string]::IsNullOrWhiteSpace($env:IMAGE_NAME)) {
    $IMAGE_NAME = "ms-news-mcp-server"
} else {
    $IMAGE_NAME = $env:IMAGE_NAME
}

if ([string]::IsNullOrWhiteSpace($env:IMAGE_TAG)) {
    $IMAGE_TAG = "latest"
} else {
    $IMAGE_TAG = $env:IMAGE_TAG
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Microsoft News MCP Server - ACA Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Resource Group : $RESOURCE_GROUP" -ForegroundColor White
Write-Host "  Location       : $LOCATION" -ForegroundColor White
Write-Host "  ACR Name       : $ACR_NAME" -ForegroundColor White
Write-Host "  App Name       : $CONTAINER_APP_NAME" -ForegroundColor White
Write-Host "  App Env        : $CONTAINER_APP_ENV" -ForegroundColor White
Write-Host "  Image          : ${IMAGE_NAME}:${IMAGE_TAG}" -ForegroundColor White
Write-Host ""

# Step 1: Create Resource Group (idempotent — safe to re-run if already exists)
Write-Host "[1/7] Creating Resource Group: $RESOURCE_GROUP" -ForegroundColor Yellow
az group create --name $RESOURCE_GROUP --location $LOCATION
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create resource group"; exit 1 }

# Step 2: Create Azure Container Registry
Write-Host "[2/7] Creating Azure Container Registry: $ACR_NAME" -ForegroundColor Yellow
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create ACR"; exit 1 }

# Step 3: Build and push Docker image to ACR using Dockerfile.ms-news
Write-Host "[3/7] Building Docker image from Dockerfile.ms-news..." -ForegroundColor Yellow
az acr build `
    --registry $ACR_NAME `
    --image "${IMAGE_NAME}:${IMAGE_TAG}" `
    --file Dockerfile.ms-news `
    .
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to build image"; exit 1 }

# Step 4: Get ACR credentials
Write-Host "[4/7] Getting ACR credentials..." -ForegroundColor Yellow
$ACR_LOGIN_SERVER = az acr show --name $ACR_NAME --query loginServer --output tsv
$ACR_USERNAME     = az acr credential show --name $ACR_NAME --query username --output tsv
$ACR_PASSWORD     = az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv

# Step 5: Create Container Apps Environment (idempotent — safe to re-run)
Write-Host "[5/7] Creating Container Apps Environment: $CONTAINER_APP_ENV" -ForegroundColor Yellow
az containerapp env create `
    --name $CONTAINER_APP_ENV `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create Container Apps environment"; exit 1 }

# Step 6: Create (or update) Container App
Write-Host "[6/7] Creating Container App: $CONTAINER_APP_NAME" -ForegroundColor Yellow
az containerapp create `
    --name $CONTAINER_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --environment $CONTAINER_APP_ENV `
    --image "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}" `
    --registry-server $ACR_LOGIN_SERVER `
    --registry-username $ACR_USERNAME `
    --registry-password $ACR_PASSWORD `
    --target-port 8000 `
    --ingress external `
    --cpu 0.5 `
    --memory 1.0Gi `
    --min-replicas 1 `
    --max-replicas 3
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create Container App"; exit 1 }

# Step 7: Get the FQDN and print the MCP endpoint
Write-Host "[7/7] Retrieving endpoint URL..." -ForegroundColor Yellow
$FQDN = az containerapp show `
    --name $CONTAINER_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --query properties.configuration.ingress.fqdn `
    --output tsv

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "Deployment Successful!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "MCP Server Endpoint : https://$FQDN/mcp" -ForegroundColor Cyan
Write-Host "Health Check        : https://$FQDN/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Add this to your .env file:" -ForegroundColor Yellow
Write-Host "  MS_NEWS_MCP_SERVER_URL=https://$FQDN/mcp" -ForegroundColor White
Write-Host ""
Write-Host "Test with MCP Inspector:" -ForegroundColor Yellow
Write-Host "  npx @modelcontextprotocol/inspector https://$FQDN/mcp" -ForegroundColor White
Write-Host ""
Write-Host "Resource Group : $RESOURCE_GROUP" -ForegroundColor Gray
Write-Host "Container App  : $CONTAINER_APP_NAME" -ForegroundColor Gray
Write-Host "Container Reg  : $ACR_NAME" -ForegroundColor Gray
Write-Host ""

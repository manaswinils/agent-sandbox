# Deployment Configuration — Motivational Quote App

This file is read by the deploy agent (`deploy_agent.py`) to build and deploy
the application. Update this file when infrastructure changes.

## Target

- **Azure Subscription ID:** f5fab68d-1373-4400-a53e-652e75598af0
- **Resource Group:** rg-motivational-quote
- **Region:** East US

## Container Registry

- **ACR Name:** motivationalquoteacr
- **Login Server:** motivationalquoteacr.azurecr.io
- **Image Name:** motivational-quote-app

## Staging Environment

- **App Name:** motivational-quote-app-staging
- **Container Apps Environment:** motivational-quote-env
- **Live URL:** https://motivational-quote-app-staging.delightfulfield-c939fa9a.eastus.azurecontainerapps.io
- **Min Replicas:** 0 (scale to zero when idle)

Deploy command (replace `<TAG>`):
```bash
az containerapp update \
  --name motivational-quote-app-staging \
  --resource-group rg-motivational-quote \
  --image motivationalquoteacr.azurecr.io/motivational-quote-app:<TAG>
```

## Production Environment

- **App Name:** motivational-quote-app
- **Container Apps Environment:** motivational-quote-env
- **Live URL:** https://motivational-quote-app.delightfulfield-c939fa9a.eastus.azurecontainerapps.io
- **Min Replicas:** 1 (always on)

Deploy command (replace `<TAG>`):
```bash
az containerapp update \
  --name motivational-quote-app \
  --resource-group rg-motivational-quote \
  --image motivationalquoteacr.azurecr.io/motivational-quote-app:<TAG>
```

## Build

Build the Docker image and push to ACR using the Azure Container Registry build service
(no local Docker required). Replace `<TAG>` with the deployment tag.

```bash
az acr build \
  --registry motivationalquoteacr \
  --image motivational-quote-app:<TAG> \
  .
```

The same image tag is used for both staging and production — build once, promote to prod.

## Health Checks

- **Staging URL:** https://motivational-quote-app-staging.delightfulfield-c939fa9a.eastus.azurecontainerapps.io
- **Production URL:** https://motivational-quote-app.delightfulfield-c939fa9a.eastus.azurecontainerapps.io
- **Expected:** HTTP 200
- **Retries:** 5 attempts with 10-second delays

## Rollback Procedure

Each deploy run logs the image tag to stdout. To roll back:

1. Note the previous tag from the deploy log (format: `YYYYMMDD-HHMMSS`)
2. Re-run the appropriate deploy command with the previous tag.

## Required Tooling

- Azure CLI (`az`) authenticated via `az login`
- Access to subscription `f5fab68d-1373-4400-a53e-652e75598af0`
- Contributor role on resource group `rg-motivational-quote`

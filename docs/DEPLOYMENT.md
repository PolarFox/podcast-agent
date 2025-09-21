# Deployment Guide

This guide covers preparing Kubernetes resources via Terraform and deploying the CronJob.

## Prerequisites
- Kubernetes cluster and kubeconfig context
- Terraform >= 1.6
- External resources created by platform team:
  - Image pull secret (type kubernetes.io/dockerconfigjson)
  - ConfigMap for app envs (e.g., LOG_LEVEL, PROCESSING_BACKEND)
  - ConfigMap for sources.yaml (key: `sources.yaml`)

## Terraform Variables
- `namespace` (default: `ja-agent`)
- `image` (container image reference)
- `github_token` (secret value for GitHub PAT)
- `image_pull_secret_name` (existing secret name)
- `app_env_configmap_name` (existing ConfigMap name)
- `sources_configmap_name` (existing ConfigMap name)

## Steps
```bash
cd terraform
terraform init
terraform plan \
  -var namespace=ja-agent \
  -var image=ghcr.io/your-org/johtava-arkkitehti-agent:latest \
  -var github_token=ghp_xxx \
  -var image_pull_secret_name=ghcr-pull \
  -var app_env_configmap_name=ja-agent-env \
  -var sources_configmap_name=ja-sources
terraform apply
```

## Runtime Environment
- PROCESSING_BACKEND: `ollama` or `gemini`
- For `ollama`: `OLLAMA_HOST`, `OLLAMA_MODEL`
- For `gemini`: `GOOGLE_API_KEY`, `GEMINI_MODEL`
- GitHub: `GITHUB_TOKEN`, `GITHUB_REPOSITORY`

## Verification
- Check CronJob and Jobs:
```bash
kubectl -n ja-agent get cronjob,job,pod
kubectl -n ja-agent logs -l job-name=<job-name>
```

## Notes
- External Secrets/ConfigMaps are referenced only; they must be provisioned outside this repo.
- Adjust schedule via `var.schedule` in `terraform/cronjob.tf`.

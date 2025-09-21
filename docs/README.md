# Johtava Arkkitehti Podcast Agent

Automates discovery of relevant articles and drafts GitHub issues for potential podcast topics.

## Features
- Fetches from RSS and HTTP sources defined in `config/sources.yaml`
- Normalizes and deduplicates content (hash, fuzzy, optional semantic similarity)
- Classifies into categories: Agile, DevOps, Architecture/Infra, Leadership
- Generates TL;DR summaries and team impact bullets (AI-backed)
- Creates formatted GitHub issues (dry-run supported)
- Optional monthly prioritization analysis for editorial planning

## Quickstart (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.main --dry-run --log-level DEBUG
```

## Configuration
- Sources file: `config/sources.yaml`
  - Supported types: `rss`, `http`
- AI backend (required): set environment variable `PROCESSING_BACKEND` to `ollama` or `gemini`
  - Ollama: `OLLAMA_HOST`, `OLLAMA_MODEL`
  - Gemini: `GOOGLE_API_KEY`, `GEMINI_MODEL`
- GitHub: set `GITHUB_TOKEN` and `GITHUB_REPOSITORY` (owner/repo) in environment for real issue creation

## CLI
```bash
python -m src.main --config config/sources.yaml --dry-run --log-level INFO
python -m src.main --analysis-only --horizon-weeks 4 --log-level INFO
```

## Kubernetes (Terraform)
- See `terraform/` for IaC
  - Variables to provide: `image_pull_secret_name`, `app_env_configmap_name`, `sources_configmap_name`
  - Secret `github-pat` created by Terraform; provide `github_token` variable
- A placeholder manifest is also in `k8s/cronjob.yaml`

## Monthly Analysis
```bash
python -m src.main --analysis-only --horizon-weeks 4
# Output: docs/analysis/situational-YYYY-MM.md
```

## Troubleshooting
- Ensure `PROCESSING_BACKEND` matches your environment and required vars are set
- For Gemini, verify `GOOGLE_API_KEY` and network egress
- For Ollama, verify `OLLAMA_HOST` reachable and model present
- Enable DEBUG logs to diagnose

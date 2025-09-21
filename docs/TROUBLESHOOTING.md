# Troubleshooting

## Common Issues

- No issues created
  - Running with `--dry-run`? Remove to create issues
  - Ensure `GITHUB_TOKEN` and `GITHUB_REPOSITORY` are set

- AI backend errors
  - PROCESSING_BACKEND must be `ollama` or `gemini`
  - Ollama: check `OLLAMA_HOST`, model availability, and network access
  - Gemini: verify `GOOGLE_API_KEY`, model name, egress allowed

- Rate limits
  - GitHub: client will wait on rate limits; increase schedules or set caching
  - Gemini: respect quotas; consider lower frequency or shorter content

- Duplicates not detected
  - Ensure `.cache/seen.json` persists between runs (volume mount in k8s)
  - Tune `title_threshold` or enable semantic similarity (requires sentence-transformers)

## Debugging
- Increase verbosity with `--log-level DEBUG`
- Inspect logs for pipeline timings (classification, summarization, bullets)
- Validate `config/sources.yaml` structure

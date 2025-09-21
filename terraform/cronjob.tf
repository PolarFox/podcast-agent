variable "image" {
  description = "Container image for the agent"
  type        = string
  default     = "ghcr.io/your-org/johtava-arkkitehti-agent:latest"
}

variable "log_level" {
  description = "Log level for the app"
  type        = string
  default     = "INFO"
}

variable "schedule" {
  description = "Cron schedule"
  type        = string
  default     = "0 6 * * *"
}

variable "image_pull_secret_name" {
  description = "Name of existing dockerconfigjson Secret for private registry auth"
  type        = string
  default     = ""
  validation {
    condition     = length(var.image_pull_secret_name) > 0
    error_message = "image_pull_secret_name must be set to reference external registry secret."
  }
}

variable "app_env_configmap_name" {
  description = "Name of existing ConfigMap that holds application env vars"
  type        = string
  default     = ""
  validation {
    condition     = length(var.app_env_configmap_name) > 0
    error_message = "app_env_configmap_name must be set to reference external app env ConfigMap."
  }
}

variable "sources_configmap_name" {
  description = "Name of existing ConfigMap that contains sources.yaml under key 'sources.yaml'"
  type        = string
  default     = ""
  validation {
    condition     = length(var.sources_configmap_name) > 0
    error_message = "sources_configmap_name must be set to reference external sources ConfigMap."
  }
}

resource "kubernetes_cron_job_v1" "agent" {
  metadata {
    name      = "ja-agent"
    namespace = kubernetes_namespace.ns.metadata[0].name
    labels = {
      "app.kubernetes.io/name" = "ja-agent"
    }
  }
  spec {
    schedule                   = var.schedule
    concurrency_policy         = "Forbid"
    successful_jobs_history_limit = 1
    failed_jobs_history_limit     = 3

    job_template {
      metadata {}
      spec {
        template {
          metadata {
            labels = {
              "app.kubernetes.io/name" = "ja-agent"
            }
          }
          spec {
            service_account_name = kubernetes_service_account.agent.metadata[0].name
            restart_policy       = "OnFailure"
            image_pull_secrets {
              name = var.image_pull_secret_name
            }

            container {
              name  = "agent"
              image = var.image

              args = ["python", "-m", "src.main", "--config", "/app/config/sources.yaml"]

              env {
                name  = "LOG_LEVEL"
                value = var.log_level
              }
              # Example of mapping envs from ConfigMap. Add/rename keys as needed.
              env {
                name = "PROCESSING_BACKEND"
                value_from {
                  config_map_key_ref {
                    name = var.app_env_configmap_name
                    key  = "PROCESSING_BACKEND"
                  }
                }
              }
              env {
                name = "GITHUB_TOKEN"
                value_from {
                  secret_key_ref {
                    name = kubernetes_secret.github_pat.metadata[0].name
                    key  = "GITHUB_TOKEN"
                  }
                }
              }

              resources {
                limits = {
                  cpu    = "500m"
                  memory = "1Gi"
                }
                requests = {
                  cpu    = "200m"
                  memory = "512Mi"
                }
              }

              volume_mount {
                name       = "config"
                mount_path = "/app/config"
                read_only  = true
              }
            }

            volume {
              name = "config"
              config_map {
                name = var.sources_configmap_name
              }
            }
          }
        }
      }
    }
  }
}

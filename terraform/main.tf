provider "kubernetes" {}
provider "helm" {}

variable "namespace" {
  description = "Namespace for the podcast agent"
  type        = string
  default     = "ja-agent"
}

variable "github_token" {
  description = "GitHub Personal Access Token (PAT)"
  type        = string
  sensitive   = true
}

variable "repository" {
  description = "GitHub repository in owner/repo format"
  type        = string
}

resource "kubernetes_namespace" "ns" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/name" = "ja-agent"
    }
  }
}

resource "kubernetes_secret" "github_pat" {
  metadata {
    name      = "github-pat"
    namespace = kubernetes_namespace.ns.metadata[0].name
  }
  data = {
    GITHUB_TOKEN = var.github_token
  }
  type = "Opaque"
}

resource "kubernetes_service_account" "agent" {
  metadata {
    name      = "ja-agent"
    namespace = kubernetes_namespace.ns.metadata[0].name
  }
}

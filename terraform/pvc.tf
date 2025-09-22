variable "archive_storage_size" {
  description = "Requested storage size for archive PVC"
  type        = string
  default     = "1Gi"
}

variable "archive_storage_class" {
  description = "StorageClass name for archive PVC (null to omit)"
  type        = string
  default     = null
}

resource "kubernetes_persistent_volume_claim" "archive" {
  metadata {
    name      = "ja-archive"
    namespace = kubernetes_namespace.ns.metadata[0].name
    labels = {
      "app.kubernetes.io/name" = "ja-agent"
    }
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = var.archive_storage_size
      }
    }
    storage_class_name = var.archive_storage_class
  }
}

# terraform/gke/main.tf

terraform {
  backend "gcs" {
    bucket = "vllm-sara-tf-state"
    prefix = "gke/terraform"
  }
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "vllm_cluster" {
  name                     = "vllm-cluster"
  location                 = var.region
  deletion_protection      = false
  remove_default_node_pool = true
  initial_node_count       = 1

  # Critical: Override default disk size to stay under quota
  node_config {
    disk_size_gb = 10
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

# Your main node pool (1 node per zone if regional)
resource "google_container_node_pool" "default_pool" {
  name       = "default-pool"
  location   = var.region
  cluster    = google_container_cluster.vllm_cluster.name
  node_count = 1

  node_config {
    machine_type = "n1-standard-4"
    disk_size_gb = 20
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-east1"
}

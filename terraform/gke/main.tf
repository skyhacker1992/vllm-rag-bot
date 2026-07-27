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
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_client_config" "default" {}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.vllm_cluster.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.vllm_cluster.master_auth[0].cluster_ca_certificate)
  }
}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.vllm_cluster.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.vllm_cluster.master_auth[0].cluster_ca_certificate)
}

resource "google_container_cluster" "vllm_cluster" {
  name                     = "vllm-cluster"
  location                 = var.region
  deletion_protection      = false
  remove_default_node_pool = true
  initial_node_count       = 1

  # Enable Workload Identity (needed for the auth we set up)
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

# Node pool optimized for VLLM (you can adjust machine type later)
resource "google_container_node_pool" "default_pool" {
  name       = "gpu-pool"
  location   = var.region
  cluster    = google_container_cluster.vllm_cluster.name
  node_count = 1

  node_config {
    machine_type = "n1-standard-4" # Change to g2-standard or a2 for real GPUs later
    disk_size_gb = 50

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}

# -----------------------------
# Argo CD
# -----------------------------

resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
  }

  depends_on = [
    google_container_node_pool.default_pool
  ]
}

resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = "7.7.10"
  namespace  = kubernetes_namespace.argocd.metadata[0].name

  values = [
    <<-EOT
    server:
      service:
        type: LoadBalancer
    configs:
      params:
        server.insecure: true
    EOT
  ]

  depends_on = [
    kubernetes_namespace.argocd
  ]
}

# Variables
variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-east1"
}

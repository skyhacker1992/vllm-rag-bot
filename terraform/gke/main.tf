# GKE GPU landing zone — NAOFPA LLM platform
terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" { type = string }
variable "region"     { type = string  default = "us-central1" }
variable "zone"       { type = string  default = "us-central1-a" }

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "naofpa_llm" {
  name     = "naofpa-llm-gke"
  location = var.zone

  # Governance: disable legacy ABAC, use workload identity
  enable_legacy_abac = false
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  initial_node_count = 1
  remove_default_node_pool = true

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  ip_allocation_policy {}
}

resource "google_container_node_pool" "gpu_pool" {
  name       = "gpu-pool"
  location   = var.zone
  cluster    = google_container_cluster.naofpa_llm.name
  node_count = 1

  node_config {
    machine_type = "g2-standard-8"  # L4 GPU class
    guest_accelerator {
      type  = "nvidia-l4"
      count = 1
    }
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    labels = { workload = "llm-inference" }
    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }
}

resource "google_compute_network" "vpc" {
  name                    = "naofpa-llm-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "naofpa-llm-subnet"
  ip_cidr_range = "10.10.0.0/20"
  region        = var.region
  network       = google_compute_network.vpc.id
}
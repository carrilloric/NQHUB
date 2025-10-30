# Compute Module - VM Instance with GPU

# TODO: Define VM instance based on selected cloud provider

# Example for GCP:
# resource "google_compute_instance" "nqhub_vm" {
#   name         = "${var.project_name}-${var.environment}"
#   machine_type = var.machine_type
#   zone         = var.zone
#
#   boot_disk {
#     initialize_params {
#       image = "ubuntu-os-cloud/ubuntu-2204-lts"
#       size  = var.disk_size_gb
#     }
#   }
#
#   guest_accelerator {
#     type  = var.gpu_type
#     count = 1
#   }
#
#   scheduling {
#     on_host_maintenance = "TERMINATE"
#     automatic_restart   = false
#   }
#
#   network_interface {
#     network = var.network_name
#     access_config {
#       # Ephemeral IP
#     }
#   }
#
#   metadata = {
#     ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
#   }
#
#   tags = ["nqhub", var.environment]
# }

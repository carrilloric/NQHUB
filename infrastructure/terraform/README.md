# NQHUB Terraform Configuration

Infrastructure as Code for NQHUB deployment.

## Prerequisites

- Terraform 1.6+
- Cloud provider CLI configured (gcloud, aws cli, or az cli)
- SSH key pair generated

## Structure

```
terraform/
├── main.tf              # Main configuration
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── modules/
│   ├── compute/         # VM instances
│   ├── networking/      # VPC, firewall rules
│   └── storage/         # Persistent disks
└── environments/
    ├── dev/
    └── production/
```

## Usage

### 1. Select Cloud Provider

Edit `main.tf` and uncomment the appropriate provider configuration.

### 2. Configure Variables

Create `terraform.tfvars`:
```hcl
environment   = "production"
project_name  = "nqhub"
machine_type  = "n1-standard-4"
gpu_type      = "nvidia-tesla-t4"
disk_size_gb  = 100
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Plan

```bash
terraform plan
```

### 5. Apply

```bash
terraform apply
```

### 6. Outputs

```bash
terraform output
```

## Modules

### compute
Creates VM instance with GPU support.

### networking
Creates VPC, subnets, and firewall rules.

### storage
Creates persistent disks for data.

## Environments

### dev
Development environment with smaller resources.

### production
Production environment with full resources.

## Security

- Never commit `terraform.tfvars` with sensitive data
- Use environment variables for secrets
- Restrict firewall rules to known IPs

## Cleanup

```bash
terraform destroy
```

## TODO

- [ ] Select cloud provider
- [ ] Implement compute module
- [ ] Implement networking module
- [ ] Implement storage module
- [ ] Add backend configuration (S3/GCS for state)
- [ ] Add environment-specific configurations

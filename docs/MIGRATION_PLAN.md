# NQHUB - Migration Plan to VM

**Status**: Planning Phase
**Last Updated**: 2025-10-29
**Current Environment**: WSL 2 (Development)

---

## Current State

### Development Environment
- **Platform**: WSL 2 (Ubuntu 22.04)
- **Exposure**: ngrok (temporary)
- **Services**: Docker Compose (local)
- **GPU**: Host GPU (if available)

### Services Running
- PostgreSQL + TimescaleDB
- Redis
- Neo4j
- Mailpit (SMTP)
- Backend (FastAPI)
- Frontend (React)
- Monitoring (Grafana, Prometheus, Loki)

---

## Target Architecture

### Production Environment
- **Platform**: Cloud VM with GPU
- **Exposure**: Public IP + Domain
- **Services**: Containerized (Docker)
- **SSL**: Let's Encrypt
- **Backups**: Automated daily
- **CI/CD**: GitHub Actions (future)

---

## Cloud Provider Options

### Evaluation Criteria
- GPU availability (CUDA support)
- Cost per hour/month
- Latency for target users
- Ease of setup
- Support quality

### Provider Comparison

| Provider | Instance Type | GPU | vCPU | RAM | Storage | Cost/Hour | Notes |
|----------|--------------|-----|------|-----|---------|-----------|-------|
| **AWS** | g4dn.xlarge | T4 | 4 | 16GB | 125GB | $0.526 | Mature, expensive |
| **GCP** | n1-standard-4 + T4 | T4 | 4 | 15GB | Custom | $0.35-0.45 | Good pricing |
| **Azure** | NC6s_v3 | V100 | 6 | 112GB | 736GB | $0.90 | Powerful, pricey |
| **Paperspace** | P4000 | P4000 | 8 | 30GB | 250GB | $0.51 | Good for ML |
| **RunPod** | RTX 3090 | 3090 | - | - | - | $0.34 | Cheapest GPU |

**Recommendation**: TBD based on budget and requirements

---

## Migration Phases

### Phase 1: Pre-Migration Preparation

**Timeline**: Before migration

#### Tasks
- [ ] Export all data from development databases
  - [ ] PostgreSQL database dump
  - [ ] Neo4j graph export
  - [ ] Redis data backup (if needed)
- [ ] Document all environment variables
- [ ] Create backup of all configurations
- [ ] Verify Docker setup works completely
- [ ] Test backup/restore procedures locally
- [ ] Document all external dependencies
- [ ] Create rollback plan

#### Commands
```bash
# PostgreSQL backup
docker exec nqhub_postgres pg_dump -U nqhub nqhub > backup_$(date +%Y%m%d).sql

# Neo4j export
docker exec nqhub_neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j_$(date +%Y%m%d).dump

# Environment variables
./scripts/export_env.sh > env_backup.txt
```

---

### Phase 2: Infrastructure Provisioning (Terraform)

**Timeline**: Day 1-2

#### Tasks
- [ ] Select cloud provider
- [ ] Create Terraform configuration
- [ ] Define network architecture (VPC, subnets, security groups)
- [ ] Provision VM instance with GPU
- [ ] Configure storage volumes
- [ ] Setup DNS records
- [ ] Apply Terraform plan

#### Terraform Structure
```
infrastructure/terraform/
├── main.tf              # Provider and main resources
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── modules/
│   ├── compute/         # VM instance
│   ├── networking/      # VPC, firewall
│   └── storage/         # Persistent disks
└── environments/
    └── production/
        ├── main.tf
        └── terraform.tfvars
```

#### Key Resources
```hcl
# Example VM with GPU
resource "google_compute_instance" "nqhub_vm" {
  name         = "nqhub-production"
  machine_type = "n1-standard-4"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-2204-lts"
      size  = 100
    }
  }

  guest_accelerator {
    type  = "nvidia-tesla-t4"
    count = 1
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
  }
}
```

---

### Phase 3: Server Configuration (Ansible)

**Timeline**: Day 2-3

#### Tasks
- [ ] Install Docker and Docker Compose
- [ ] Install NVIDIA drivers and CUDA
- [ ] Configure firewall (UFW)
- [ ] Setup SSL certificates (Let's Encrypt)
- [ ] Configure monitoring agents
- [ ] Setup log rotation
- [ ] Configure automated backups
- [ ] Harden SSH access

#### Ansible Playbooks

**setup.yml** - Initial server setup
```yaml
---
- hosts: production
  become: yes
  roles:
    - docker
    - nvidia
    - security
    - monitoring
```

**deploy.yml** - Deploy application
```yaml
---
- hosts: production
  become: yes
  tasks:
    - name: Copy application code
    - name: Copy environment files
    - name: Start Docker Compose
    - name: Verify services are running
```

---

### Phase 4: Application Deployment

**Timeline**: Day 3-4

#### Tasks
- [ ] Copy application code to VM
- [ ] Configure production environment variables
- [ ] Restore database backups
- [ ] Start Docker Compose services
- [ ] Verify all services are healthy
- [ ] Test database connections
- [ ] Test API endpoints
- [ ] Configure domain DNS
- [ ] Setup SSL certificates
- [ ] Test HTTPS access

#### Deployment Commands
```bash
# From local machine
./scripts/deploy.sh production

# On VM
cd /opt/nqhub
docker-compose -f docker/docker-compose.yml up -d
docker-compose -f docker/docker-compose.monitoring.yml up -d
```

#### Health Checks
```bash
# Check all services
docker ps
docker-compose logs -f

# Test endpoints
curl https://api.nqhub.com/api/health
curl https://nqhub.com

# Check monitoring
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3001/api/health  # Grafana
```

---

### Phase 5: Post-Migration

**Timeline**: Day 4-7

#### Tasks
- [ ] Setup automated backups (daily)
- [ ] Configure monitoring alerts
- [ ] Test failover procedures
- [ ] Performance tuning
- [ ] Security audit
- [ ] Update documentation
- [ ] Train team on production access
- [ ] Setup CI/CD pipeline (future)

#### Automated Backups
```bash
# Crontab on VM
0 2 * * * /opt/nqhub/scripts/backup.sh
```

#### Monitoring Alerts
- API response time > 2s
- Error rate > 5%
- Disk usage > 85%
- Memory usage > 90%
- GPU utilization issues
- Database connection failures

---

## Rollback Plan

### If Migration Fails

1. **Keep development environment running** until migration is verified
2. **Have database backups** available for restore
3. **Document all issues** encountered
4. **Revert DNS** if needed
5. **Destroy cloud resources** to avoid costs

### Rollback Steps
```bash
# Revert DNS to ngrok
# Stop cloud VM
terraform destroy -auto-approve

# Restore local development
./scripts/dev_setup.sh
```

---

## Security Considerations

### Network Security
- [ ] Firewall configured (only necessary ports open)
- [ ] SSH key-based authentication only
- [ ] Fail2ban installed
- [ ] Regular security updates

### Application Security
- [ ] Environment variables secured
- [ ] Database passwords strong and unique
- [ ] JWT secrets generated securely
- [ ] API rate limiting enabled
- [ ] CORS properly configured

### SSL/TLS
- [ ] Let's Encrypt certificates
- [ ] Auto-renewal configured
- [ ] HTTPS redirect enabled
- [ ] HSTS headers configured

---

## Cost Estimation

### Monthly Costs (Estimated)

| Item | Provider | Estimated Cost |
|------|----------|---------------|
| VM with GPU | TBD | $200-400/month |
| Storage (500GB) | TBD | $20-40/month |
| Bandwidth (1TB) | TBD | $20-50/month |
| Backups | TBD | $10-20/month |
| **Total** | | **$250-510/month** |

### Cost Optimization
- Use spot/preemptible instances when possible
- Scale down during off-hours
- Optimize storage usage
- Use CDN for static assets (future)

---

## Checklist

### Pre-Migration
- [ ] All code committed and pushed
- [ ] Database backups created
- [ ] Environment variables documented
- [ ] Terraform configuration ready
- [ ] Ansible playbooks ready
- [ ] Rollback plan reviewed

### Migration
- [ ] Cloud provider account created
- [ ] Payment method configured
- [ ] Terraform plan reviewed and applied
- [ ] VM provisioned successfully
- [ ] Ansible configuration applied
- [ ] Application deployed
- [ ] Services health checks passing
- [ ] DNS configured
- [ ] SSL certificates working

### Post-Migration
- [ ] Monitoring dashboards configured
- [ ] Alerts configured and tested
- [ ] Automated backups working
- [ ] Documentation updated
- [ ] Team trained
- [ ] Performance baseline established
- [ ] Security audit completed

---

## Update Log

| Date | Update | Author |
|------|--------|--------|
| 2025-10-29 | Initial migration plan created | System |

---

## Next Steps

1. **Select cloud provider** based on requirements and budget
2. **Create Terraform configuration** for chosen provider
3. **Test Terraform locally** with test environment
4. **Create Ansible playbooks** for server configuration
5. **Test deployment process** in staging environment
6. **Schedule migration window**
7. **Execute migration**

---

**Note**: This is a living document. Update it as the migration progresses and new information becomes available.

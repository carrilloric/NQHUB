# NQHUB Ansible Configuration

Ansible playbooks for NQHUB server configuration and deployment.

## Prerequisites

- Ansible 2.16+
- SSH access to target servers
- sudo/root access on target servers

## Installation

```bash
pip install ansible
```

## Structure

```
ansible/
├── playbooks/
│   ├── setup.yml       # Initial server setup
│   ├── deploy.yml      # Deploy application
│   ├── update.yml      # Update application
│   └── backup.yml      # Backup procedures
├── roles/
│   ├── docker/         # Install Docker
│   ├── nvidia/         # Install NVIDIA drivers
│   ├── monitoring/     # Setup monitoring
│   └── nqhub/          # NQHUB-specific config
└── inventory/
    ├── dev.ini
    └── production.ini
```

## Usage

### 1. Configure Inventory

Edit `inventory/production.ini` with your server details:
```ini
[production]
nqhub-prod ansible_host=1.2.3.4 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/key.pem
```

### 2. Test Connection

```bash
ansible production -i inventory/production.ini -m ping
```

### 3. Initial Server Setup

```bash
ansible-playbook -i inventory/production.ini playbooks/setup.yml
```

This will:
- Install Docker and Docker Compose
- Install NVIDIA drivers and CUDA
- Configure firewall
- Setup monitoring agents
- Create NQHUB user

### 4. Deploy Application

```bash
ansible-playbook -i inventory/production.ini playbooks/deploy.yml
```

This will:
- Copy application code
- Copy environment files
- Start Docker Compose services
- Verify services are healthy

### 5. Update Application

```bash
ansible-playbook -i inventory/production.ini playbooks/update.yml
```

## Roles

### docker
Installs Docker, Docker Compose, and configures Docker daemon.

### nvidia
Installs NVIDIA drivers, CUDA toolkit, and nvidia-docker.

### monitoring
Sets up Prometheus node exporter and log forwarding.

### nqhub
NQHUB-specific configurations and optimizations.

## Variables

Common variables can be defined in `group_vars/` or passed via `-e`:
```bash
ansible-playbook playbooks/deploy.yml -e "version=v1.2.3"
```

## Security

- Never commit `inventory/*.ini` with production IPs
- Never commit SSH keys
- Use Ansible Vault for sensitive data:
  ```bash
  ansible-vault create secrets.yml
  ```

## Troubleshooting

### Check logs
```bash
ansible production -i inventory/production.ini -a "docker-compose logs -f"
```

### Run specific role
```bash
ansible-playbook playbooks/setup.yml --tags docker
```

### Dry run
```bash
ansible-playbook playbooks/deploy.yml --check
```

## TODO

- [ ] Implement update.yml playbook
- [ ] Implement backup.yml playbook
- [ ] Add SSL certificate management role
- [ ] Add database backup automation
- [ ] Add log rotation configuration

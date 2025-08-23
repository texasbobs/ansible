Ansible — Homelab automation (Proxmox + k3s + Flux)

Spin up K3s nodes on Proxmox, configure networking/hostnames, set a friendly MOTD, cleanly delete VMs, and bootstrap Flux GitOps. Batteries included; dragons optional. 🐉

What this repo does

Clone VMs from a Proxmox template and tag them (e.g., ubuntu;k3s)

Bring VMs online one at a time and set static netplan + hostname

Stamp a custom login banner (MOTD) with the install date

Prep K3s nodes for Longhorn (iSCSI/NFS), then bootstrap Flux

Delete VMs safely (stop first, then remove)

Opinionated defaults: Proxmox API token auth (not passwords), YAML everywhere, and bob as the SSH user.

Repo layout (high level)
ansible/
├─ ansible.cfg                     # points to inventory, sets defaults
├─ inv                             # your inventory (example below)
├─ group_vars/
│  └─ all/
│     └─ vault.yaml                # secrets (encrypted with ansible-vault)
├─ roles/
│  ├─ update_netplan/              # write netplan, set hostname, reboot
│  ├─ motd_custom/                 # banner with “Last updated: YYYY-MM-DD”
│  └─ pve_delete_vms/              # stop & delete VMs if they exist
├─ create-k3s-vms.yaml             # clone & start VMs from template
├─ update-netplan.yaml             # power-on → SSH via .253 → set static IP/hostname
├─ set-motd.yaml                   # one-time MOTD banner install
├─ delete-vms.yaml                 # remove one or many VMs
└─ prep-and-bootstrap-flux.yaml    # Longhorn prerequisites + Flux bootstrap

Requirements
Control host

Ansible 8+ (or latest)

Collections & libs:

ansible-galaxy collection install community.general
python3 -m pip install --user proxmoxer requests


SSH key loaded and allowed on the VMs for user bob

Proxmox

A template VM (e.g., u24) with:

qemu-guest-agent installed & enabled

user bob with your ~/.ssh/id_ed25519.pub in ~bob/.ssh/authorized_keys

A token (preferably with privilege separation) for API auth:

User (realm included): ansible@pam

Token name (not user!token): e.g., ansible

Permissions (minimum to clone to local-lvm on node pve2):

/vms/112 → PVEVMAdmin (source template)

/nodes/pve2 → PVEVMAdmin (target node)

/storage/local-lvm → PVEAdmin (allocate space)

Storage IDs referenced in playbooks must exist on the target node (e.g., local-lvm)

K3s nodes (for Longhorn)

open-iscsi and nfs-common installed & iscsid enabled (playbook included)

Secrets (Ansible Vault)

Create group_vars/all/vault.yaml and encrypt it:

# Proxmox API (token auth)
proxmox_host_ip: 192.168.2.112
proxmox_user: "ansible@pam"
proxmox_token_id: "ansible"               # token NAME only
proxmox_token_secret: "YOUR_LONG_SECRET"

# Optional: sudo password if bob is not passwordless sudo
# ansible_become_password: "..."

# Flux bootstrap
# (personal access token with 'repo' scope for your account/org)
github_token: "ghp_xxx..."


Encrypt it:

ansible-vault create group_vars/all/vault.yaml


Pro tip: set a vault passfile in ~/.ansible.cfg and never commit it.

Inventory

Example inv (INI):

[newvms]
k3s-01 ansible_host=192.168.2.253 vmid=241 target_ip=192.168.2.241
k3s-02 ansible_host=192.168.2.253 vmid=242 target_ip=192.168.2.242
# …or just use the dynamic “add_host” in the playbooks

[k3s_nodes]
192.168.2.241
192.168.2.242
# … etc

[all:vars]
ansible_user=bob
ansible_ssh_private_key_file=/home/bob/.ssh/id_ed25519


ansible.cfg already points Ansible at this inventory and sets sane defaults.

Usage
1) Clone & start VMs (from Proxmox template VMID 112)
ansible-playbook create-k3s-vms.yaml


Clones from 112 (or edit to use your template’s name/ID)

Tags VMs with ubuntu;k3s

Target node: pve2, storage: local-lvm

2) Set network & hostname (one at a time)
ansible-playbook update-netplan.yaml


What it does:

Powers on one VM at a time

SSHes to 192.168.2.253 (your bootstrap IP)

Replaces /etc/netplan/01-netcfg.yaml:

IP becomes 192.168.2.<VMID> (e.g., .241)

GW 192.168.2.1, DNS 192.168.2.2 (tweak in role defaults)

Sets hostname to the VM’s name

Reboots and waits for SSH on the new static IP

Make sure only one VM is using .253 at a time—this play handles serial execution to avoid collisions.

3) Stamp a friendly MOTD (one time)
ansible-playbook set-motd.yaml


Writes /etc/update-motd.d/00-custom (executable)

Banner shows Welcome to <hostname> and Last updated: YYYY-MM-DD

Date is fixed at deploy time; hostname reflects the current host each login

4) Prep nodes & bootstrap Flux
ansible-playbook prep-and-bootstrap-flux.yaml \
  -e flux_repo_owner=texasbobs \
  -e flux_repo_name=homelab-gitops \
  -e flux_repo_branch=main \
  -e flux_path=clusters/homelab \
  -e flux_personal=true


Installs open-iscsi + nfs-common and enables iscsid on all k3s_nodes

Verifies kubectl get nodes works locally

Bootstraps Flux to your GitHub repo via the token in vault.yaml

5) Delete VMs cleanly
ansible-playbook delete-vms.yaml


Stops VMs if running, deletes if present (by id or name)

Skips quietly if a VM doesn’t exist

Role quick references
roles/update_netplan

Vars (override via group_vars or extra-vars):

netplan_interface: ens18
netplan_prefix: 24
netplan_gateway: 192.168.2.1
netplan_dns: ["192.168.2.2"]
netplan_path: /etc/netplan/01-netcfg.yaml


Expects host vars: target_ip, new_hostname (the playbooks set these).

roles/motd_custom

One-time script at /etc/update-motd.d/00-custom

Stamps today’s date at deploy; safe to re-run if you want to update it

roles/pve_delete_vms

Uses community.general.proxmox_kvm

Requires proxmox_* vars from vault.yaml

Idempotent: only acts on VMs that exist

Gotchas & tips

Token formatting: pass api_user: "ansible@pam" and api_token_id: "ansible" (token name only). Do not pass user!token as api_token_id; the module builds that.

Permissions: a 403 like Datastore.AllocateSpace means your token lacks rights on the target storage. Grant PVEAdmin on /storage/<store> for the token (or the user if not using privilege separation).

QEMU Guest Agent: required for IP discovery (if you use that pattern). Install on the template.

SSH: defaults to bob. Ensure your key is in ~bob/.ssh/authorized_keys on the template.

All YAML, no YML: filenames and examples stick to .yaml by design.

Contributing / TODO

Helm/Flux manifests for Longhorn + kube-prometheus-stack

Optional DNS/LB (e.g., MetalLB + external-dns) via Flux

Make storage/node selectors configurable via group_vars

PRs and issues welcome. If something explodes, it was obviously the mimic. 🧪

License

MIT

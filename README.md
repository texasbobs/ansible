## Create K3s Cluster

Step 1: Run the create-k3s-vms.yaml playbook to get the VMs created
ansible-playbook create-cluster/create-k3s-vms.yaml

Step 2: Run update-vms.yaml  to set the mem and cpu for the nodes
ansible-playbook create-cluster/update-cms.yaml -i inv/k3s.yaml

Step 3: Run the update-netplan.yaml to start the VMs and set the netplan config and host names
ansible-playbook create-cluster/update-netplan.yaml

Step 4: Run set-motd.yaml to update MotD
ansible-playbook create-cluster/set-motd.yaml -i inv/k3s.yaml

Step 5: cd to the k3s dir

Step 6: Install k3s on all nodes
ansible-playbook playbooks/site.yml -i ~/github/ansible/inv/k3s.yaml

step 7: prep vms
ansible-playbook create-cluster/prep-vms.yaml -i inv/k3s.yaml

step 8: create-longhorn-disks
ansible-playbook -i inv/k3s.yaml  create-cluster/add-longhorn-disk.yaml

step 9: bootstrap flux
ansible-playbook -i inv/k3s.yaml create-cluster/bootstrap-flux.yaml

├── create-cluster
│   ├── add-longhorn-disk.yaml
│   ├── bootstrap-flux.yaml
│   ├── create-k3s-vms.yaml
│   ├── delete-vms.yaml
│   ├── deploy-k3s-registry.yaml
│   ├── prep-vms.yaml
│   ├── register-disks-to-longhorn.yaml
│   ├── set-motd.yaml
│   ├── update-netplan.yaml
│   └── update-vms.yaml
├── envs.yaml-old
├── group_vars
│   └── all
│       └── vault.yaml
├── inv
│   ├── inventory.proxmox.yaml
│   ├── k3s.yaml
│   └── proxmox_dynamic.py
├── patch-ubuntu.yaml
├── README.md
├── roles
│   ├── longhorn_disk
│   │   ├── defaults
│   │   │   └── main.yaml
│   │   ├── handlers
│   │   ├── handlers.main.yaml
│   │   └── tasks
│   │       └── main.yaml
│   ├── motd_custom
│   │   ├── tasks
│   │   │   └── main.yaml
│   │   └── templates
│   │       └── 00-custom.j2
│   ├── patch_ubuntu
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── files
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── README.md
│   │   ├── tasks
│   │   │   └── main.yml
│   │   ├── templates
│   │   ├── tests
│   │   │   ├── inventory
│   │   │   └── test.yml
│   │   └── vars
│   │       └── main.yml
│   ├── proxmox
│   │   ├── defaults
│   │   │   └── main.yml
│   │   └── tasks
│   │       └── main.yml
│   ├── proxmox-guest
│   │   ├── defaults
│   │   │   └── main.yml
│   │   └── tasks
│   │       └── main.yml
│   ├── pve_delete_vms
│   │   ├── defaults
│   │   │   └── main.yaml
│   │   └── tasks
│   │       └── main.yaml
│   └── update_netplan
│       ├── defaults
│       │   └── main.yaml
│       ├── tasks
│       │   └── main.yml
│       └── templates
│           └── 01-netcfg.yaml.j2
└── todo.txt

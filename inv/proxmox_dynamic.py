#!/usr/bin/env python3
import os, json, ssl
from urllib import request, parse, error

# ─── CONFIG ───
PVE_HOST = os.environ.get('PVE_HOST', 'https://192.168.2.112:8006')
API_BASE = f"{PVE_HOST}/api2/json"
USER     = os.environ.get('PVE_USER', 'ansible@pam')
PASS     = os.environ.get('PVE_PASS', 'Kb0ygd100')
# ─────────────

# disable SSL verification for self-signed certs
ssl._create_default_https_context = ssl._create_unverified_context

def get_ticket():
    data = parse.urlencode({'username': USER, 'password': PASS}).encode()
    req  = request.Request(
        f"{PVE_HOST}/api2/json/access/ticket",
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    with request.urlopen(req) as resp:
        return json.load(resp)['data']['ticket']

def api_get(path, ticket):
    url = f"{API_BASE}{path}"
    req = request.Request(url, headers={'Cookie': f'PVEAuthCookie={ticket}'})
    with request.urlopen(req) as resp:
        return json.load(resp)['data']

def main():
    ticket = get_ticket()
    inv = {'_meta': {'hostvars': {}}, 'proxmox_all_running': {'hosts': []}}

    # 1) list all VMs
    for vm in api_get('/cluster/resources?type=vm', ticket):
        if vm.get('status') != 'running': 
            continue
        if 'ubuntu' not in vm.get('tags','').split(';'):
            continue

        node = vm['node']
        vmid = vm['vmid']
        name = vm['name']

        # 2) fetch QEMU-agent interfaces (wrapped under "result" vs. direct list)
        try:
            data = api_get(f"/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces", ticket)
            nets = data.get('result', []) if isinstance(data, dict) else data
        except error.HTTPError:
            continue

        # 3) find ens18 and extract the first IP
        ip = None
        for iface in nets:
            if iface.get('name') == 'ens18':
                addrs = iface.get('ip-addresses', [])
                if addrs:
                    ip = addrs[0].get('ip-address')
                break
        if not ip:
            continue

        # 4) record host
        inv['_meta']['hostvars'][name] = {
            'ansible_host': ip,
            'ansible_user': 'bob'
        }
        inv['proxmox_all_running']['hosts'].append(name)

    print(json.dumps(inv, indent=2))

if __name__ == '__main__':
    main()

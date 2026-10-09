.PHONY: fleet-inventory firewall-review

fleet-inventory:
	sops exec-env scripts/secrets.enc.env "python3 scripts/generate-fleet-inventory.py"

# Print the would-drop sets of the host firewall on all docker_hosts (read-only).
firewall-review:
	cd ansible && ansible docker_hosts:firewall_only_hosts --become -m ansible.builtin.shell \
		-a "/usr/sbin/nft list set inet homelab_fw would_drop_v4; /usr/sbin/nft list set inet homelab_fw would_drop_v6"

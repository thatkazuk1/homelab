.PHONY: fleet-inventory

fleet-inventory:
	sops exec-env scripts/secrets.enc.env "python3 scripts/generate-fleet-inventory.py"

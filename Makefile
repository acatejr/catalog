SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: build shell chown dev_server dcu dcs fmt bash migrate

dcu:
	docker compose -f compose.yml up -d --build

dcd:
	docker compose -f compose.yml down

dcs:
	docker compose -f compose.yml stop

# shell:
# 	docker exec -it catalog bash

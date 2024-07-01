SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

# # .PHONY: dcu dcd dcs shell chown build collect_static dcr serve
.PHONY: collect_static

collect_static:
	docker exec -it catalog ./manage.py collectstatic --no-input

# serve:
#     pyhon manage.py runserver

# dcu:
# 	docker compose -f .docker/compose.yml up -d --build

# dcd:
# 	docker compose -f .docker/compose.yml down

# dcs:
# 	docker compose -f .docker/compose.yml stop

# dcr:
# 	docker compose -f .docker/compose.yml restart

# shell:
# 	docker exec -it mmp bash

# chown:
# 	sudo chown $(USER):$(USER) -R .

# build:
# 	git pull
# 	docker compose -f .docker/compose.prd.yml up -d --build
# 	docker exec -it mmp ./manage.py migrate
# 	docker exec -it mmp ./manage.py collectstatic --noinput
# 	docker compose -f .docker/compose.prd.yml restart

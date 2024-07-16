SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: collect_static dcu dcd dcd serve shell

collect_static:
	docker exec -it catalog ./manage.py collectstatic --no-input

dcu:
	docker compose -f .docker/compose.yml up -d --build

dcs:
	docker compose -f .docker/compose.yml stop

serve:
	docker exec -it catalog python manage.py runserver 0.0.0.0:8000

shell:
	docker exec -it catalog bash

dcd:
	docker compose -f .docker/compose.yml down


# dcr:
# 	docker compose -f .docker/compose.yml restart

# chown:
# 	sudo chown $(USER):$(USER) -R .

# build:
# 	git pull
# 	docker compose -f .docker/compose.prd.yml up -d --build
# 	docker exec -it catalog ./manage.py migrate
# 	docker exec -it catalog ./manage.py collectstatic --noinput
# 	docker compose -f .docker/compose.prd.yml restart

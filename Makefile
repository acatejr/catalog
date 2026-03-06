.PHONY: gh-deploy build-chromadb test-app test-qstn

gh-deploy:
	uv run mkdocs gh-deploy

build-chromadb:
	uv run catalog build-fs-chromadb

test-app:
	uv run pytest -vs

init:
	git submodule init
extract:
	@echo "pull chain-registry"
	git submodule update --remote
	python3 asset_data.py extract
export:
	python3 asset_data.py export
update: extract export

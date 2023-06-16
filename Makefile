extract:
	@echo "pull chain-registry"
	git submodule init
	git submodule update --remote
	python3 asset_data.py extract
export:
	python3 asset_data.py export
update: extract export

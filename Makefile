extract:
	@echo "pull chain-registry"
	git submodule init
	git submodule update --remote
	@echo "extract data"
	python3 asset_data.py --extract=True --export=False
export:
	@echo "export data"
	python3 asset_data.py --extract=False --export=True
update: extract export
build_code:
	@echo "build code"
	python3 contract_deploy.py --build_code=True
store_code:
	@echo "store code"
	python3 contract_deploy.py --chain_name=$(chain_name) --store_code=True
init_contract:
	@echo "instantiate contract"
	python3 contract_deploy.py --chain_name=$(chain_name) --init_contract=True
deploy_contract:
	@echo "build a code, store a code and instantiate a contract"
	python3 contract_deploy.py --chain_name=$(chain_name) --build_code=True --store_code=True --init_contract=True

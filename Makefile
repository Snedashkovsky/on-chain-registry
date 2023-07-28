default: help

all : help extract export run_notebook update build_code store_code init_contract deploy_contract
.PHONY : all

help:  # show help for each of the makefile recipes
	@grep -E '^[a-zA-Z0-9 -_]+:.*#'  Makefile | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

extract:  # extract metadata from node apis
	@echo "pull chain-registry"
	git submodule init
	git submodule update --remote
	@echo "extract data"
	python3 asset_data.py --extract --export

export:  # export metadata to jsons, csv and contracts
	@echo "export metadata to jsons, csv and contracts"
	python3 asset_data.py --export

run_notebook:  # run asset_data.ipynb notebook
	jupyter nbconvert --to=notebook --inplace --execute asset_data.ipynb

update: extract export run_notebook  # extract from node apis and export metadata, run asset_data.ipynb notebook

build_code:  # build cw-on-chain-registry code
	@echo "build cw-on-chain-registry code"
	python3 contract_deploy.py --build_code

store_code:  # store cw-on-chain-registry code to a chain
	@echo "store cw-on-chain-registry code"
	python3 contract_deploy.py --chain_name=$(chain_name) --store_code

init_contract:  # instantiate a contract in a chain
	@echo "instantiate a contract"
	python3 contract_deploy.py --chain_name=$(chain_name) --init_contract

deploy_contract:  # build and store cw-on-chain-registry code, instantiate a contract from it
	@echo "build and store cw-on-chain-registry code, instantiate a contract from it"
	python3 contract_deploy.py --chain_name=$(chain_name) --build_code --store_code --init_contract

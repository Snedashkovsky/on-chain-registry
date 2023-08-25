default: help

all : help install_venv clean_venv extract export run_notebook update commit update_and_commit build_code store_code init_contract deploy_contract
.PHONY : all

CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
TARGET_BRANCH = update_asset_list

help:  # show help for each of the makefile recipes
	@grep -E '^[a-zA-Z0-9 -_]+:.*#'  Makefile | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

install_venv:  # install python virtual environment and requirements in it
	test -d venv || python3 -m venv venv
	. venv/bin/activate; pip install -Ur requirements.txt

clean_venv:  # clean python virtual environment and requirements in it
	rm -rf venv

extract:  # extract metadata from node apis
	@echo "pull chain-registry"
	git submodule init
	git submodule update --remote
	@echo "extract data"
	. venv/bin/activate; python3 asset_data.py --extract --export

export:  # export metadata to jsons and csv
	@echo "export metadata to jsons and csv"
	. venv/bin/activate; python3 asset_data.py --export

export_to_contracts:  # export metadata to contracts
	@echo "export metadata to contracts"
	. venv/bin/activate; python3 asset_data.py --export_to_contracts

run_notebook:  # run asset_data.ipynb notebook
	. venv/bin/activate; jupyter nbconvert --to=notebook --inplace --execute asset_data.ipynb

update: extract export run_notebook export_to_contracts # extract from node apis and export metadata, run asset_data.ipynb notebook

commit:  # commit updates
ifeq (${CURRENT_BRANCH}, ${TARGET_BRANCH})
	@echo "commit updates"
	git commit -am "- update asset list"
	git push origin ${TARGET_BRANCH}
else
	@echo "please change current branch from '${CURRENT_BRANCH}' to '${TARGET_BRANCH}' and run 'make commit'"
endif

update_and_commit: update commit  # extract from node apis and export metadata, run asset_data.ipynb notebook and commit updates

build_code:  # build cw-on-chain-registry code
	@echo "build cw-on-chain-registry code"
	. venv/bin/activate; python3 contract_deploy.py --build_code

store_code:  # store cw-on-chain-registry code to a chain
	@echo "store cw-on-chain-registry code"
	. venv/bin/activate; python3 contract_deploy.py --chain_name=$(chain_name) --store_code

init_contract:  # instantiate a contract in a chain
	@echo "instantiate a contract"
	. venv/bin/activate; python3 contract_deploy.py --chain_name=$(chain_name) --init_contract

deploy_contract:  # build and store cw-on-chain-registry code, instantiate a contract from it
	@echo "build and store cw-on-chain-registry code, instantiate a contract from it"
	. venv/bin/activate; python3 contract_deploy.py --chain_name=$(chain_name) --build_code --store_code --init_contract

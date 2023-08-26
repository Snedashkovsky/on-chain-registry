# On-Chain Registry: Cosmos-SDK Asset List
As blockchain assets transition between various chains within the Cosmos ecosystem and beyond, the need arises for a precise tool to monitor this intricate data flow. Meet the **On-Chain Registry (OCR)** – meticulously designed to compile all proof-of-nodes data, offering a timely and detailed snapshot of the current asset landscape.

## Proof-of-Nodes Concept

Rather than a static registry, the OCR represents a living, constantly updating protocol that sources data straight directly from nodes.
This mechanism leads to:  
 - **Accuracy**: The registry furnishes complete and precise data, crucial for meaningful and successful blockchain transactions.
 - **Reliability**: By ruling out the chance of human error, the registry delivers consistent information that users can rely on.
 - **Inclusivity**: It leaves out no data not specified in the chains, thereby offering a comprehensive overview of the blockchain environment.

### [Milestones](milestones.md)

### Workflow:

<p align="center">
  <img src="src/img/architecture.png" width="80%" height="80%" alt="architecture">
</p>

## Functionality

OCR provides an interface for updating, storing, and accessing data on-chain. This enables it to dynamically adapt to the ever-changing state of the chains.

**API & IBC Tokens Verification.** OCR functions as a robust and secure API, offering users the capability to verify Inter-Blockchain Communication (IBC) tokens with trusted and verified metadata. This feature further enhances the transparency and security of cross-chain transactions.

**Integration of External Registries.** In the pursuit of providing an all-encompassing data access point, OCR integrates data from other registries as well. This guarantees that users have a comprehensive, unified, and updated view of the entire blockchain ecosystem.

## Assets

On-chain based data allows viewing of **all existing assets**:

- [**chain-registry like data**](data_json)  
- [**csv data**](data_csv)  
- **contracts** ([code](https://github.com/Snedashkovsky/cw-on-chain-registry/tree/main/contracts/on-chain-registry), 
[schema](https://github.com/Snedashkovsky/cw-on-chain-registry/tree/main/contracts/on-chain-registry/schema))
  - [bostrom](https://cyb.ai/contracts/bostrom1t33kxpypdlnp28fl4sttj59jj6e5tg6sxl3423s6sjp79ldqaucqzf6y3v)
  - [osmosis-testnet](https://testnet.mintscan.io/osmosis-testnet/wasm/contract/osmo1me45lxajuhe5g0rqqwsn4rw4hm26d05q5f395742ztngu647yy2qrqwxq7)
<p align="center">
  <img src="charts/charts.png" width="100%" height="100%" alt="assets charts">
</p>

## Asset Data Structure

OCR uses a chain-registry like [asset data structure](assetlist.schema.json) for better compatibility.  
<img src="src/img/assetlist_schema.png" width="100%" height="100%" alt="assetlist schema">  

Differences from the [chain-registry asset data structure](https://github.com/cosmos/chain-registry/blob/master/assetlist.schema.json):
- add `chain_id` required property;
- `denom_units`, `display`, `name` and `symbol` asset object properties are optional;
- add `chain_id` required property in asset traces section;
- set `chain_name` property in asset traces section as optional;
- add `supply` optional property in asset section and `base_supply` optional property in asset traces section;
- add `admin` required property for `factory` asset type in asset section.

## Contract queries
[Query schema](https://github.com/Snedashkovsky/cw-on-chain-registry/tree/main/contracts/on-chain-registry/schema/query_msg.json)  
[Query examples](asset_data.ipynb)  

## How to deploy
clone repo and optionally edit the `.env` file 
```bash 
git clone https://github.com/Snedashkovsky/on-chain-registry && \
cd on-chain-registry && \
cp .env.example .env
```
install python virtual environment and requirements in it
```bash
make install_venv
```

update asset list
```bash
make update
```

## Data Sources 
[REST APIs Queries](data_sources.md)

## Contributions

We warmly welcome pull requests, issues, and feedback from the community.

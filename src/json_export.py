import pandas as pd


def get_asset_json_dict(assets_df: pd.DataFrame, chain_id_name_dict: dict[str, str]) -> dict[str, dict]:
    assets_json = {}
    for chain_id, assets_item_df in assets_df.groupby('chain_id'):
        asset_json_list = []
        for _, row in assets_item_df.iterrows():
            asset_json = {
                "base": row['denom'],
                "type_asset": row['type_asset'],
                "supply": int(row['supply']) if row['supply'] and not pd.isna(row['supply']) else 0
            }
            if row['description']:
                asset_json['description'] = row['description']
            if row['denom_units']:
                asset_json['denom_units'] = row['denom_units']
            if row['display']:
                asset_json['display'] = row['display']
            if row['name']:
                asset_json['name'] = row['name']
            if row['symbol']:
                asset_json['symbol'] = row['symbol']

            if row['type_asset'] == 'cw20':
                asset_json['address'] = row['denom_base'][5:]

            if row['type_asset'] == 'erc20' and row['denom'][:9] == 'gravity0x':
                asset_json['address'] = row['denom_base'][7:]

            if row['type_asset'] == 'snip20':
                # asset_json['address'] =   # Add
                pass

            if row['type_asset'] == 'factory':
                asset_json['address'] = row['denom']
                asset_json['admin'] = row['admin']

            if row['type_asset'] == 'ics20' and type(row['channels']) == list and \
                    len(row['channels']) == 1 and not pd.isna(row['chain_id_counterparty']):
                asset_json['ibc'] = {
                    "source_channel": row['channels'][0],
                    "dst_channel": row['channel_id_counterparty'],
                    "source_denom": row['denom_base']}  # Add source_denom calculation
                chain_name_counterparty = \
                    chain_id_name_dict[row['chain_id_counterparty']] \
                        if row['chain_id_counterparty'] in chain_id_name_dict.keys() else None
                if row['type_asset_base'] in ('sdk.coin', 'pool', 'cw20'):
                    asset_json['traces'] = [{
                        "type": 'ibc' if row['type_asset_base'] in ('sdk.coin', 'pool') else 'ibc-cw20',
                        "counterparty": {
                            "chain_id": row['chain_id_counterparty'],
                            "base_denom": row['denom_base'],
                            "channel_id": row['channel_id_counterparty']
                        },
                        "chain": {
                            "channel_id": row['channels'][0],
                            "path": f"transfer/{row['channels'][0]}/{row['denom_base']}"
                        }
                    }]
                    if chain_name_counterparty:
                        asset_json['traces'][0]["counterparty"]["chain_name"] = chain_name_counterparty
                    if row['supply_base'] and not pd.isna(row['supply_base']):
                        asset_json['traces'][0]["counterparty"]["base_supply"] = int(row['supply_base'])
                    if row['type_asset_base'] == 'cw20':
                        asset_json['traces'][0]["chain"]["port"] = 'transfer'
                        asset_json['traces'][0]["counterparty"]["port"] = 'transfer'

            asset_json_list.append(asset_json)
        assets_json[chain_id] = {
            "chain_name": chain_id_name_dict[chain_id],
            "chain_id": chain_id,
            "assets": asset_json_list
        }
    return assets_json

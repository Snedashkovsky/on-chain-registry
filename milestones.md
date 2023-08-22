# Milestones

## 1. Metadata improvements
- Add full IBC traces and front traces [#11](https://github.com/Snedashkovsky/on-chain-registry/issues/11)
- Clarify factory tokens metadata [#3](https://github.com/Snedashkovsky/on-chain-registry/issues/3)
- Another improvement

## 2. New metadata sections
- Add IBC channels metadata [#1](https://github.com/Snedashkovsky/on-chain-registry/issues/1)
- Add chain parameters [#38](https://github.com/Snedashkovsky/on-chain-registry/issues/38)
- Add `markets` subsection into assets metadata [#41](https://github.com/Snedashkovsky/on-chain-registry/issues/41)

## 3. OCR webApp
Develop webApp with interactive queries to OCR contracts and charts [#27](https://github.com/Snedashkovsky/on-chain-registry/issues/27)

## 4. Multi-Registry contract
Add support for multiple registries to the OCR contract so that any user can create and update their registry. 
This will make it possible to have a common access point to all registries of the space ecosystem, including:
- on-chain registry
- [chain registry](https://github.com/cosmos/chain-registry/)
- [keplr chain registry](https://github.com/chainapsis/keplr-chain-registry)
- [osmosis asset lists](https://github.com/osmosis-labs/assetlists)
- user registries

## 5. OCR government
Create a DAO and transfer control to it.

## 6. Updating metadata from other chains by interchain queries
Use [InterChain Queries (ICQ) module](https://docs.neutron.org/neutron/modules/interchain-queries) to update a metadata 
in an OCR contract.

## 7. Cron contract execution
Deploy an OCR cron contract by [DMN module](https://github.com/cybercongress/go-cyber/tree/main/x/dmn) as an autonomous agent that runs ICQ on a schedule.

## 8. Following tokens
Add notifications of significant changes to tokens, channels, and chains

## 9. User metadata enrichment
Add content around assets to the OCR protocol:
- scoring
- ranking
- links, pics, APIs etc.

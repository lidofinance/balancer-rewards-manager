# Balancer rewards manager

This repository contains Lido rewards controller for [Balancer Merkle Orchard contract](https://github.com/balancer-labs/balancer-v2-monorepo/blob/master/pkg/distributors/contracts/MerkleOrchard.sol) and manager for simplifying managing it via DAO voting.
Rewarder weekly approves certain amount of LDO to be spendable by Balancer contract. And provides interface to general rewards manager.

## Deploying Environment

`deploy.py` script that deploys `BalancerRewardsController` and `RewardsManager` contracts. The script next ENV variables be set.

`DEPLOYER` deployer account

`ALLOCATOR` balancer allocator account

`OWNER` address of manager owner

## BalancerRewardsController.vy
### Balancer side

##### `view available_allowance() -> uint256`

Returns current allowance limit available for distribution by calling `createDistribution`

##### `createDistribution(_token: address, _merkle_root: bytes32, _amount: uint256, _distribution_id: uint256):`

Wrapper for `createDistribution` of MerkleOrchard contract.

Wrapper for `createDistribution(token: ERC20, merkleRoot: bytes32, amount: uint256, distributionId: uint256)`
of Merkle Orchard contract and allowes to distibute LDO token holded by this contract
with amount limited by available_allowance()

Reverts if `_amount` is greater than Manager balance or allowance limit.
Reverts if `_token` is not LDO.
Reverts if contract is paused.
Reverts if contract has not enough balance to distribute `_amount` of LDO

Events:

```vyper=
event RewardsDistributed:
    amount: uint256
```

##### `set_allocator(_new_allocator: address)`

Changes `ALLOCATOR`. Can be called by owner or current allocator.

Events:

```vyper=
event AllocatorChanged:
    previous_allocator: address
    new_allocator: address
```

## Levers

##### `transfer_ownership(_to: address)`

Changes `OWNER`. Can be called by owner only.

Events:

```vyper=
event OwnerChanged:
    previous_owner: address
    new_owner: address
```


##### `set_allocator(_new_allocator: address)`

Changes `ALLOCATOR`. Can be called by owner or current allocator.

Events:

```vyper=
event AllocatorChanged:
    previous_allocator: address
    new_allocator: address
```

##### `set_distributor(_new_distributor: address)`

Changes `DISTRIBUTOR`. Can be called by owner only.

Events:

```vyper=
event RewardsDistributorChanged:
    previous_distributor: address
    new_distributor: address
```


##### `set_state(_allowance: uint256, _remining_intervals: uint256, _rewards_rate_per_interval: uint256,  _new_start_date: uint256: uint256)`

Sets new start date, allowance limit, rewards rate per period, and number of not accounted periods.

Reverts if balace of contract is lower then _new_allowance + _remining_intervals * _rewards_rate_per_interval


##### `pause()`

Stops updating allowance limit and rejects `create_ldo_distribution` calls. Can be called by owner only.

Reverts if contract is paused.

Events:
```vyper=
event Paused:
    actor: address
```

##### `unpause()`

Resumes updating allowance limit and allows `create_ldo_distribution` calls.
Can be called by owner only.

Reverts if contract is not paused.

Events:
```vyper=
event Unpaused:
    actor: address
```

##### `recover_erc20(_token: address, _amount: uint256, _recipient: address = msg.sender)`

Transfers the amount of the given ERC20 token to the recipient. Can be called by owner only.

Events:
```vyper=
event ERC20TokenRecovered:
    token: address
    amount: uint256
    recipient: address
```

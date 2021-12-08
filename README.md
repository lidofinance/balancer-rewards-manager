# Balancer rewards manager

This repository contains Lido reward manager for [Balancer Merkle Orchard contract](https://github.com/balancer-labs/balancer-v2-monorepo/blob/master/pkg/distributors/contracts/MerkleOrchard.sol).
It weekly approves certain amount of LDO to be spendable by Balancer contract. And provides interface to general rewards manager.

# Rewards Manager

The reward manager contract should be set as `owner` of the Balancer Merkle contract.

## Deploying Environment

`DEPLOYER` deployer account

`ALLOCATOR` balancer allocator account

`OWNER` address of manager owne

## Balancer side

##### `view available_allocations() -> uint256`

Returns current allowance of Reward contract.

##### `createDistribution(_token: address, _merkle_root: bytes32, _amount: uint256, _distribution_id: uint256):`

Wrapper for `createDistribution` of MerkleOrchard contract.
Can be called by allocator address only.

Reverts if `_amount` is greater than Manager balance or allocations limit.
Reverts if `_token` is not LDO.

Events:

```vyper=
event RewardsDistributed:
    amount: uint256
```

## Levers

##### `transfer_ownership(_to: address)`

Changes `OWNER`. Can be called by owner only.

Events:

```vyper=
event OwnerChanged:
    old_owner: address
    new_owner: address
```


##### `set_allocator(_new_allocator: address)`

Changes `ALLOCATOR`. Can be called by owner only.

Events:

```vyper=
event AllocatorChanged:
    old_allocator: address
    new_allocator: address
```

##### `set_distributor(_new_distributor: address)`

Changes `DISTRIBUTOR`. Can be called by owner only.

Events:

```vyper=
event RewardsDistributorChanged:
    old_distributor: address
    new_distributor: address
```


##### `set_allocations_limit(_new_allocations_limit: uint256)`

Sets new allocations limit for Reward contract.


##### `pause()`

Stops updating allocations limit and rejects `create_ldo_distribution` calls. Can be called by owner only.

Events:
```vyper=
event Paused:
    actor: address
```

##### `unpause(_start_date: uint256, _new_allocations_limit: uint256)`

Resumes updating allocations limit and allows `create_ldo_distribution` calls.
Updates contracts state with new start date and allocations limit. Can be called by owner only.

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

# Balancer rewards manager

This repository contains rewards manager for [Balancer Liquidity Gauge](https://etherscan.io/address/0xcD4722B7c24C29e0413BDCd9e51404B4539D14aE#code). The manager simplifies reward distribution operations by DAO voting and Easy Track.

## Environment preparation with Poetry

Step 1. Install dependencies
```shell
poetry install
```

Step 2. Activate newly created environment
```shell
poetry shell
```

## Testing

`brownie test -s`

## Deploying Environment

The `deploy.py` script is in charge of the `RewardsManager` contract on-chain deployment.
The following environment variables needs to be set for the script's execution:

* `DEPLOYER` - deployer account

## Specification

#### [RewardsManager.vy](contracts/RewardsManager.vy)

**def period_finish() -> uint256: view**

Returns estimated date of last rewards period start date
    
    BLG.periodFinish + (WEEKS_PER_PERIOD - self.rewards_iteration - 1) * SECONDS_PER_WEEK
    
**def start_next_rewards_period()**

Permissionless method, allows to start new weekly rewards period at Balancer Liquidity Gauge

If contact has enough assets in it (`LDO.balanceOf(self) >= self.weekly_amount`), and the BLG period is finished, it will start a new period by calling `deposit_reward_token(_reward_token: address, _amount: uint256): nonpayable` with `self.weekly_amount` as amount of LDO

Recalculates `self.weekly_amount` every 4 calls, requires balance to be not less then `self.min_rewards_amount`

Events:

```vyper=
event NewRewardsPeriodStarted:
    amount: uint256
```

```vyper=
event WeeklyRewardsAmountUpdated:
    newWeeklyRewardsAmount: uint256
```

**def balancer_period_finish() -> uint256: view**

Returns timestamp of current period ending at Balancer Liquidity Gauge

**def is_balancer_rewards_period_finished() -> bool: view**

Sign of ending of current rewards period at Balancer Liquidity Gauge

**def transfer_ownership(_to: address):**

Changes `OWNER`. Can be called by owner only.

Events:

```vyper=
event OwnershipTransferred:
    previousOwner: indexed(address)
    newOwner: indexed(address)
```

**def transfer_rewards_contract(_to: address):**

Transfers permission to start new rewards period form self.

Events:

```vyper=
event RewardsContractTransferred:
    newDistributor: indexed(address)
```

**def set_rewards_contract(_rewards_contract: address):**

```vyper=
event RewardsContractUpdated:
    newRewardsContract: indexed(address)
```

**def recover_erc20(_token: address, _amount: uint256, _recipient: address = msg.sender):**

Transfers the amount of the given ERC20 token to the recipient. Can be called by owner only.

Events:
```vyper=
event ERC20TokenRecovered:
    token: indexed(address)
    amount: uint256
    recipient: indexed(address)
```

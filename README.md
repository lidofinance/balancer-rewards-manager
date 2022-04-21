# Balancer rewards manager

This repository contains rewards manager and wrapper for [Balancer Liquidity Gauge](https://etherscan.io/address/0xcD4722B7c24C29e0413BDCd9e51404B4539D14aE#code) for simplifying managing it via DAO voting and easytracks.

## Deploying Environment

`deploy.py` script that deploys `RewardsManager` contract. The script next ENV variables be set.

`DEPLOYER` deployer account

## Testing

`brownie test -s`

## Poetry

`poetry install`

`poetry shell`

#### Wrapper

Contract implements interface for [RewardsManager](https://github.com/lidofinance/staking-rewards-manager) :

**def notifyRewardAmount(reward: uint256, rewardHolder: address):: nonpayable**

Takes reward amount from `rewardHolder`, adds it's own LDO balance, calculates weekly rewards amount and saves the result as `weekly_amount`, only distributor (manager contract) can do it.

**def periodFinish() -> uint256: view**
    
Returns estimated date of last rewards period start date
    
    BLG.periodFinish + (LDO.balanceOf(self)/self.rewardAmount - 1) * WEEK_IN_SECONDS
    
Contract has permissionless method to start a new rewards period at BLG contract.

**def start_next_rewards_period()**

Permissionless method, allows to start new weekly rewards period at Balancer Liquidity Gauge 

If contact has enough assets in it (`LDO.balanceOf(self) >= self.weekly_amount`), and the BLG period is finished, it will start a new period by calling `deposit_reward_token(_reward_token: address, _amount: uint256): nonpayable` with `self.weekly_amount` as amount of LDO

**def balancer_period_finish() -> uint256:**

Returns timestamp of current period ending at Balancer Liquiditi Gauge

**def is_balancer_rewards_period_finished() -> bool:**

Sign of ending of current rewards period at Balancer Liquidity Gauge

### Levers (owner only)

**def transfer_ownership(_to: address):**

**def transfer_rewards_contract(_to: address):**

**def set_rewards_contract(_rewards_contract: address):**

**def set_distributor(_new_disributor: address):**

**def set_min_rewards_amount(_new_min_rewards_amount: uint256):**

**def set_weekly_amount(_new_weekly_amount: uint256):**

**def recover_erc20(_token: address, _amount: uint256, _recipient: address = msg.sender):**
# @version 0.3.1
# @notice Wrapper contract for the Balancer Liquidity Gauge.
# @author bulbozaur <info@lido.fi>
# @license MIT

from vyper.interfaces import ERC20


struct BalancerReward:
    token: address
    distributor: address
    period_finish: uint256
    rate: uint256
    last_update: uint256
    integral: uint256


interface BalancerLiquidityGauge:
    def reward_data(addr: address) -> BalancerReward: view
    def deposit_reward_token(_reward_token: address, _amount: uint256): nonpayable
    def set_reward_distributor(_reward_token: address, _distributor: address): nonpayable


event OwnershipTransferred:
    previousOwner: indexed(address)
    newOwner: indexed(address)


event RewardsContractUpdated:
    newRewardsContract: indexed(address)


event RewardsContractTransfered:
    newDistributor: indexed(address)


event WeeklyRewardsAmountUpdated:
    newWeeklyRewardsAmount: uint256


event NewRewardsPeriodStarted:
    amount: uint256


event ERC20Recovered:
    token: indexed(address)
    amount: uint256
    recipient: indexed(address)


owner: public(address)
rewards_contract: public(address)
min_rewards_amount: public(uint256)
weekly_amount: public(uint256)
rewards_iteration: public(uint256)
LDO_TOKEN: constant(address) = 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32
WEEK_IN_SECONDS: constant(uint256) = 7 * 24 * 60 * 60
PERIOD_IN_WEEKS: constant(uint256) = 4


@external
def __init__(
    owner: address, 
    min_rewards_amount: uint256, 
    rewards_contract: address
):
    self.owner = owner
    self.min_rewards_amount = min_rewards_amount
    self.rewards_contract = rewards_contract

    log OwnershipTransferred(ZERO_ADDRESS, owner)
    log RewardsContractUpdated(rewards_contract)


@view
@internal
def _balancer_period_finish(rewards_contract: address) -> uint256:
    reward_data: BalancerReward = BalancerLiquidityGauge(rewards_contract).reward_data(LDO_TOKEN)
    return reward_data.period_finish


@view
@internal
def _is_balancer_rewards_period_finished(rewards_contract: address) -> bool:
    return block.timestamp >= self._balancer_period_finish(rewards_contract)


@view
@external
def is_balancer_rewards_period_finished() -> bool:
    """
    @notice Whether the current rewards period has finished.
    """
    return self._is_balancer_rewards_period_finished(self.rewards_contract)


@view
@external
def balancer_period_finish() -> uint256:
    """
    @notice Returns end of the rewards period of BalancerLiquidityGauge contract
    """
    return self._balancer_period_finish(self.rewards_contract)


@external
def start_next_rewards_period():
    """
    @notice
        Starts the next rewards period of duration `rewards_contract.deposit_reward_token(address, uint256)`,
        distributing `self.weekly_amount` tokens throughout the period. The current
        rewards period must be finished by this time and LDO balance not lower then `self.weekly_amount`.
        Ones per 4 calls recalculates `self.weekly_amount` based on self LDO balance. Balance required 
        not to be lower then `self.min_rewards_amount`
    """
    rewards_contract: address = self.rewards_contract
    amount: uint256 = ERC20(LDO_TOKEN).balanceOf(self)
    iteration: uint256 = self.rewards_iteration    
    rewards_amount: uint256 = 0

    assert rewards_contract != ZERO_ADDRESS, "manager: rewards disabled"

    if (iteration == 0):
        amount_to_distribute: uint256 = ERC20(LDO_TOKEN).balanceOf(self)
        assert amount >= self.min_rewards_amount, "manager: low balance"
        
        rewards_amount = amount / PERIOD_IN_WEEKS
        self.weekly_amount = rewards_amount

        log WeeklyRewardsAmountUpdated(rewards_amount)
    else:
        rewards_amount = self.weekly_amount
    
    if iteration < 3: 
        self.rewards_iteration = iteration + 1
    else: 
        self.rewards_iteration = 0

    assert rewards_amount > 0, "manager: rewards disabled"
    assert amount >= rewards_amount, "manager: low balance"
    assert self._is_balancer_rewards_period_finished(rewards_contract), "manager: rewards period not finished"

    ERC20(LDO_TOKEN).approve(rewards_contract, rewards_amount)
    BalancerLiquidityGauge(rewards_contract).deposit_reward_token(LDO_TOKEN, rewards_amount)

    log NewRewardsPeriodStarted(rewards_amount)


@view
@internal
def _period_finish() -> uint256:
    amount: uint256 = self.weekly_amount

    if (amount == 0): 
        return 0

    ldo_balance: uint256 = ERC20(LDO_TOKEN).balanceOf(self)
    if (ldo_balance < amount):
        return self._balancer_period_finish(self.rewards_contract)

    return self._balancer_period_finish(self.rewards_contract) + ldo_balance / amount * WEEK_IN_SECONDS


@view
@external
def period_finish() -> uint256:
    """
    @notice Returns end of the rewards period of BalancerLiquidityGauge contract
    """
    return self._period_finish()


@view
@external
def is_rewards_period_finished() -> bool:
    """
    @notice Whether the current rewards period has finished.
    """
    return block.timestamp >= self._period_finish()
    

@external
def transfer_ownership(_to: address):
    """
    @notice Changes the contract owner. Can only be called by the current owner.
    """
    current_owner: address = self.owner
    assert msg.sender == current_owner, "not permitted"
    self.owner = _to
    log OwnershipTransferred(current_owner, _to)


@external
def transfer_rewards_contract(_to: address):
    """
    @notice Changes the reward contracts distributor. Can only be called by the current owner.
    """
    assert msg.sender == self.owner, "not permitted"
    assert _to != ZERO_ADDRESS, "zero address not allowed"
    BalancerLiquidityGauge(self.rewards_contract).set_reward_distributor(LDO_TOKEN, _to)

    log RewardsContractTransfered(_to)


@external
def set_rewards_contract(_rewards_contract: address):
    """
    @notice Sets the rewards contract. Can only be called by the owner.
    """
    assert msg.sender == self.owner, "not permitted"
    self.rewards_contract = _rewards_contract

    log RewardsContractUpdated(_rewards_contract)


@external
def recover_erc20(_token: address, _amount: uint256, _recipient: address = msg.sender):
    """
    @notice
        Transfers the given _amount of the given ERC20 token from self
        to the recipient. Can only be called by the owner.
    """
    assert msg.sender == self.owner, "not permitted"
    if _amount != 0:
        assert ERC20(_token).transfer(_recipient, _amount), "token transfer failed"

        log ERC20Recovered(_token, _amount, _recipient)

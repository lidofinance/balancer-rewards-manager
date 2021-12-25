# @version 0.3.0
# @author bulbozaur <info@lido.fi>
# @notice A manager contract for the Balancer Merkle Rewards contract.

# @license MIT

from vyper.interfaces import ERC20


interface IMerkleRewardsContract:
    def createDistribution(token: address, merkleRoot: bytes32, amount: uint256, distributionId: uint256): nonpayable


event OwnerChanged:
    previous_owner: indexed(address)
    new_owner: indexed(address)


event AllocatorChanged:
    previous_allocator: indexed(address)
    new_allocator: indexed(address)


event RewardsDistributorChanged:
    previous_distributor: indexed(address)
    new_distributor: indexed(address)


event RewardsDistributed:
    amount: uint256


event ERC20TokenRecovered:
    token: indexed(address)
    amount: uint256
    recipient: indexed(address)


event AccountedAllowanceUpdated:
    new_allowance: uint256


event AccountedIntervalStartDateUpdated:
    accounted_interval_start_date: uint256


event RemainigIntervalsUpdated:
    remining_intervals: uint256


event RewadrdsRateUpdated:
    rewards_rate_per_interval: uint256


event PeriodStarted:
    intervals: uint256
    start_date: uint256
    rewards_rate_per_interval: uint256


event Paused:
    actor: indexed(address)


event Unpaused:
    actor: indexed(address)


owner: public(address)
allocator: public(address)
distributor: public(address)

rewards_contract: constant(address) = 0xdAE7e32ADc5d490a43cCba1f0c736033F2b4eFca
rewards_token: constant(address) = 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32

interval_duration: constant(uint256) = 604800     # 3600 * 24 * 7  (1 week)
rewards_iterations: constant(uint256) = 4          # number of iteration in one rewards period

accounted_interval_start_date: public(uint256)
accounted_allowance: public(uint256)

remining_intervals: public(uint256)        # number of iteration left for current rewards period
rewards_rate_per_interval: public(uint256)

is_paused: public(bool)


@external
def __init__(
    _allocator: address,
    _distributor: address,
    _start_date: uint256
):
    self.owner = msg.sender
    self.allocator = _allocator
    self.distributor = _distributor

    self.accounted_allowance = 0    # allowance at accounted_interval_start_date
    self.accounted_interval_start_date = _start_date - interval_duration

    self.is_paused = False

    self.rewards_rate_per_interval = 0

    log OwnerChanged(ZERO_ADDRESS, self.owner)
    log AllocatorChanged(ZERO_ADDRESS, self.allocator)
    log RewardsDistributorChanged(ZERO_ADDRESS, self.distributor)
    log Unpaused(self.owner)
    log AccountedAllowanceUpdated(self.accounted_allowance)
    log AccountedIntervalStartDateUpdated(self.accounted_interval_start_date)
    log RemainigIntervalsUpdated(0)


@internal
@view
def _period_finish() -> uint256:
    return self.accounted_interval_start_date + self.remining_intervals * interval_duration


@internal
@view
def _is_rewards_period_finished() -> bool:
    return block.timestamp >= self._period_finish()


@internal
@view
def _unaccounted_periods() -> uint256:
    accounted_interval_start_date: uint256 = self.accounted_interval_start_date
    if (accounted_interval_start_date > block.timestamp):
        return 0
    return (block.timestamp - accounted_interval_start_date) / interval_duration


@internal
@view
def _available_allowance() -> uint256:
    if self.is_paused == True:
        return self.accounted_allowance
    
    unaccounted_periods: uint256 = min(self._unaccounted_periods(), self.remining_intervals)
    
    return self.accounted_allowance + unaccounted_periods * self.rewards_rate_per_interval


@internal
def _update_accounted_and_remainig_intervals():
    """
    @notice 
        Updates accounted_interval_start_date to timestamp of current period
        and decreases remining_intervals by number of intervals passed
    """
    unaccounted_periods: uint256 = self._unaccounted_periods()
    if (unaccounted_periods == 0):
        return

    accounted_interval_start_date: uint256 = self.accounted_interval_start_date \
        + interval_duration * unaccounted_periods

    self.accounted_interval_start_date = accounted_interval_start_date

    remaining_intervals: uint256 = self.remining_intervals - min(self.remining_intervals, unaccounted_periods)
    
    self.remining_intervals = remaining_intervals

    log AccountedIntervalStartDateUpdated(accounted_interval_start_date)
    log RemainigIntervalsUpdated(remaining_intervals)


@internal
def _set_allowance(_new_allowance: uint256):
    """
    @notice Changes the allowance limit for Merkle Rewadrds contact. 
    """
    self.accounted_allowance = _new_allowance

    # Reseting unaccounted period date
    self._update_accounted_and_remainig_intervals()

    log AccountedAllowanceUpdated(_new_allowance)
    log AccountedIntervalStartDateUpdated(self.accounted_interval_start_date)


@internal
def _update_allowance():
    """
    @notice Updates allowance based on current calculated allowance limit
    """
    new_allowance: uint256 = self._available_allowance()
    self._set_allowance(new_allowance)


@external
def set_state(_new_allowance: uint256, _remining_intervals: uint256, _rewards_rate_per_interval: uint256, _new_start_date: uint256):
    """
    @notice 
        Sets new start date, allowance limit, rewards rate per period, and number of not accounted periods.

        Reverts if balace of contract is lower then _new_allowance + _remining_intervals * _rewards_rate_per_interval
    """
    assert msg.sender == self.owner, "manager: not permitted"
    rewarder_balance: uint256 = ERC20(rewards_token).balanceOf(self)
    required_balance: uint256 = _new_allowance + _remining_intervals * _rewards_rate_per_interval
    assert rewarder_balance >= required_balance, "manager: reward token balance is low"
    if (_new_start_date == 0):
        self._set_allowance(_new_allowance)
    else:
        accounted_interval_start_date: uint256 = _new_start_date - interval_duration
        self.accounted_interval_start_date = accounted_interval_start_date
        self.accounted_allowance = _new_allowance

        log AccountedAllowanceUpdated(_new_allowance)
        log AccountedIntervalStartDateUpdated(accounted_interval_start_date)

    self.remining_intervals = _remining_intervals
    self.rewards_rate_per_interval = _rewards_rate_per_interval

    log RemainigIntervalsUpdated(_remining_intervals)
    log RewadrdsRateUpdated(_rewards_rate_per_interval)



@external
def notifyRewardAmount(amount: uint256, holder: address):
    """
    @notice
        Starts the next rewards period from the begining of the next interval with amount from 
        holder address.
        If call before period finished it will distibute remainded amout of non distibuted tokens 
        additionally to the provided amount.
    """
    assert msg.sender == self.distributor, "manager: not permitted"

    assert ERC20(rewards_token).transferFrom(holder, self, amount), "manager: transfer failed"

    self._update_allowance()

    unaccounted_periods: uint256 = min(self._unaccounted_periods(), self.remining_intervals)
    
    amount_to_distribute: uint256 = unaccounted_periods * self.rewards_rate_per_interval + amount 
    assert amount_to_distribute != 0, "manager: no funds"
  
    rate: uint256 = amount_to_distribute / rewards_iterations
    self.rewards_rate_per_interval = rate
    self.remining_intervals = rewards_iterations

    log PeriodStarted(rewards_iterations, self.accounted_interval_start_date, rate)



@external 
def createDistribution(token: address, _merkle_root: bytes32, _amount: uint256, _distribution_id: uint256):    
    """
    @notice
        Wraps createDistribution(token: ERC20, merkleRoot: bytes32, amount: uint256, distributionId: uint256)
        of Merkle rewards contract and allowes to distibute LDO token holded by this contract
        with amount limited by available_allowance()

        Can be called by allocator address only.
    """
    assert msg.sender == self.allocator, "manager: not permitted"
    assert rewards_token == token, "manager: only LDO distribution allowed"
    assert self.is_paused == False, "manager: contract is paused"
    assert ERC20(rewards_token).balanceOf(self) >= _amount, "manager: reward token balance is low"

    available_allowance: uint256 = self._available_allowance()
    assert available_allowance >= _amount, "manager: not enought amount approved"

    self._set_allowance(available_allowance - _amount)

    ERC20(rewards_token).approve(rewards_contract, _amount)
    IMerkleRewardsContract(rewards_contract).createDistribution(rewards_token, _merkle_root, _amount, _distribution_id)

    log RewardsDistributed(_amount)


@external
def pause():
    """
    @notice
        Pause allowance increasing and rejects createDistribution calling
    """
    assert msg.sender == self.owner, "manager: not permitted"
    assert not self.is_paused, "manager: contract already paused"
    
    self._update_allowance()
    self.is_paused = True

    log Paused(msg.sender)


@external
def unpause():
    """
    @notice
        Unpause allowance increasing and allows createDistribution calling
    """
    assert msg.sender == self.owner, "manager: not permitted"
    assert self.is_paused, "manager: contract not paused"

    self._update_accounted_and_remainig_intervals()
    self.is_paused = False

    log Unpaused(msg.sender)
    log AccountedAllowanceUpdated(self.accounted_allowance)
    log AccountedIntervalStartDateUpdated(self.accounted_interval_start_date)


@external
def transfer_ownership(_to: address):
    """
    @notice Changes the contract owner. Can only be called by the current owner.
    """
    previous_owner: address = self.owner
    assert msg.sender == previous_owner, "manager: not permitted"
    assert _to != ZERO_ADDRESS, "manager: zero address not allowed"
    self.owner = _to
    log OwnerChanged(previous_owner, _to)


@external
def set_allocator(_new_allocator: address):
    """
    @notice Changes the allocator. Can only be called by the current owner or current allocator.
    """
    previous_allocator: address = self.allocator
    assert msg.sender == self.owner or msg.sender ==  previous_allocator, "manager: not permitted"
    assert _new_allocator != ZERO_ADDRESS, "manager: zero address not allowed"
    self.allocator = _new_allocator
    log AllocatorChanged(previous_allocator, _new_allocator)


@external
def set_distributor(_new_distributor: address):
    """
    @notice Changes the distributor. Can only be called by the current owner.
    """
    assert msg.sender == self.owner, "manager: not permitted"
    assert _new_distributor != ZERO_ADDRESS, "manager: zero address not allowed"
    previous_distributor: address = self.distributor
    self.distributor = _new_distributor
    log RewardsDistributorChanged(previous_distributor, _new_distributor)


@external
def recover_erc20(_token: address, _amount: uint256, _recipient: address = msg.sender):
    """
    @notice
        Transfers specified amount of the given ERC20 token from self
        to the recipient. Can only be called by the owner.
    """
    assert msg.sender == self.owner, "manager: not permitted"

    if _amount > 0:
        assert ERC20(_token).transfer(_recipient, _amount), "manager: token transfer failed"
        log ERC20TokenRecovered(_token, _amount, _recipient)


@external
@view
def periodFinish() -> uint256:
    """
    @notice Date of last allowance increasing.
    """
    return self._period_finish()


@external
@view
def is_rewards_period_finished() -> bool:
    """
    @notice Whether the current rewards period has finished.
    """
    return self._is_rewards_period_finished()


@external
@view
def available_allowance() -> uint256:
    """
    @notice 
        Returns current allowance limit available for distribution 
        by calling createDistribution
    """
    return self._available_allowance()


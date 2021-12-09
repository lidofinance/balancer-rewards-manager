# @version 0.3.0
# @author bulbozaur <info@lido.fi>
# @notice A manager contract for the Balancer Merkle Rewards contract.

# @license MIT

from vyper.interfaces import ERC20


interface IMerkleRewardsContract:
    def createDistribution(token: address, merkleRoot: bytes32, amount: uint256, distributionId: uint256): nonpayable


event OwnerChanged:
    old_owner: indexed(address)
    new_owner: indexed(address)


event AllocatorChanged:
    old_allocator: indexed(address)
    new_allocator: indexed(address)


event RewardsDistributorChanged:
    old_distributor: indexed(address)
    new_distributor: indexed(address)


event RewardsDistributed:
    amount: uint256


event ERC20TokenRecovered:
    token: indexed(address)
    amount: uint256
    recipient: indexed(address)


event Paused:
    actor: indexed(address)


event Unpaused:
    actor: indexed(address)


owner: public(address)
allocator: public(address)
distributor: public(address)

rewards_contract: constant(address) = 0xdAE7e32ADc5d490a43cCba1f0c736033F2b4eFca
rewards_token: constant(address) = 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32

period_duration: constant(uint256) = 604800     # 3600 * 24 * 7  (1 week)
rewards_periods: constant(uint256) = 4          # number of periods in one rewards iteration

last_accounted_period_start_date: public(uint256)
max_unaccounted_periods: public(uint256)        # number of periods left for current rewards iteration
rewards_rate_per_period: public(uint256)
accounted_allocations_limit: public(uint256)
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

    self.accounted_allocations_limit = 0
    self.is_paused = False
    self.last_accounted_period_start_date = _start_date - period_duration

    self.rewards_rate_per_period = 0

    log OwnerChanged(ZERO_ADDRESS, self.owner)
    log AllocatorChanged(ZERO_ADDRESS, self.allocator)
    log RewardsDistributorChanged(ZERO_ADDRESS, self.distributor)
    log Unpaused(self.owner)


@internal
@view
def _period_finish() -> uint256:
    return self.last_accounted_period_start_date + self.max_unaccounted_periods * period_duration


@external
@view
def periodFinish() -> uint256:
    return self._period_finish()


@internal
@view
def _is_rewards_period_finished() -> bool:
    return block.timestamp >= self._period_finish()


@external
@view
def is_rewards_period_finished() -> bool:
    """
    @notice Whether the current rewards period has finished.
    """
    return self._is_rewards_period_finished()


@internal
@view
def _unaccounted_periods() -> uint256:
    last_accounted_period_start_date: uint256 = self.last_accounted_period_start_date
    if (last_accounted_period_start_date > block.timestamp):
        return 0
    return (block.timestamp - self.last_accounted_period_start_date) / period_duration


@internal
@view
def _available_allocations() -> uint256:
    if self.is_paused == True:
        return self.accounted_allocations_limit
    
    unaccounted_periods: uint256 = min(self._unaccounted_periods(), self.max_unaccounted_periods)
    
    return self.accounted_allocations_limit + unaccounted_periods * self.rewards_rate_per_period


@external
@view
def available_allocations() -> uint256:
    """
    @notice 
        Returns current allocations limit for Merkle Rewards contract 
        as sum of merkle contract accounted limit
        and calculated allocations amount for unaccounted period 
        since last allocations limit update
    """
    return self._available_allocations()


@internal
def _update_last_accounted_period_start_date():
    """
    @notice 
        Updates last_accounted_period_start_date to timestamp of current period
    """
    unaccounted_periods: uint256 = self._unaccounted_periods()
    if (unaccounted_periods == 0):
        return

    self.last_accounted_period_start_date = self.last_accounted_period_start_date \
        + period_duration * unaccounted_periods
    
    self.max_unaccounted_periods = self.max_unaccounted_periods - min(self.max_unaccounted_periods, unaccounted_periods)


@internal
def _set_allocations_limit(_new_allocations_limit: uint256):
    """
    @notice Changes the allocations limit for Merkle Rewadrds contact. 
    """
    self.accounted_allocations_limit = _new_allocations_limit

    # Reseting unaccounted period date
    self._update_last_accounted_period_start_date()


@internal
def _update_allocations_limit():
    """
    @notice Updates allowance based on current calculated allocations limit
    """
    new_allocations_limit: uint256 = self._available_allocations()
    self._set_allocations_limit(new_allocations_limit)


@external
def notifyRewardAmount(amount: uint256, holder: address):
    """
    @notice
        Starts the next rewards 
        The current rewards period must be finished by this time.
    """
    assert msg.sender == self.distributor, "manager: not permitted"
    assert self._is_rewards_period_finished(), "manager: rewards period not finished"

    ERC20(rewards_token).transferFrom(holder, self, amount)
    
    amount_to_distribute: uint256 = ERC20(rewards_token).balanceOf(self) - self._available_allocations()
    assert amount_to_distribute != 0, "manager: no funds"

    self._update_allocations_limit()    
    self.rewards_rate_per_period = amount_to_distribute / rewards_periods
    self.max_unaccounted_periods = rewards_periods


@external
def set_state(_new_allocations_limit: uint256, _max_unaccounted_periods: uint256, _rewards_rate_per_period: uint256):
    """
    @notice 
        Sets new allocations limit, rewards rate per period, and number of not accounted periods.

        Reverts if balace of contract is lower then _new_allocations_limit + _max_unaccounted_periods * _rewards_rate_per_period
    """
    assert msg.sender == self.owner, "manager: not permitted"
    rewarder_balance: uint256 = ERC20(rewards_token).balanceOf(self)
    required_balance: uint256 = _new_allocations_limit + _max_unaccounted_periods * _rewards_rate_per_period
    assert rewarder_balance >= required_balance, "manager: reward token balance is low"
    
    self._set_allocations_limit(_new_allocations_limit)
    self.max_unaccounted_periods = _max_unaccounted_periods
    self.rewards_rate_per_period = _rewards_rate_per_period


@external 
def createDistribution(token: address, _merkle_root: bytes32, _amount: uint256, _distribution_id: uint256):    
    """
    @notice
        Wraps createDistribution(token: ERC20, merkleRoot: bytes32, amount: uint256, distributionId: uint256)
        of Merkle rewards contract with amount limited by available_allocations()
    """
    assert msg.sender == self.allocator, "manager: not permitted"
    assert rewards_token == token, "manager: only LDO distribution allowed"
    assert self.is_paused == False, "manager: contract is paused"
    assert ERC20(rewards_token).balanceOf(self) >= _amount, "manager: reward token balance is low"

    available_allocations: uint256 = self._available_allocations()
    assert available_allocations >= _amount, "manager: not enought amount approved"

    self._set_allocations_limit(available_allocations - _amount)

    ERC20(rewards_token).approve(rewards_contract, _amount)
    IMerkleRewardsContract(rewards_contract).createDistribution(rewards_token, _merkle_root, _amount, _distribution_id)

    log RewardsDistributed(_amount)


@external
def pause():
    """
    @notice
        Pause allocations increasing and rejects createDistribution calling
    """
    assert msg.sender == self.owner, "manager: not permitted"
    
    self._update_allocations_limit()
    self.is_paused = True

    log Paused(msg.sender)


@external
def unpause():
    """
    @notice
        Unpause allocations increasing and allows createDistribution calling
    """
    assert msg.sender == self.owner, "manager: not permitted"

    self._update_last_accounted_period_start_date()
    self.is_paused = False

    log Unpaused(msg.sender)


@external
def transfer_ownership(_to: address):
    """
    @notice Changes the contract owner. Can only be called by the current owner.
    """
    old_owner: address = self.owner
    assert msg.sender == old_owner, "manager: not permitted"
    assert _to != ZERO_ADDRESS
    self.owner = _to
    log OwnerChanged(old_owner, _to)


@external
def set_allocator(_new_allocator: address):
    """
    @notice Changes the allocator. Can only be called by the current owner.
    """
    old_allocator: address = self.allocator
    assert msg.sender == self.owner or msg.sender ==  old_allocator, "manager: not permitted"
    self.allocator = _new_allocator
    log AllocatorChanged(old_allocator, _new_allocator)


@external
def set_distributor(_new_distributor: address):
    """
    @notice Changes the distributor. Can only be called by the current owner.
    """
    old_distributor: address = self.distributor
    assert msg.sender == self.owner, "manager: not permitted"
    self.distributor = _new_distributor
    log RewardsDistributorChanged(old_distributor, _new_distributor)


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

import pytest
from brownie import reverts, chain, ZERO_ADDRESS
from math import floor
from utils.config import steth_token_address

rewards_limit = 75 * 1000 * 10**18
rewards_period = 3600 * 24 * 7
amount = 300_000 * 10**18

def test_init(ldo_agent, balancer_allocator, rewards_contract, program_start_date):
    assert rewards_contract.owner() == ldo_agent
    assert rewards_contract.allocator() == balancer_allocator
    assert rewards_contract.rewards_rate_per_interval() == 0
    assert rewards_contract.accounted_allowance() == 0
    assert rewards_contract.accounted_interval_start_date() == program_start_date - rewards_period


def test_transfer_ownership(
    rewards_contract, 
    ldo_agent, 
    stranger, 
    helpers,
    ):

    with reverts():
        rewards_contract.transfer_ownership(stranger, {"from": stranger})

    assert rewards_contract.owner() == ldo_agent
    tx = rewards_contract.transfer_ownership(stranger, {"from": ldo_agent})
    assert rewards_contract.owner() == stranger

    helpers.assert_single_event_named("OwnerChanged", tx, {"previous_owner": ldo_agent, "new_owner": stranger})


def test_set_allocator(rewards_contract, ldo_agent, balancer_allocator, stranger, helpers):
    with reverts():
        rewards_contract.set_allocator(stranger, {"from": stranger})

    assert rewards_contract.allocator() == balancer_allocator

    with reverts():
        rewards_contract.set_allocator(ZERO_ADDRESS, {"from": ldo_agent})

    tx = rewards_contract.set_allocator(stranger, {"from": ldo_agent})
    assert rewards_contract.allocator() == stranger

    helpers.assert_single_event_named("AllocatorChanged", tx, {"previous_allocator": balancer_allocator, "new_allocator": stranger})


def test_set_allocator_by_current_allocator(rewards_contract, ldo_agent, balancer_allocator, stranger, helpers):
    with reverts():
        rewards_contract.set_allocator(stranger, {"from": stranger})

    assert rewards_contract.allocator() == balancer_allocator
    tx = rewards_contract.set_allocator(stranger, {"from": balancer_allocator})
    assert rewards_contract.allocator() == stranger

    helpers.assert_single_event_named("AllocatorChanged", tx, {"previous_allocator": balancer_allocator, "new_allocator": stranger})


def test_set_distributor(rewards_contract, rewards_manager, ldo_agent, stranger, helpers):
    with reverts():
        rewards_contract.set_distributor(stranger, {"from": stranger})

    assert rewards_contract.distributor() == rewards_manager
    tx = rewards_contract.set_distributor(stranger, {"from": ldo_agent})
    assert rewards_contract.distributor() == stranger

    helpers.assert_single_event_named("RewardsDistributorChanged", tx, {"previous_distributor": rewards_manager, "new_distributor": stranger})


@pytest.mark.parametrize(
    'period', 
    [
        rewards_period, 
        rewards_period - 10, 
        rewards_period + 10, 
        floor(0.5*rewards_period), 
        floor(0.9*rewards_period), 
        floor(2.5*rewards_period)
    ]
)
def test_allowance_basic_calculation(rewards_manager, rewards_contract, ldo_token, dao_treasury, period, stranger, program_start_date):
    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_manager) == amount
    rewards_manager.start_next_rewards_period({"from": stranger})

    assert rewards_contract.available_allowance() == 0

    chain.sleep(program_start_date + period - chain.time())
    chain.mine()

    assert rewards_contract.available_allowance() == min(4, floor(period/rewards_period + 1)) * rewards_limit
    
    chain.sleep(rewards_period)
    chain.mine()

    assert rewards_contract.available_allowance() == min(4, floor(period/rewards_period + 2 )) * rewards_limit
    

def test_allowance_paused_calculation(
    rewards_contract, 
    rewards_manager, 
    dao_treasury, 
    ldo_token, 
    stranger, 
    ldo_agent, 
    program_start_date
    ):
    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_manager) == amount
    rewards_manager.start_next_rewards_period({"from": stranger})


    assert rewards_contract.available_allowance() == 0
    chain.sleep(floor(1.1 * rewards_period))
    chain.mine()
    assert rewards_contract.available_allowance() == rewards_limit
    rewards_contract.pause({"from": ldo_agent})
    assert rewards_contract.available_allowance() == rewards_limit
    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allowance() == rewards_limit

    rewards_contract.unpause({"from": ldo_agent})
    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allowance() == 2 * rewards_limit

def test_pause(
    rewards_contract, 
    rewards_manager, 
    dao_treasury, 
    ldo_token, 
    stranger, 
    ldo_agent, 
    helpers, 
    balancer_allocator, 
    program_start_date
    ):
    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_manager) == amount
    rewards_manager.start_next_rewards_period({"from": stranger})

    assert rewards_contract.is_paused() == False

    chain.sleep(rewards_period)
    chain.mine()

    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', 0, 0, {"from": balancer_allocator})
    rewards_contract.createDistribution(ldo_token, '', 0, 0, {"from": balancer_allocator})

    assert rewards_contract.available_allowance() == rewards_limit

    with reverts():
        rewards_contract.unpause({"from": ldo_agent})

    with reverts():
        rewards_contract.pause({"from": stranger})
    tx = rewards_contract.pause({"from": ldo_agent})
    
    helpers.assert_single_event_named("Paused", tx, {"actor": ldo_agent})
    assert rewards_contract.is_paused() == True
    assert rewards_contract.available_allowance() == rewards_limit

    with reverts():
        rewards_contract.pause({"from": ldo_agent})

    with reverts('manager: contract is paused'):
        rewards_contract.createDistribution(ldo_token, '', 0, 1, {"from": balancer_allocator})

    with reverts():
        rewards_contract.unpause({"from": stranger})
    tx = rewards_contract.unpause({"from": ldo_agent})

    helpers.assert_single_event_named("Unpaused", tx, {"actor": ldo_agent})
    assert rewards_contract.is_paused() == False

    rewards_contract.createDistribution(ldo_token, '', 0, 1, {"from": balancer_allocator})


def test_set_state(
    rewards_contract, 
    rewards_manager, 
    dao_treasury, 
    ldo_token, 
    stranger, 
    ldo_agent,
    program_start_date
    ):
    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_manager) == amount
    rewards_manager.start_next_rewards_period({"from": stranger})

    assert rewards_contract.available_allowance() == 0

    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allowance() == rewards_limit

    with reverts('manager: not permitted'):
        rewards_contract.set_state(10, 2, amount, program_start_date, {"from": stranger})
    with reverts('manager: reward token balance is low'):
        rewards_contract.set_state( 10, 2, amount, program_start_date, {"from": ldo_agent})

    rewards_contract.set_state(2*10**18, 1, 10**18, 0, {"from": ldo_agent})
    assert rewards_contract.available_allowance() == 2*10**18
    assert rewards_contract.remaining_intervals() == 1
    assert rewards_contract.rewards_rate_per_interval() == 10**18
    
    new_start_date = chain.time() + 100
    rewards_contract.set_state(10**18, 2, (amount - 10**18)/2, new_start_date, {"from": ldo_agent})
    assert rewards_contract.available_allowance() == 10**18
    assert rewards_contract.remaining_intervals() == 2
    assert rewards_contract.rewards_rate_per_interval() == (amount - 10**18)/2
    assert rewards_contract.accounted_interval_start_date() == new_start_date - rewards_period


def test_createDistribution(
    rewards_contract, 
    rewards_manager, 
    dao_treasury, 
    ldo_token, 
    stranger, 
    ldo_agent,
    helpers,
    balancer_allocator
):
    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_manager) == amount
    rewards_manager.start_next_rewards_period({"from": stranger})

    with reverts():
        rewards_contract.createDistribution(ldo_token, '', 0, 0, {"from": stranger})

    rewards_contract.pause({"from": ldo_agent})
    with reverts():
        rewards_contract.createDistribution(ldo_token, '', 0,  0, {"from": balancer_allocator})
    rewards_contract.unpause({"from": ldo_agent})


    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allowance() == rewards_limit
    
    with reverts('manager: not enought amount approved'):
        rewards_contract.createDistribution(ldo_token, '', 76000 * 10**18, 0, {"from": balancer_allocator})
    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', rewards_limit, 0, {"from": balancer_allocator})

    tx = rewards_contract.createDistribution(ldo_token, '', rewards_limit, 0, {"from": balancer_allocator})
    helpers.assert_single_event_named("RewardsDistributed", tx, {"amount": rewards_limit})
    assert rewards_contract.available_allowance() == 0
    assert ldo_token.balanceOf(rewards_contract) == 3*rewards_limit


def test_recover_erc20(rewards_contract, ldo_agent, ldo_token, stranger, helpers, dao_treasury):
    ldo_token.transfer(rewards_contract, 100, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_contract) == 100

    with reverts('manager: not permitted'):
        rewards_contract.recover_erc20(ldo_token, 100, ldo_agent, {"from": stranger})

    balance = ldo_token.balanceOf(ldo_agent)

    tx = rewards_contract.recover_erc20(ldo_token, 100, ldo_agent, {"from": ldo_agent})
    assert ldo_token.balanceOf(rewards_contract) == 0
    assert ldo_token.balanceOf(ldo_agent) == balance + 100
    helpers.assert_single_event_named(
        "ERC20TokenRecovered", 
        tx, 
        {"token": ldo_token, "amount": 100, "recipient": ldo_agent}
    )

def test_recover_erc20_empty_balance(
    rewards_contract, 
    ldo_agent, 
    ldo_token, 
    stranger
):
    assert ldo_token.balanceOf(rewards_contract) == 0

    with reverts('manager: not permitted'):
        rewards_contract.recover_erc20(ldo_token, 100, ldo_agent, {"from": stranger})
    with reverts('manager: token transfer failed'):
        rewards_contract.recover_erc20(ldo_token, 100, ldo_agent, {"from": ldo_agent})


def test_notify_rewards_amount_reverts_zero_amount(
    rewards_contract, 
    rewards_manager,
    dao_treasury,
    ldo_token
):
    ldo_token.transfer(rewards_manager, 100, {"from": dao_treasury})
    ldo_token.approve(rewards_contract, 100, {"from": rewards_manager})
    with reverts('manager: no funds'):
        rewards_contract.notifyRewardAmount(0, rewards_manager, {"from": rewards_manager})


def test_allowance_before_start_date(
    rewards_contract, 
    rewards_manager,
    ldo_agent
):
    new_start_date = chain.time() + rewards_period + 1000
    rewards_contract.set_state(0, 0, 0, new_start_date, {"from": ldo_agent})
    assert rewards_contract.available_allowance() == 0
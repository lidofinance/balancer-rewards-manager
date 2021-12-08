import pytest
from brownie import reverts, chain
from math import floor
from utils.config import steth_token_address

rewards_limit = 75 * 1000 * 10**18
rewards_period = 3600 * 24 * 7
amount = 300_000 * 10**18
start_date = 1638748800 #  Monday, 6 December 2021, 0:00:00

def test_init(ldo_agent, balancer_allocator, rewards_contract):
    assert rewards_contract.owner() == ldo_agent
    assert rewards_contract.allocator() == balancer_allocator
    assert rewards_contract.rewards_rate_per_period() == 0
    assert rewards_contract.accounted_allocations_limit() == 0
    assert rewards_contract.last_accounted_period_start_date() == 0


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

    helpers.assert_single_event_named("OwnerChanged", tx, {"old_owner": ldo_agent, "new_owner": stranger})


def test_set_allocator(rewards_contract, ldo_agent, balancer_allocator, stranger, helpers):
    with reverts():
        rewards_contract.set_allocator(stranger, {"from": stranger})

    assert rewards_contract.allocator() == balancer_allocator
    tx = rewards_contract.set_allocator(stranger, {"from": ldo_agent})
    assert rewards_contract.allocator() == stranger

    helpers.assert_single_event_named("AllocatorChanged", tx, {"old_allocator": balancer_allocator, "new_allocator": stranger})


def test_set_distributor(rewards_contract, rewards_manager, ldo_agent, balancer_allocator, stranger, helpers):
    with reverts():
        rewards_contract.set_distributor(stranger, {"from": stranger})

    assert rewards_contract.distributor() == rewards_manager
    tx = rewards_contract.set_distributor(stranger, {"from": ldo_agent})
    assert rewards_contract.distributor() == stranger

    helpers.assert_single_event_named("RewardsDistributorChanged", tx, {"old_distributor": rewards_manager, "new_distributor": stranger})


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
def test_allocations_limit_basic_calculation(rewards_manager, rewards_contract, ldo_token, dao_treasury, period, stranger):
    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_manager) == amount
    rewards_manager.start_next_rewards_period({"from": stranger})

    start_date = rewards_contract.last_accounted_period_start_date() + rewards_period
    assert rewards_contract.available_allocations() == rewards_limit

    chain.sleep(start_date + period - chain.time())
    chain.mine()

    assert rewards_contract.available_allocations() == min(4, floor(period/rewards_period + 1)) * rewards_limit
    
    chain.sleep(rewards_period)
    chain.mine()
    
    assert rewards_contract.available_allocations() == min(4, floor(period/rewards_period + 2 )) * rewards_limit
    

def test_allocations_limit_paused_calculation(
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


    assert rewards_contract.available_allocations() == rewards_limit
    chain.sleep(floor(1.1 * rewards_period))
    chain.mine()
    assert rewards_contract.available_allocations() == 2 * rewards_limit
    rewards_contract.pause({"from": ldo_agent})
    assert rewards_contract.available_allocations() == 2 * rewards_limit
    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allocations() == 2 * rewards_limit

    rewards_contract.unpause(program_start_date + 2 * rewards_period, rewards_limit, {"from": ldo_agent})
    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allocations() == 2 * rewards_limit

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

    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', 0, 0, {"from": balancer_allocator})

    rewards_contract.createDistribution(ldo_token, '', 0, 0, {"from": balancer_allocator})

    with reverts():
        rewards_contract.pause({"from": stranger})

    tx = rewards_contract.pause({"from": ldo_agent})
    helpers.assert_single_event_named("Paused", tx, {"actor": ldo_agent})
    assert rewards_contract.is_paused() == True

    assert rewards_contract.available_allocations() == rewards_limit

    with reverts():
        rewards_contract.createDistribution(ldo_token, '', 0, 1, {"from": balancer_allocator})
    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', 0, 1, {"from": balancer_allocator})

    with reverts():
        rewards_contract.unpause(program_start_date, 0, {"from": stranger})

    tx = rewards_contract.unpause(program_start_date, 0, {"from": ldo_agent})
    helpers.assert_single_event_named("Unpaused", tx, {"actor": ldo_agent})
    assert rewards_contract.is_paused() == False

    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', 0, 1, {"from": balancer_allocator})
    rewards_contract.createDistribution(ldo_token, '', 0, 1, {"from": balancer_allocator})


def test_set_allocations_limit(
    rewards_contract, 
    rewards_manager, 
    dao_treasury, 
    ldo_token, 
    stranger, 
    ldo_agent
    ):
    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_manager) == amount
    rewards_manager.start_next_rewards_period({"from": stranger})

    assert rewards_contract.available_allocations() == rewards_limit

    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allocations() == 2 * rewards_limit

    with reverts():
        rewards_contract.set_allocations_limit(10, {"from": stranger})

    rewards_contract.set_allocations_limit( 10, {"from": ldo_agent})
    assert rewards_contract.available_allocations() == 10


def test_create_ldo_distribution(
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

    with reverts():
        rewards_contract.create_ldo_distribution('', 0, 0, {"from": stranger})

    rewards_contract.pause({"from": ldo_agent})
    with reverts():
        rewards_contract.create_ldo_distribution('', 0,  0, {"from": balancer_allocator})
    rewards_contract.unpause(program_start_date, 0, {"from": ldo_agent})


    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allocations() == rewards_limit
    
    with reverts('manager: not enought amount approved'):
        rewards_contract.create_ldo_distribution('', 76000 * 10**18, 0, {"from": balancer_allocator})

    tx = rewards_contract.create_ldo_distribution('', rewards_limit, 0, {"from": balancer_allocator})
    helpers.assert_single_event_named("RewardsDistributed", tx, {"amount": rewards_limit})
    assert rewards_contract.available_allocations() == 0
    assert ldo_token.balanceOf(rewards_contract) == 3*rewards_limit


def test_createDistribution(
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

    with reverts():
        rewards_contract.createDistribution(ldo_token, '', 0, 0, {"from": stranger})

    rewards_contract.pause({"from": ldo_agent})
    with reverts():
        rewards_contract.createDistribution(ldo_token, '', 0,  0, {"from": balancer_allocator})
    rewards_contract.unpause(program_start_date, 0, {"from": ldo_agent})


    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allocations() == rewards_limit
    
    with reverts('manager: not enought amount approved'):
        rewards_contract.createDistribution(ldo_token, '', 76000 * 10**18, 0, {"from": balancer_allocator})
    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', rewards_limit, 0, {"from": balancer_allocator})

    tx = rewards_contract.createDistribution(ldo_token, '', rewards_limit, 0, {"from": balancer_allocator})
    helpers.assert_single_event_named("RewardsDistributed", tx, {"amount": rewards_limit})
    assert rewards_contract.available_allocations() == 0
    assert ldo_token.balanceOf(rewards_contract) == 3*rewards_limit


def test_recover_erc20(rewarder, ldo_agent, ldo_token, stranger, helpers, dao_treasury):
    ldo_token.transfer(rewarder[1], 100, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewarder[1]) == 100

    with reverts('manager: not permitted'):
        rewarder[1].recover_erc20(ldo_token, 100, ldo_agent, {"from": stranger})

    balance = ldo_token.balanceOf(ldo_agent)

    tx = rewarder[1].recover_erc20(ldo_token, 100, ldo_agent, {"from": ldo_agent})
    assert ldo_token.balanceOf(rewarder[1]) == 0
    assert ldo_token.balanceOf(ldo_agent) == balance + 100
    helpers.assert_single_event_named(
        "ERC20TokenRecovered", 
        tx, 
        {"token": ldo_token, "amount": 100, "recipient": ldo_agent}
    )

def test_recover_erc20_empty_balance(
    rewarder, 
    ldo_agent, 
    ldo_token, 
    stranger
):
    assert ldo_token.balanceOf(rewarder[1]) == 0

    with reverts('manager: not permitted'):
        rewarder[1].recover_erc20(ldo_token, 100, ldo_agent, {"from": stranger})
    with reverts('manager: token transfer failed'):
        rewarder[1].recover_erc20(ldo_token, 100, ldo_agent, {"from": ldo_agent})

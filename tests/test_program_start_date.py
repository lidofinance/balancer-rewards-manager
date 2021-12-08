import pytest
import time
from brownie import reverts, chain
from scripts.deploy import deploy_manager_and_reward_contract
from math import floor
from utils.config import steth_token_address

rewards_limit = 75 * 1000 * 10**18
rewards_period = 3600 * 24 * 7
start_date = 1638748800 #  Monday, 6 December 2021, 0:00:00
amount = 300_000 * 10**18

def test_start_program(
    balancer_allocator, 
    ldo_token, 
    dao_treasury, 
    deployer,
    stranger
    ):

    (rewards_manager, rewards_contract) = deploy_manager_and_reward_contract(balancer_allocator, {"from": deployer})

    chain.sleep(1639137600 - chain.time())  # Wiating for omnibus finishing Fri Dec 10 2021 12:00:00 GMT+0000 
    chain.mine()

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})

    rewards_manager.start_next_rewards_period({"from": stranger})
    
    assert rewards_contract.available_allocations() == rewards_limit

    with reverts('manager: not enought amount approved'):
        rewards_contract.createDistribution(ldo_token, '', rewards_limit + 1, 0, {"from": balancer_allocator})
    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', rewards_limit + 1, 0, {"from": balancer_allocator})

    chain.sleep(rewards_period) 
    chain.mine()

    assert rewards_contract.available_allocations() == 2 * rewards_limit
    
    rewards_contract.create_ldo_distribution('', rewards_limit, 0, {"from": balancer_allocator})
    assert ldo_token.balanceOf(rewards_contract) == amount - rewards_limit
    assert rewards_contract.available_allocations() == rewards_limit

    chain.sleep(rewards_period) # waiting for next period
    chain.mine()
    
    assert rewards_contract.available_allocations() == 2 * rewards_limit


def test_start_program_next_iteration(
    balancer_allocator, 
    ldo_token, 
    dao_treasury, 
    rewards_manager, 
    rewards_contract,
    stranger
    ):

    chain.sleep(start_date - rewards_period - chain.time() + 100 )
    chain.mine()

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    rewards_manager.start_next_rewards_period({"from": stranger})

    assert rewards_contract.available_allocations() == rewards_limit

    chain.sleep(4*rewards_period) 
    chain.mine()

    rewards_contract.create_ldo_distribution('', 4 * rewards_limit, 0, {"from": balancer_allocator})
    assert rewards_contract.available_allocations() == 0

    chain.sleep(3*rewards_period) # waiting for next period
    chain.mine()

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    rewards_manager.start_next_rewards_period({"from": stranger})
    assert rewards_contract.available_allocations() == 0

import pytest
import time
from brownie import reverts, chain
from scripts.deploy import deploy_manager_and_reward_contract
from math import floor
from utils.config import steth_token_address

rewards_limit = 75 * 1000 * 10**18
rewards_period = 3600 * 24 * 7
amount = 300_000 * 10**18

def test_happy_path(
    balancer_allocator, 
    ldo_token, 
    dao_treasury, 
    deployer,
    stranger,
    program_start_date
    ):

    (rewards_manager, rewards_contract) = deploy_manager_and_reward_contract(balancer_allocator, program_start_date, {"from": deployer})

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})

    rewards_manager.start_next_rewards_period({"from": stranger})
    
    assert rewards_contract.available_allowance() == 0

    chain.sleep(program_start_date - chain.time() - 1) 
    chain.mine()

    assert rewards_contract.available_allowance() == 0

    chain.sleep(2) 
    chain.mine()

    assert rewards_contract.available_allowance() == rewards_limit

    with reverts('manager: not enought amount approved'):
        rewards_contract.createDistribution(ldo_token, '', rewards_limit + 1, 0, {"from": balancer_allocator})
    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', rewards_limit + 1, 0, {"from": balancer_allocator})
    rewards_contract.createDistribution(ldo_token, '', rewards_limit, 0, {"from": balancer_allocator})

    assert ldo_token.balanceOf(rewards_contract) == amount - rewards_limit
    assert rewards_contract.available_allowance() == 0

    chain.sleep(rewards_period)
    chain.mine()
    
    assert rewards_contract.available_allowance() == rewards_limit

    chain.sleep(2*rewards_period)
    chain.mine()

    assert rewards_manager.is_rewards_period_finished() == True
    assert rewards_contract.available_allowance() == 3 * rewards_limit

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    rewards_manager.start_next_rewards_period({"from": stranger})
    assert rewards_contract.available_allowance() == 3 * rewards_limit

    chain.sleep(4*rewards_period)
    chain.mine()

    assert rewards_contract.available_allowance() == 7 * rewards_limit

    assert (chain.time() - program_start_date)

    chain.sleep(2*rewards_period)
    chain.mine()

    assert rewards_contract.available_allowance() == 7 * rewards_limit

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    rewards_manager.start_next_rewards_period({"from": stranger})

    assert rewards_contract.available_allowance() == 7 * rewards_limit

    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allowance() == 8 * rewards_limit
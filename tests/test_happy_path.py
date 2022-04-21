import pytest
from brownie import chain
from scripts.deploy import deploy_manager_and_wrapper
from math import floor
from utils.config import balancer_rewards_contract, min_rewards_amount

rewards_period = 3600 * 24 * 7
rewards_amount = 75_000 * 10**18

def test_happy_path(
    ldo_token, 
    dao_treasury, 
    deployer,
    stranger,
    rewards_contract,
    balancer_admin
):

    chain.sleep(5 * rewards_period) 
    chain.mine()

    (rewards_manager, wrapper_contract) = deploy_manager_and_wrapper(
        balancer_rewards_contract, 
        min_rewards_amount, 
        {"from": deployer}
    )
    rewards_contract.set_reward_distributor(ldo_token, wrapper_contract, {"from": balancer_admin})
    
    for month in range(2):
        ldo_token.transfer(rewards_manager, rewards_amount, {"from": dao_treasury})
        rewards_manager.start_next_rewards_period({"from": stranger})

        for week in range (4):
            wrapper_contract.start_next_rewards_period({"from": stranger})

            chain.sleep(rewards_period) 
            chain.mine()
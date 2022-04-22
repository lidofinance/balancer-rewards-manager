import pytest
from brownie import chain, RewardsManager
from math import floor
from utils.config import balancer_rewards_contract, min_rewards_amount

rewards_period = 3600 * 24 * 7
rewards_amount = 50_000 * 10**18

def test_happy_path(
    ldo_token, 
    dao_treasury, 
    ldo_agent,
    stranger,
    rewards_contract,
    balancer_admin,
    deployer
):

    chain.sleep(rewards_period) 
    chain.mine()

    rewards_manager = RewardsManager.deploy(
        ldo_agent, 
        min_rewards_amount, 
        balancer_rewards_contract,
        {"from": deployer}
    )
    
    rewards_contract.set_reward_distributor(ldo_token, rewards_manager, {"from": balancer_admin})
    
    for month in range(2):
        ldo_token.transfer(rewards_manager, rewards_amount, {"from": dao_treasury})

        for week in range (4):
            rewards_manager.start_next_rewards_period({"from": stranger})

            chain.sleep(rewards_period) 
            chain.mine()
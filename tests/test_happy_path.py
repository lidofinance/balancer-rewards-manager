import pytest
from brownie import chain
from scripts.deploy import deploy_manager
from math import floor
from utils.config import balancer_rewards_contract

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

    rewards_manager = deploy_manager(balancer_rewards_contract, {"from": deployer})
    rewards_contract.set_reward_distributor(ldo_token, rewards_manager, {"from": balancer_admin})
    
    chain.sleep(rewards_period) 
    chain.mine()
    
    ldo_token.transfer(rewards_manager, rewards_amount, {"from": dao_treasury})
    
    rewards_manager.start_next_rewards_period({"from": stranger})

    chain.sleep(rewards_period) 
    chain.mine()

    ldo_token.transfer(rewards_manager, rewards_amount, {"from": dao_treasury})
    
    rewards_manager.start_next_rewards_period({"from": stranger})

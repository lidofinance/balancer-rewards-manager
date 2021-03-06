import pytest
from brownie import chain, RewardsManager, reverts
from math import floor
from utils.config import balancer_rewards_contract, min_rewards_amount
from os.path import exists
import json

deployment_file_path = 'deployed-mainnet.json'

rewards_period = 3600 * 24 * 7
rewards_amount = 50_000 * 10**18

def test_happy_path(
    ldo_token, 
    dao_treasury, 
    ldo_agent,
    stranger,
    rewards_contract,
    balancer_admin,
    deployer,
    helpers
):

    chain.sleep(rewards_period) 
    chain.mine()

    rewards_manager = RewardsManager.deploy(
            ldo_agent, 
            min_rewards_amount, 
            balancer_rewards_contract,
            {"from": deployer}
        )

    reward_data = rewards_contract.reward_data(ldo_token)
    assert reward_data[1] != rewards_manager
    rewards_contract.set_reward_distributor(ldo_token, rewards_manager, {"from": balancer_admin})
    reward_data = rewards_contract.reward_data(ldo_token)
    assert reward_data[1] == rewards_manager
    assert reward_data[2] == rewards_manager.period_finish()

    for month in range(2):
        with reverts("manager: low balance"):
            rewards_manager.start_next_rewards_period({"from": stranger})

        ldo_token.transfer(rewards_manager, 4*rewards_amount, {"from": dao_treasury})
        balance_before = ldo_token.balanceOf(rewards_contract)

        
        reward_data = rewards_contract.reward_data(ldo_token)
        assert reward_data[2] == rewards_manager.period_finish()

        tx = rewards_manager.start_next_rewards_period({"from": stranger})
        
        reward_data = rewards_contract.reward_data(ldo_token)
        assert reward_data[2] + rewards_period * 3 == rewards_manager.period_finish()

        helpers.assert_single_event_named(
            "NewRewardsPeriodStarted", 
            tx, 
            {"amount": rewards_amount}
        )

        helpers.assert_single_event_named(
            "WeeklyRewardsAmountUpdated", 
            tx, 
            {"newWeeklyRewardsAmount": rewards_amount}
        )

        chain.sleep(rewards_period - 10) 
        chain.mine()

        with reverts("manager: rewards period not finished"):
            rewards_manager.start_next_rewards_period({"from": stranger})

        assert ldo_token.balanceOf(rewards_contract) == balance_before + rewards_amount

        chain.sleep(10) 
        chain.mine()

        for week in range (3):

            reward_data = rewards_contract.reward_data(ldo_token)
            assert reward_data[2] + rewards_period * (3 - week) == rewards_manager.period_finish()

            balance_before = ldo_token.balanceOf(rewards_contract)
            tx = rewards_manager.start_next_rewards_period({"from": stranger})

            reward_data = rewards_contract.reward_data(ldo_token)
            assert reward_data[2] + rewards_period * (3 - week - 1) == rewards_manager.period_finish()
            
            helpers.assert_single_event_named(
                "NewRewardsPeriodStarted", 
                tx, 
                {"amount": rewards_amount}
            )

            chain.sleep(rewards_period - 10) 
            chain.mine()

            with reverts("manager: rewards period not finished"):
                rewards_manager.start_next_rewards_period({"from": stranger})

            assert ldo_token.balanceOf(rewards_contract) == balance_before + rewards_amount

            chain.sleep(10) 
            chain.mine()


def test_acceptance(
    ldo_token, 
    dao_treasury, 
    stranger,
    rewards_contract,
    balancer_admin,
    helpers
):
    chain.sleep(rewards_period) 
    chain.mine()
    
    f = open(deployment_file_path, 'r')
    deployment_data = json.load(f)
    rewards_manager = RewardsManager.at(deployment_data["balancerRewardsManager"]["baseAddress"])
    f.close()

    reward_data = rewards_contract.reward_data(ldo_token)
    assert reward_data[1] != rewards_manager
    rewards_contract.set_reward_distributor(ldo_token, rewards_manager, {"from": balancer_admin})
    reward_data = rewards_contract.reward_data(ldo_token)
    assert reward_data[1] == rewards_manager
    assert reward_data[2] == rewards_manager.period_finish()

    for month in range(2):
        with reverts("manager: low balance"):
            rewards_manager.start_next_rewards_period({"from": stranger})

        ldo_token.transfer(rewards_manager, 4*rewards_amount, {"from": dao_treasury})
        balance_before = ldo_token.balanceOf(rewards_contract)

        
        reward_data = rewards_contract.reward_data(ldo_token)
        assert reward_data[2] == rewards_manager.period_finish()

        tx = rewards_manager.start_next_rewards_period({"from": stranger})
        
        reward_data = rewards_contract.reward_data(ldo_token)
        assert reward_data[2] + rewards_period * 3 == rewards_manager.period_finish()

        helpers.assert_single_event_named(
            "NewRewardsPeriodStarted", 
            tx, 
            {"amount": rewards_amount}
        )

        helpers.assert_single_event_named(
            "WeeklyRewardsAmountUpdated", 
            tx, 
            {"newWeeklyRewardsAmount": rewards_amount}
        )

        chain.sleep(rewards_period - 10) 
        chain.mine()

        with reverts("manager: rewards period not finished"):
            rewards_manager.start_next_rewards_period({"from": stranger})

        assert ldo_token.balanceOf(rewards_contract) == balance_before + rewards_amount

        chain.sleep(10) 
        chain.mine()

        for week in range (3):

            reward_data = rewards_contract.reward_data(ldo_token)
            assert reward_data[2] + rewards_period * (3 - week) == rewards_manager.period_finish()

            balance_before = ldo_token.balanceOf(rewards_contract)
            tx = rewards_manager.start_next_rewards_period({"from": stranger})

            reward_data = rewards_contract.reward_data(ldo_token)
            assert reward_data[2] + rewards_period * (3 - week - 1) == rewards_manager.period_finish()
            
            helpers.assert_single_event_named(
                "NewRewardsPeriodStarted", 
                tx, 
                {"amount": rewards_amount}
            )

            chain.sleep(rewards_period - 10) 
            chain.mine()

            with reverts("manager: rewards period not finished"):
                rewards_manager.start_next_rewards_period({"from": stranger})

            assert ldo_token.balanceOf(rewards_contract) == balance_before + rewards_amount

            chain.sleep(10) 
            chain.mine()
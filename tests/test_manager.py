import pytest

from brownie import reverts, ZERO_ADDRESS, chain

random_address = "0xb842afd82d940ff5d8f6ef3399572592ebf182b0"
rewards_period = 3600 * 24 * 7

def test_init(rewards_manager, rewards_contract_mock, ldo_agent):
    assert rewards_manager.owner() == ldo_agent
    assert rewards_manager.rewards_contract() == rewards_contract_mock
    assert rewards_manager.weekly_amount() == 0


def test_stranger_can_not_set_rewards_contract(rewards_manager, stranger):
    assert rewards_manager.rewards_contract()   != ZERO_ADDRESS
    with reverts("not permitted"):
        rewards_manager.set_rewards_contract(ZERO_ADDRESS, {"from": stranger})


def test_owner_can_set_rewards_contract(rewards_manager, ldo_agent, helpers):
    assert rewards_manager.rewards_contract() != random_address
    tx = rewards_manager.set_rewards_contract(random_address, {"from": ldo_agent})
    assert rewards_manager.rewards_contract() == random_address
    helpers.assert_single_event_named(
        "RewardsContractUpdated", 
        tx, 
        {"newRewardsContract": random_address}
    )


def test_stranger_can_not_replace_me_by_other_distributor(rewards_manager, stranger):
    with reverts("not permitted"):
        rewards_manager.replace_me_by_other_distributor(stranger, {"from": stranger})


def test_stranger_can_check_is_rewards_period_finished(rewards_manager, stranger):
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == True


def test_stranger_can_check_period_finish(rewards_manager, stranger):
    rewards_manager.is_rewards_period_finished({"from": stranger})


def test_rewards_contract_can_be_transferred(
    rewards_manager, 
    ldo_agent, 
    ldo_token, 
    rewards_contract_mock, 
    stranger,
    helpers
):
    reward = rewards_contract_mock.reward_data(ldo_token)
    assert reward[1] == rewards_manager
    tx = rewards_manager.replace_me_by_other_distributor(stranger, {"from": ldo_agent})
    reward = rewards_contract_mock.reward_data(ldo_token)
    assert reward[1] == stranger
    helpers.assert_single_event_named(
        "RewardsContractTransferred", 
        tx, 
        {"newDistributor": stranger}
    )


def test_start_reward_period_fails_on_zero_contract( 
    rewards_manager,
    ldo_agent,
    stranger
):
    rewards_manager.set_rewards_contract(ZERO_ADDRESS, {"from": ldo_agent})
    with reverts("manager: rewards disabled"):
        rewards_manager.start_next_rewards_period({"from": stranger})
    

def test_start_reward_period_fails_on_zero_balance( 
    rewards_manager,
    stranger
):
    with reverts("manager: low balance"):
        rewards_manager.start_next_rewards_period({"from": stranger})


def test_start_reward_period_fails_on_started_period( 
    rewards_manager,
    dao_treasury,
    stranger,
    ldo_token,
    helpers
):
    ldo_token.transfer(rewards_manager, 10**18, {"from": dao_treasury})
    tx = rewards_manager.start_next_rewards_period({"from": stranger})
    
    helpers.assert_single_event_named(
        "NewRewardsPeriodStarted", 
        tx, 
        {"amount": 0.25 * 10**18}
    )

    chain.sleep(rewards_period-10) 
    chain.mine()

    with reverts("manager: rewards period not finished"):
        rewards_manager.start_next_rewards_period({"from": stranger})


def test_notify_reward_amount_fails_on_low_balance(
    stranger, 
    rewards_manager,
    ldo_token,
    dao_treasury
):
    ldo_token.transfer(rewards_manager, 10**18 - 1, {"from": dao_treasury})
    with reverts("manager: low balance"):
        rewards_manager.start_next_rewards_period({"from": stranger})

import pytest

from brownie import reverts, ZERO_ADDRESS

random_address = "0xb842afd82d940ff5d8f6ef3399572592ebf182b0"

def test_init(balancer_wrapper, rewards_contract_mock, rewards_manager, ldo_agent):
    assert balancer_wrapper.owner() == ldo_agent
    assert balancer_wrapper.rewards_contract() == rewards_contract_mock
    assert balancer_wrapper.min_rewards_amount() == 10**18
    assert balancer_wrapper.weekly_amount() == 0
    assert balancer_wrapper.distributor() == rewards_manager


def test_stranger_can_not_transfer_ownership(balancer_wrapper, stranger):
    with reverts("not permitted"):
        balancer_wrapper.transfer_ownership(stranger, {"from": stranger})


def test_ownership_can_be_transferred(balancer_wrapper, ldo_agent, stranger, helpers):
    tx = balancer_wrapper.transfer_ownership(stranger, {"from": ldo_agent})
    assert balancer_wrapper.owner() == stranger
    helpers.assert_single_event_named(
        "OwnershipTransferred", 
        tx, 
        {"previousOwner": ldo_agent, "newOwner": stranger}
    )


def test_ownership_can_be_transferred_to_zero_address(balancer_wrapper, ldo_agent, helpers):
    tx = balancer_wrapper.transfer_ownership(ZERO_ADDRESS, {"from": ldo_agent})
    assert balancer_wrapper.owner() == ZERO_ADDRESS
    helpers.assert_single_event_named(
        "OwnershipTransferred", 
        tx, 
        {"previousOwner": ldo_agent, "newOwner": ZERO_ADDRESS}
    )


def test_stranger_can_not_set_rewards_contract(balancer_wrapper, stranger):
    assert balancer_wrapper.rewards_contract()   != ZERO_ADDRESS
    with reverts("not permitted"):
        balancer_wrapper.set_rewards_contract(ZERO_ADDRESS, {"from": stranger})


def test_owner_can_set_rewards_contract(balancer_wrapper, ldo_agent, helpers):
    assert balancer_wrapper.rewards_contract() != random_address
    tx = balancer_wrapper.set_rewards_contract(random_address, {"from": ldo_agent})
    assert balancer_wrapper.rewards_contract() == random_address
    helpers.assert_single_event_named(
        "RewardsContractUpdated", 
        tx, 
        {"newRewardsContract": random_address}
    )


def test_stranger_can_not_transfer_rewards_contract(balancer_wrapper, stranger):
    with reverts("not permitted"):
        balancer_wrapper.transfer_rewards_contract(stranger, {"from": stranger})


def test_stranger_can_not_set_min_rewards_amount(balancer_wrapper, stranger):
    with reverts("not permitted"):
        balancer_wrapper.set_min_rewards_amount(10*10**18, {"from": stranger})


def test_owner_can_set_min_rewards_amount(balancer_wrapper, ldo_agent, helpers):
    new_amount = 10*10**18
    assert balancer_wrapper.min_rewards_amount() != new_amount
    tx = balancer_wrapper.set_min_rewards_amount(new_amount, {"from": ldo_agent})
    assert balancer_wrapper.min_rewards_amount() == new_amount
    helpers.assert_single_event_named(
        "MinimalRewardsAmountUpdated", 
        tx, 
        {"newMinRewardsAmount": new_amount}
    )


def test_stranger_can_not_set_weekly_amount(balancer_wrapper, stranger):
    with reverts("not permitted"):
        balancer_wrapper.set_weekly_amount(10*10**18, {"from": stranger})


def test_owner_can_set_weekly_amount(balancer_wrapper, ldo_agent, helpers):
    new_amount = 10*10**18
    assert balancer_wrapper.weekly_amount() != new_amount
    tx = balancer_wrapper.set_weekly_amount(new_amount, {"from": ldo_agent})
    assert balancer_wrapper.weekly_amount() == new_amount
    helpers.assert_single_event_named(
        "WeeklyRewardsAmountUpdated", 
        tx, 
        {"newWeeklyRewardsAmount": new_amount}
    )


def test_stranger_can_not_set_distributor(balancer_wrapper, stranger):
    with reverts("not permitted"):
        balancer_wrapper.set_distributor(random_address, {"from": stranger})


def test_owner_can_set_distributor(balancer_wrapper, ldo_agent, helpers):
    assert balancer_wrapper.distributor != random_address
    tx = balancer_wrapper.set_distributor(random_address, {"from": ldo_agent})
    assert balancer_wrapper.distributor() == random_address
    helpers.assert_single_event_named(
        "DistributorUpdated", 
        tx, 
        {"newDistributor": random_address}
    )


def test_stranger_can_check_is_rewards_period_finished(balancer_wrapper, stranger):
    assert balancer_wrapper.is_rewards_period_finished({"from": stranger}) == True


def test_stranger_can_check_period_finish(balancer_wrapper, stranger):
    balancer_wrapper.is_rewards_period_finished({"from": stranger})


def test_rewards_contract_can_be_transferred(
    balancer_wrapper, 
    ldo_agent, 
    ldo_token, 
    rewards_contract_mock, 
    stranger,
    helpers
):
    reward = rewards_contract_mock.reward_data(ldo_token)
    assert reward[1] == balancer_wrapper
    print(balancer_wrapper.owner())
    tx = balancer_wrapper.transfer_rewards_contract(stranger, {"from": ldo_agent})
    reward = rewards_contract_mock.reward_data(ldo_token)
    assert reward[1] == stranger
    helpers.assert_single_event_named(
        "RewardsContractTransfered", 
        tx, 
        {"newDistributor": stranger}
    )


def test_start_reward_period_fails_on_zero_contract( 
    balancer_wrapper,
    ldo_agent,
    stranger
):
    balancer_wrapper.set_rewards_contract(ZERO_ADDRESS, {"from": ldo_agent})
    with reverts("manager: rewards disabled"):
        balancer_wrapper.start_next_rewards_period({"from": stranger})
    

def test_start_reward_period_fails_on_zero_balance( 
    balancer_wrapper,
    stranger
):
    with reverts("manager: rewards disabled"):
        balancer_wrapper.start_next_rewards_period({"from": stranger})


def test_start_reward_period_fails_on_low_balance( 
    balancer_wrapper,
    ldo_agent,
    stranger
):
    balancer_wrapper.set_weekly_amount(10*18, {"from": ldo_agent})
    with reverts("manager: low balance"):
        balancer_wrapper.start_next_rewards_period({"from": stranger})


def test_start_reward_period_fails_on_started_period( 
    balancer_wrapper,
    dao_treasury,
    ldo_agent,
    stranger,
    ldo_token
):
    balancer_wrapper.set_weekly_amount(10**18, {"from": ldo_agent})
    ldo_token.transfer(balancer_wrapper, 10**18, {"from": dao_treasury})
    balancer_wrapper.start_next_rewards_period({"from": stranger})
    with reverts("manager: low balance"):
        balancer_wrapper.start_next_rewards_period({"from": stranger})


def test_notify_reward_amount_faild_on_stranger(balancer_wrapper, stranger):
    with reverts("not permitted"):
        balancer_wrapper.notifyRewardAmount(10**18, stranger, {"from": stranger})


def test_notify_reward_amount_fails_on_low_balance(
    stranger, 
    rewards_manager,
    ldo_token,
    dao_treasury
):
    ldo_token.transfer(rewards_manager, 10**18 - 1, {"from": dao_treasury})
    with reverts("manager: low balance"):
        rewards_manager.start_next_rewards_period({"from": stranger})

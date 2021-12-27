import pytest
from brownie import chain, reverts, Wei, ZERO_ADDRESS
from brownie.network.state import Chain

rewards_period = 3600 * 24 * 7
random_address = "0xb842afd82d940ff5d8f6ef3399572592ebf182b0"


def test_owner_is_deployer(rewards_manager, ldo_agent):
    assert rewards_manager.owner() == ldo_agent


def test_stranger_can_not_transfer_ownership(rewards_manager, stranger):
    with reverts("not permitted"):
        rewards_manager.transfer_ownership(stranger, {"from": stranger})


def test_ownership_can_be_transferred(rewards_manager, ldo_agent, stranger):
    rewards_manager.transfer_ownership(stranger, {"from": ldo_agent})
    assert rewards_manager.owner() == stranger


def test_ownership_can_be_transferred_to_zero_address(rewards_manager, ldo_agent):
    rewards_manager.transfer_ownership(ZERO_ADDRESS, {"from": ldo_agent})
    assert rewards_manager.owner() == ZERO_ADDRESS


def test_stranger_can_not_set_rewards_contract(rewards_manager, stranger):
    assert rewards_manager.rewards_contract != ZERO_ADDRESS
    with reverts("not permitted"):
        rewards_manager.set_rewards_contract(ZERO_ADDRESS, {"from": stranger})


def test_owner_can_set_rewards_contract(rewards_manager, ldo_agent):
    assert rewards_manager.rewards_contract != random_address
    rewards_manager.set_rewards_contract(random_address, {"from": ldo_agent})
    assert rewards_manager.rewards_contract() == random_address


def test_owner_can_set_rewards_contract_to_zero_address(rewards_manager, ldo_agent):
    assert rewards_manager.rewards_contract != ZERO_ADDRESS
    rewards_manager.set_rewards_contract(ZERO_ADDRESS, {"from": ldo_agent})
    assert rewards_manager.rewards_contract() == ZERO_ADDRESS


def test_stranger_can_not_recover_erc20(rewards_manager, ldo_token, stranger):
    with reverts("not permitted"):
        rewards_manager.recover_erc20(ldo_token, 0, {"from": stranger})


def test_owner_recovers_erc20(rewards_manager, ldo_token, ldo_agent):
    assert ldo_token.balanceOf(rewards_manager) == 0

    rewards_amount = Wei("1 ether")
    ldo_token.transfer(rewards_manager, rewards_amount, {"from": ldo_agent})
    assert ldo_token.balanceOf(rewards_manager) == rewards_amount

    rewards_manager.recover_erc20(ldo_token, rewards_amount // 2, {"from": ldo_agent})
    assert ldo_token.balanceOf(rewards_manager) == rewards_amount // 2


def test_stranger_can_check_is_rewards_period_finished(rewards_manager, stranger):
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == True


def test_stranger_can_not_start_next_rewards_period_without_rewards_contract_set(
    rewards_manager, stranger
):
    with reverts("manager: rewards disabled"):
        rewards_manager.start_next_rewards_period({"from": stranger})


def test_stranger_can_not_start_next_rewards_period_with_zero_amount(
    rewards_manager, stranger
):
    with reverts("manager: rewards disabled"):
        rewards_manager.start_next_rewards_period({"from": stranger})


def test_stranger_starts_next_rewards_period(
    rewards_manager, ldo_token, ldo_agent, stranger
):
    rewards_amount = Wei("1 ether")
    ldo_token.transfer(rewards_manager, rewards_amount, {"from": ldo_agent})
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == True
    rewards_manager.start_next_rewards_period({"from": stranger})
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == False


def test_stranger_can_not_start_next_rewards_period_while_current_is_active(
    rewards_manager, ldo_token, ldo_agent, stranger
):
    rewards_amount = Wei("1 ether")
    ldo_token.transfer(rewards_manager, rewards_amount, {"from": ldo_agent})
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == True
    rewards_manager.start_next_rewards_period({"from": stranger})
    chain = Chain()
    chain.sleep(1)
    chain.mine()

    ldo_token.transfer(rewards_manager, rewards_amount, {"from": ldo_agent})
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == False
    with reverts("manager: rewards period not finished"):
        rewards_manager.start_next_rewards_period({"from": stranger})


def test_stranger_can_start_next_rewards_period_after_current_is_finished(
    rewards_manager, ldo_token, ldo_agent, stranger
):
    rewards_amount = Wei("1 ether")
    ldo_token.transfer(rewards_manager, rewards_amount, {"from": ldo_agent})
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == True
    rewards_manager.start_next_rewards_period({"from": stranger})
    chain = Chain()
    chain.sleep(rewards_period*4)
    chain.mine()

    ldo_token.transfer(rewards_manager, rewards_amount, {"from": ldo_agent})
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == True
    rewards_manager.start_next_rewards_period({"from": stranger})
    assert rewards_manager.is_rewards_period_finished({"from": stranger}) == False

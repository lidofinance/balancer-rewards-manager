import pytest
import brownie


def test_owner_recovers_erc20_with_zero_amount(
    rewards_manager, ldo_token, ldo_agent, dao_treasury
):
    rewards_amount = brownie.Wei("1 ether")
    ldo_token.transfer(rewards_manager, rewards_amount, {"from": dao_treasury})
    balance_before = ldo_token.balanceOf(ldo_agent)
    tx = rewards_manager.recover_erc20(ldo_token, 0, {"from": ldo_agent})
    assert len(tx.events) == 0

    balance_after = ldo_token.balanceOf(ldo_agent)
    assert balance_before == balance_after
    assert ldo_token.balanceOf(rewards_manager) == rewards_amount


def test_owner_recovers_erc20_with_balance(
    rewards_manager, ldo_token, ldo_agent, stranger, helpers
):
    recipient = stranger
    transfer_amount = brownie.Wei("1 ether")
    recover_amount = brownie.Wei("0.5 ether")
    ldo_token.transfer(rewards_manager, transfer_amount, {"from": ldo_agent})
    assert ldo_token.balanceOf(rewards_manager) == transfer_amount

    recipient_balance_before = ldo_token.balanceOf(recipient)
    tx = rewards_manager.recover_erc20(
        ldo_token, recover_amount, recipient, {"from": ldo_agent}
    )
    recipient_balance_after = ldo_token.balanceOf(recipient)

    assert ldo_token.balanceOf(rewards_manager) == transfer_amount - recover_amount
    assert recipient_balance_after - recipient_balance_before == recover_amount


def test_owner_recovers_erc20_to_the_caller_by_default(
    rewards_manager, ldo_token, ldo_agent, helpers
):
    transfer_amount = brownie.Wei("1 ether")
    ldo_token.transfer(rewards_manager, transfer_amount, {"from": ldo_agent})

    recipient_balance_before = ldo_token.balanceOf(ldo_agent)
    tx = rewards_manager.recover_erc20(ldo_token, transfer_amount, {"from": ldo_agent})
    recipient_balance_after = ldo_token.balanceOf(ldo_agent)

    assert ldo_token.balanceOf(rewards_manager) == 0
    assert recipient_balance_after - recipient_balance_before == transfer_amount



def test_recover_erc20_not_enough_balance(rewards_manager, ldo_token, ldo_agent):
    transfer_amount = brownie.Wei("1 ether")
    recover_amount = brownie.Wei("2 ether")
    ldo_token.transfer(rewards_manager, transfer_amount, {"from": ldo_agent})

    with brownie.reverts("token transfer failed"):
        rewards_manager.recover_erc20(ldo_token, recover_amount, {"from": ldo_agent})
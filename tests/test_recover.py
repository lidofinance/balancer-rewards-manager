import pytest
from brownie import Wei, reverts, interface
from utils.config import (
    lido_dao_agent_address,
    ldo_token_address,
    lido_dao_voting_address,
    lido_dao_token_manager_address
)
from utils.evm_script import encode_call_script
from utils.voting import create_vote


def test_owner_recovers_erc20_with_zero_amount(
    rewards_manager, ldo_token, ldo_agent, dao_treasury
):
    rewards_amount = Wei("1 ether")
    ldo_token.transfer(rewards_manager, rewards_amount, {"from": dao_treasury})
    balance_before = ldo_token.balanceOf(ldo_agent)
    tx = rewards_manager.recover_erc20(ldo_token, 0, {"from": ldo_agent})
    assert len(tx.events) == 0

    balance_after = ldo_token.balanceOf(ldo_agent)
    assert balance_before == balance_after
    assert ldo_token.balanceOf(rewards_manager) == rewards_amount


def test_owner_recovers_erc20_with_balance(
    rewards_manager, ldo_token, ldo_agent, stranger
):
    recipient = stranger
    transfer_amount = Wei("1 ether")
    recover_amount = Wei("0.5 ether")
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
    rewards_manager, ldo_token, ldo_agent
):
    transfer_amount = Wei("1 ether")
    ldo_token.transfer(rewards_manager, transfer_amount, {"from": ldo_agent})

    recipient_balance_before = ldo_token.balanceOf(ldo_agent)
    tx = rewards_manager.recover_erc20(ldo_token, transfer_amount, {"from": ldo_agent})
    recipient_balance_after = ldo_token.balanceOf(ldo_agent)

    assert ldo_token.balanceOf(rewards_manager) == 0
    assert recipient_balance_after - recipient_balance_before == transfer_amount


def test_recover_erc20_not_enough_balance(rewards_manager, ldo_token, ldo_agent):
    transfer_amount = Wei("1 ether")
    recover_amount = Wei("2 ether")
    ldo_token.transfer(rewards_manager, transfer_amount, {"from": ldo_agent})

    with reverts("token transfer failed"):
        rewards_manager.recover_erc20(ldo_token, recover_amount, {"from": ldo_agent})


def test_erc_20_recover_via_voting(
    ldo_holder, 
    rewards_manager, 
    dao_treasury, 
    helpers, 
    accounts, 
    dao_voting, 
    ldo_token, 
    stranger
    ):
    
    agent_contract = interface.Agent(lido_dao_agent_address)
    ldo_token.transfer(rewards_manager, 10**18, {"from": dao_treasury})

    balance = ldo_token.balanceOf(rewards_manager)
    assert balance > 0

    encoded_recover_calldata = rewards_manager.recover_erc20.encode_input(ldo_token_address, balance, stranger)
    recover_script = encode_call_script([(rewards_manager.address, encoded_recover_calldata)])
    forwrded_script = encode_call_script([(lido_dao_agent_address, agent_contract.forward.encode_input(recover_script))])
    
    (vote_id, _) = create_vote(
        voting=interface.Voting(lido_dao_voting_address),
        token_manager=interface.TokenManager(lido_dao_token_manager_address),
        vote_desc='',
        evm_script=forwrded_script,
        tx_params={"from": ldo_holder})
    
    helpers.execute_vote(vote_id=vote_id,
                         accounts=accounts,
                         dao_voting=dao_voting)
    
    assert ldo_token.balanceOf(rewards_manager) == 0
    assert ldo_token.balanceOf(stranger) == balance

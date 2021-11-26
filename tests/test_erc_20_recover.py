import pytest

from brownie import interface, Contract

from utils.voting import create_vote
from utils.config import (lido_dao_voting_address,
                          lido_dao_agent_address,
                          balancer_deployed_manager,
                          lido_dao_token_manager_address,
                          ldo_token_address)
from utils.evm_script import encode_call_script

def test_erc_20_recover_via_voting(
    ldo_holder, 
    rewards_contract, 
    dao_treasury, 
    helpers, 
    accounts, 
    dao_voting, 
    ldo_token, 
    stranger
    ):
    
    agent_contract = interface.Agent(lido_dao_agent_address)
    ldo_token.transfer(rewards_contract, 10**18, {"from": dao_treasury})

    balance = ldo_token.balanceOf(rewards_contract)
    assert balance > 0

    encoded_recover_calldata = rewards_contract.recover_erc20.encode_input(ldo_token_address, balance, stranger)
    recover_script = encode_call_script([(rewards_contract.address, encoded_recover_calldata)])
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
    
    assert ldo_token.balanceOf(rewards_contract) == 0
    assert ldo_token.balanceOf(stranger) == balance

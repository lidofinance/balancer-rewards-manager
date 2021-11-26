import pytest
from brownie import chain
from math import floor

rewards_limit = 25 * 1000 * 10**18
rewards_period = 3600 * 24 * 7
amount = 300_000 * 10**18

@pytest.mark.parametrize(
    'period', 
    [   
        floor(0.5*rewards_period), 
        rewards_period,
        2*rewards_period , 
        3*rewards_period , 
        4*rewards_period , 
        4*rewards_period + 1, 
        4*rewards_period - 1,
        5*rewards_period
    ]
)
def test_out_of_funding_date(rewards_contract, rewards_manager, dao_treasury, period, ldo_token, stranger):

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    assert ldo_token.balanceOf(rewards_manager) == amount
    rewards_manager.start_next_rewards_period({"from": stranger})

    period_finish = rewards_contract.last_accounted_period_start_date() + rewards_period * 4

    chain.sleep(period)
    chain.mine()

    assert rewards_contract.periodFinish() == period_finish

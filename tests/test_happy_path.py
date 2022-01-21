import pytest
import time
from datetime import datetime
from brownie import reverts, chain
from scripts.deploy import deploy_manager_and_reward_contract
from math import floor
from utils.config import steth_token_address

rewards_limit = 75 * 1000 * 10**18
rewards_period = 3600 * 24 * 7
amount = 300_000 * 10**18

def test_happy_path(
    balancer_distributor, 
    ldo_token, 
    dao_treasury, 
    deployer,
    stranger,
    program_start_date
    ):

    (rewards_manager, rewards_contract) = deploy_manager_and_reward_contract(balancer_distributor, program_start_date, {"from": deployer})

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})

    rewards_manager.start_next_rewards_period({"from": stranger})
    
    assert rewards_contract.available_allowance() == 0

    chain.sleep(program_start_date - chain.time() - 1) 
    chain.mine()

    assert rewards_contract.available_allowance() == 0

    chain.sleep(2) 
    chain.mine()

    assert rewards_contract.available_allowance() == rewards_limit

    with reverts('manager: not enough amount approved'):
        rewards_contract.createDistribution(ldo_token, '', rewards_limit + 1, 0, {"from": balancer_distributor})
    with reverts('manager: only LDO distribution allowed'):
        rewards_contract.createDistribution(steth_token_address, '', rewards_limit, 0, {"from": balancer_distributor})
    rewards_contract.createDistribution(ldo_token, '', rewards_limit, 0, {"from": balancer_distributor})

    assert ldo_token.balanceOf(rewards_contract) == amount - rewards_limit
    assert rewards_contract.available_allowance() == 0

    chain.sleep(rewards_period)
    chain.mine()
    
    assert rewards_contract.available_allowance() == rewards_limit

    chain.sleep(2*rewards_period)
    chain.mine()

    assert rewards_manager.is_rewards_period_finished() == True
    assert rewards_contract.available_allowance() == 3 * rewards_limit

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    rewards_manager.start_next_rewards_period({"from": stranger})
    assert rewards_contract.available_allowance() == 3 * rewards_limit

    chain.sleep(4*rewards_period)
    chain.mine()

    assert rewards_contract.available_allowance() == 7 * rewards_limit

    chain.sleep(2*rewards_period)
    chain.mine()

    assert rewards_contract.available_allowance() == 7 * rewards_limit

    ldo_token.transfer(rewards_manager, amount, {"from": dao_treasury})
    rewards_manager.start_next_rewards_period({"from": stranger})

    assert rewards_contract.available_allowance() == 7 * rewards_limit

    chain.sleep(rewards_period)
    chain.mine()
    assert rewards_contract.available_allowance() == 8 * rewards_limit

def test_happy_path_with_dates(
    balancer_distributor, 
    ldo_token, 
    dao_treasury, 
    deployer,
    stranger,
    easytrack_contract,
    rewards_multisig
):

    program_start_date = 1643587200 # Mon Jan 31 2022 00:00:00 GMT+0000
    deploy_date = 1642932000 # Sun Jan 23 2022 10:00:00 GMT+0000
    start_new_reward_period_date = 1643709600 # Tue Feb 01 2022 10:00:00 GMT+0000
    balancer_first_distribution_date = 1644314400 # Tue Feb 08 2022 10:00:00 GMT+0000
    
    chain.sleep(deploy_date - chain.time()) 
    chain.mine()
    print('Waiting deploy date', datetime.fromtimestamp(chain.time()))

    (rewards_manager, rewards_contract) = deploy_manager_and_reward_contract(balancer_distributor, program_start_date, {"from": deployer})

    add_program_motion_calldata =  '0x000000000000000000000000' + rewards_manager.address.lower()[2:] + '00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000025537573686953776170204c502072657761726473204d616e6167657220436f6e7472616374000000000000000000000000000000000000000000000000000000'

    tx = easytrack_contract.createMotion(
        '0x9D15032b91d01d5c1D940eb919461426AB0dD4e3', 
        add_program_motion_calldata,
        {"from": rewards_multisig}
    )
    motion_id = tx.events['MotionCreated']['_motionId']

    chain.sleep(3600*72) # waiting motion 
    chain.mine()
    print('add program motion enact date: ', datetime.fromtimestamp(chain.time()))

    easytrack_contract.enactMotion(
        motion_id,
        add_program_motion_calldata,
        {"from": rewards_multisig}
    )

    topup_program_motion_calldata = '0x000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000' + rewards_manager.address.lower()[2:] + '0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000003f870857a3e0e3800000'

    print(topup_program_motion_calldata);
    easytrack_contract.createMotion(
        '0x77781A93C4824d2299a38AC8bBB11eb3cd6Bc3B7',
        topup_program_motion_calldata, 
        {"from": rewards_multisig}
    )
    
    chain.sleep(3600*72) # waiting motion 
    chain.mine()
    print('topup program motion enact date: ', datetime.fromtimestamp(chain.time()))

    easytrack_contract.enactMotion(
        motion_id + 1,
        topup_program_motion_calldata,
        {"from": rewards_multisig}
    )

    assert ldo_token.balanceOf(rewards_manager) == 300_000 * 10**18

    chain.sleep(start_new_reward_period_date - chain.time()) 
    chain.mine()
    print('Waiting start program date: ', datetime.fromtimestamp(chain.time()))

    rewards_manager.start_next_rewards_period({"from": stranger})
    
    assert rewards_contract.available_allowance() == rewards_limit
    
    for i in range(3): 

        chain.sleep(balancer_first_distribution_date + i * rewards_period - chain.time()) 
        chain.mine()

        print('Balancer creates distibution: ', datetime.fromtimestamp(chain.time()))
        balance_before_distribution = ldo_token.balanceOf(rewards_contract)

        assert rewards_contract.available_allowance() == 2 * rewards_limit

        rewards_contract.createDistribution(ldo_token, '', rewards_limit, i, {"from": balancer_distributor})

        assert ldo_token.balanceOf(rewards_contract) == balance_before_distribution - rewards_limit
        assert rewards_contract.available_allowance() == rewards_limit
    
    
    easytrack_contract.createMotion(
        '0x77781A93C4824d2299a38AC8bBB11eb3cd6Bc3B7',
        topup_program_motion_calldata, 
        {"from": rewards_multisig}
    )
    
    chain.sleep(3600*72) # waiting motion 
    chain.mine()
    print('topup program motion enact date: ', datetime.fromtimestamp(chain.time()))

    easytrack_contract.enactMotion(
        motion_id + 2,
        topup_program_motion_calldata,
        {"from": rewards_multisig}
    )

    rewards_manager.start_next_rewards_period({"from": stranger})

    
    chain.sleep(1646136000 - chain.time()) # Tue Mar 01 2022 12:00:00 GMT+0000
    chain.mine()

    for i in range(4): 
        print('Balancer creates distibution: ', datetime.fromtimestamp(chain.time()))
        balance_before_distribution = ldo_token.balanceOf(rewards_contract)

        assert rewards_contract.available_allowance() == 2 * rewards_limit

        rewards_contract.createDistribution(ldo_token, '', rewards_limit, i + 3, {"from": balancer_distributor})

        assert ldo_token.balanceOf(rewards_contract) == balance_before_distribution - rewards_limit
        assert rewards_contract.available_allowance() == rewards_limit
        
        chain.sleep(rewards_period)
        chain.mine()
    
    print('Balancer creates distibution: ', datetime.fromtimestamp(chain.time()))
    balance_before_distribution = ldo_token.balanceOf(rewards_contract)

    assert rewards_contract.available_allowance() == rewards_limit

    rewards_contract.createDistribution(ldo_token, '', rewards_limit, 7, {"from": balancer_distributor})

    assert ldo_token.balanceOf(rewards_contract) == balance_before_distribution - rewards_limit
    assert rewards_contract.available_allowance() == 0
    
    chain.sleep(rewards_period)
    chain.mine()

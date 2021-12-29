import sys
import time
from brownie import (
    BalancerRewardsController,
    RewardsManager
)
from utils.config import (
    lido_dao_agent_address,
    get_is_live,
    get_deployer_account,
    prompt_bool,
    get_env
)


def main():
    is_live = get_is_live()
    deployer = get_deployer_account(is_live)
    balancer_distributor = get_env('BALANCER_DISTRIBUTOR')
    owner = get_env('OWNER')
    start_date = get_env('START_DATE')

    print('Deployer:', deployer)
    print('Balancer Distributor:', balancer_distributor)
    print('Owner:', owner)
    print(
        'Program start date:', 
        time.ctime(int(start_date))
    )

    sys.stdout.write('Proceed? [y/n]: ')

    if not prompt_bool():
        print('Aborting')
        return

    (manager_contract, rewards_contract) = deploy_manager_and_reward_contract(
        balancer_distributor,
        start_date,
        tx_params={"from": deployer, "priority_fee": "4 gwei"}
    )

    print('Manager contract: ', manager_contract)
    print('Rewards contract: ', rewards_contract)


def deploy_manager_and_reward_contract(balancer_distributor, start_date, tx_params):
    rewarder_contract = RewardsManager.deploy(tx_params)
    rewards_contract =  BalancerRewardsController.deploy(
        balancer_distributor, # _balancer_distributor
        rewarder_contract, # rewards_manager
        start_date,
        tx_params,
        publish_source=False,
    )
    rewarder_contract.set_rewards_contract(rewards_contract, tx_params)
    
    rewards_contract.transfer_ownership(lido_dao_agent_address, tx_params)
    rewarder_contract.transfer_ownership(lido_dao_agent_address, tx_params)

    return (rewarder_contract, rewards_contract)
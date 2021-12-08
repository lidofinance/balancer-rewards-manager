import sys
import time
from brownie import BalancerRewardsController
from utils.config import (
    ldo_token_address,
    lido_dao_agent_address,
    get_is_live,
    get_deployer_account,
    prompt_bool,
    get_env
)
from utils import deployment


def main():
    is_live = get_is_live()
    deployer = get_deployer_account(is_live)
    allocator = get_env('ALLOCATOR')
    owner = get_env('OWNER')
    start_date = get_env('START_DATE')
    initializer = get_env('INITIALIZER')

    print('Deployer:', deployer)
    print('Allocator:', allocator)
    print('Initializer:', initializer)
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
        allocator,
        initializer,
        tx_params={"from": deployer, "priority_fee": "4 gwei"}
    )

    print('Manager contract: ', manager_contract)
    print('Rewards contract: ', rewards_contract)


def deploy_manager_and_reward_contract(allocator, initializer, tx_params):
    rewarder_contract = deployment.deploy_rewarder_contract(tx_params=tx_params)
    rewards_contract =  BalancerRewardsController.deploy(
        allocator, # _allocator
        rewarder_contract, # distributor
        initializer, # _initializer
        tx_params,
        publish_source=False,
    )
    rewarder_contract.set_rewards_contract(rewards_contract, tx_params)
    
    rewards_contract.transfer_ownership(lido_dao_agent_address, tx_params)
    rewarder_contract.transfer_ownership(lido_dao_agent_address, tx_params)

    return (rewarder_contract, rewards_contract)
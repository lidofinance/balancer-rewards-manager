import sys
from brownie import RewardsManager

from utils.config import (
    lido_dao_agent_address,
    balancer_rewards_contract,
    min_rewards_amount,
    get_is_live,
    get_deployer_account,
    prompt_bool
)


def main():
    is_live = get_is_live()
    deployer = get_deployer_account(is_live)

    print(f'Deployer: {deployer}')
    print(f'REWARDS CONTRACT: {balancer_rewards_contract}')
    print(f'OWNER: {lido_dao_agent_address}')
    print(f'MINIMAL REWARDS AMOUNT: {min_rewards_amount}')
    sys.stdout.write('Proceed? [y/n]: ')

    if not prompt_bool():
        print('Aborting')
        return
    
    tx_params={"from": deployer, "priority_fee": "2 gwei"}
    if not is_live: del tx_params["priority_fee"]

    manager_contract = RewardsManager.deploy(
        lido_dao_agent_address,
        min_rewards_amount,
        balancer_rewards_contract,
        tx_params
    )

    print('Manager contract: ', manager_contract)

def deploy_manager(balancer_rewards_contract, min_rewards_amount, tx_params):
    return RewardsManager.deploy(
        lido_dao_agent_address,
        min_rewards_amount,
        balancer_rewards_contract,
        tx_params
    )

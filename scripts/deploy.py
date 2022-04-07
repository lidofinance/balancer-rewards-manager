import sys
from brownie import (
    RewardsManager
)
from utils.config import (
    lido_dao_agent_address,
    balancer_rewards_contract,
    get_is_live,
    get_deployer_account,
    prompt_bool,
    get_env
)


def main():
    is_live = get_is_live()
    deployer = get_deployer_account(is_live)

    print('Deployer:', deployer)
    print('REWARDS_CONTRACT:', balancer_rewards_contract)
    sys.stdout.write('Proceed? [y/n]: ')

    if not prompt_bool():
        print('Aborting')
        return

    manager_contract = deploy_manager(
        balancer_rewards_contract,
        tx_params={"from": deployer, "priority_fee": "2 gwei"}
    )

    print('Manager contract: ', manager_contract)


def deploy_manager(balancer_rewards_contract, tx_params):
    manager_contract = RewardsManager.deploy(tx_params)
    manager_contract.set_rewards_contract(balancer_rewards_contract, tx_params)
    manager_contract.transfer_ownership(lido_dao_agent_address, tx_params)

    return manager_contract
from brownie import (
    config,
    ZERO_ADDRESS,
    project,
)
from pathlib import Path

REWARDS_MANAGER_DEPENDENCY_NAME = "lidofinance/staking-rewards-sushi@0.1.0"


def deploy_rewarder_contract(tx_params):
    RewardsManager = DependencyLoader.load(
        REWARDS_MANAGER_DEPENDENCY_NAME, "RewardsManager"
    )
    return RewardsManager.deploy(tx_params)

class DependencyLoader(object):
    dependencies = {}

    @staticmethod
    def load(dependency_name, contract_name):
        if dependency_name not in DependencyLoader.dependencies:
            dependency_index = config["dependencies"].index(dependency_name)
            DependencyLoader.dependencies[dependency_name] = project.load(
                Path.home()
                / ".brownie"
                / "packages"
                / config["dependencies"][dependency_index]
            )
        return getattr(DependencyLoader.dependencies[dependency_name], contract_name)
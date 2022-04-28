import time
import pytest
from brownie import chain, accounts, BalancerLiquidityGaugeMock, RewardsManager
from utils.config import lido_dao_voting_address, balancer_rewards_contract

from utils.config import (
    ldo_token_address,
    lido_dao_agent_address
)


@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass


@pytest.fixture(scope='module')
def deployer(accounts):
    return accounts[0]


@pytest.fixture(scope='module')
def stranger(accounts):
    return accounts[9]


@pytest.fixture(scope='module')
def ldo_holder(accounts, ldo_token, dao_treasury):
    ldo_token.transfer(accounts[7], 10**18, {"from": dao_treasury})
    return accounts[7]


@pytest.fixture(scope='module')
def dao_voting(interface):
    return interface.Voting(lido_dao_voting_address)


@pytest.fixture(scope='module')
def ldo_token(interface):
    return interface.ERC20(ldo_token_address)


@pytest.fixture(scope='module')
def ldo_agent():
    return accounts.at(lido_dao_agent_address, force = True)


@pytest.fixture(scope='module')
def dao_treasury():
    return accounts.at('0x3e40d73eb977dc6a537af587d48316fee66e9c8c', force = True)


@pytest.fixture(scope='module')
def rewards_contract_mock(deployer):
    return BalancerLiquidityGaugeMock.deploy(deployer, ldo_token_address, {"from": deployer})


@pytest.fixture(scope='module')
def rewards_contract(interface):
    return interface.BalancerLiquidityGauge(balancer_rewards_contract)


@pytest.fixture(scope='module')
def balancer_admin(accounts):
    return accounts.at('0x8f42adbba1b16eaae3bb5754915e0d06059add75', force = True)


@pytest.fixture(scope='module')
def rewards_manager(rewards_contract_mock, ldo_agent, deployer, ldo_token):
    manager = RewardsManager.deploy(
        ldo_agent,
        10**18,
        rewards_contract_mock,
        {"from": deployer}
    )
    rewards_contract_mock.set_reward_distributor(ldo_token, manager, {"from": deployer})
    return manager


@pytest.fixture(scope='module')
def easytrack_contract(interface):
    return interface.EasyTrack('0xF0211b7660680B49De1A7E9f25C65660F0a13Fea')


@pytest.fixture(scope='module')
def rewards_multisig(accounts):
    return accounts.at('0x87d93d9b2c672bf9c9642d853a8682546a5012b5',force=True)


@pytest.fixture(scope='module')
def usdt_holder(accounts):
    return accounts.at('0x5754284f345afc66a98fbb0a0afe71e0f007b949',force=True)


@pytest.fixture(scope='module')
def usdt_token(interface):
    return interface.ERC20('0xdAC17F958D2ee523a2206206994597C13D831ec7')


class Helpers:
    @staticmethod
    def filter_events_from(addr, events):
      return list(filter(lambda evt: evt.address == addr, events))

    @staticmethod
    def assert_single_event_named(evt_name, tx, evt_keys_dict):
      receiver_events = Helpers.filter_events_from(tx.receiver, tx.events[evt_name])
      assert len(receiver_events) == 1
      assert dict(receiver_events[0]) == evt_keys_dict

    @staticmethod
    def execute_vote(accounts, vote_id, dao_voting):
        ldo_holders = [
            '0x3e40d73eb977dc6a537af587d48316fee66e9c8c',
            '0xb8d83908aab38a159f3da47a59d84db8e1838712',
            '0xa2dfc431297aee387c05beef507e5335e684fbcd'
        ]

        for holder_addr in ldo_holders:
            print('voting from acct:', holder_addr)
            accounts[0].transfer(holder_addr, '0.1 ether')
            account = accounts.at(holder_addr, force=True)
            dao_voting.vote(vote_id, True, False, {'from': account})

        # wait for the vote to end
        chain.sleep(3 * 60 * 60 * 24)
        chain.mine()

        assert dao_voting.canExecute(vote_id)
        dao_voting.executeVote(vote_id, {'from': accounts[0]})

        print(f'vote executed')

    @staticmethod
    def assert_no_events_named(evt_name, tx):
        assert evt_name not in tx.events

@pytest.fixture(scope='module')
def helpers():
    return Helpers

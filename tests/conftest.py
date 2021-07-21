import pytest
from brownie import MerkleMock, chain, accounts
from scripts.deploy import deploy_manager


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
def balancer_allocator(accounts):
    return accounts[1]


@pytest.fixture(scope='module')
def stranger(accounts):
    return accounts[9]


@pytest.fixture(scope='module')
def ldo_token(interface):
    return interface.ERC20(ldo_token_address)


@pytest.fixture(scope='module')
def ldo_agent(interface):
    return interface.ERC20(lido_dao_agent_address)


@pytest.fixture(scope='module')
def dao_treasury(deployer, ldo_token):
    return accounts.at('0x3e40d73eb977dc6a537af587d48316fee66e9c8c', force = True)


@pytest.fixture(scope='module')
def rewards_manager(deployer, balancer_allocator, ldo_agent, interface):
    manager_contract = deploy_manager(ldo_agent, balancer_allocator, {"from": deployer})
    merkle_owner = interface.MerkleRedeem('0x6bd0B17713aaa29A2d7c9A39dDc120114f9fD809').owner()
    if merkle_owner != manager_contract:
        interface.MerkleRedeem('0x6bd0B17713aaa29A2d7c9A39dDc120114f9fD809')\
            .transferOwnership(manager_contract, {"from": merkle_owner})

    return manager_contract


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

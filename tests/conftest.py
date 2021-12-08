import time
import pytest
from brownie import chain, accounts
from scripts.deploy import deploy_manager_and_reward_contract
from utils.config import lido_dao_voting_address


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
def ape(accounts):
    return accounts[0]


@pytest.fixture(scope='module')
def balancer_allocator(accounts):
    return accounts.at('0xadda10ac6195d272543c6ed3a4a0d7fdd25aa4fa',force=True)


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
def ldo_agent(interface):
    return interface.ERC20(lido_dao_agent_address)


@pytest.fixture(scope='module')
def dao_treasury():
    return accounts.at('0x3e40d73eb977dc6a537af587d48316fee66e9c8c', force = True)


@pytest.fixture(scope='module')
def program_start_date():
    begining_of_the_day = int(time.time()/86400)*86400
    return begining_of_the_day + 604800


@pytest.fixture(scope='module')
def merkle_contract(interface):
    return interface.MerkleOrchard('0xdAE7e32ADc5d490a43cCba1f0c736033F2b4eFca')


@pytest.fixture(scope='module')
def rewarder(deployer, balancer_allocator):
    return deploy_manager_and_reward_contract(balancer_allocator, {"from": deployer})


@pytest.fixture(scope='module')
def rewards_manager(rewarder):
    return rewarder[0]


@pytest.fixture(scope='module')
def rewards_contract(rewarder):
    return rewarder[1]


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

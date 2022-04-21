import os
import sys
from brownie import network, accounts

ldo_token_address = '0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32'
lido_dao_agent_address = '0x3e40D73EB977Dc6a537aF587D48316feE66E9C8c'
lido_dao_voting_address = '0x2e59A20f205bB85a89C53f1936454680651E618e'
lido_dao_token_manager_address = '0xf73a1260d222f447210581DDf212D915c09a3249'
steth_token_address = '0xae7ab96520de3a18e5e111b5eaab095312d7fe84'
balancer_rewards_contract = '0xcD4722B7c24C29e0413BDCd9e51404B4539D14aE'

min_rewards_amount = 5000 * 10**18


def get_is_live():
    return network.show_active() != 'development'


def get_env(name, is_required=True, message=None, default=None):
    if name not in os.environ:
        if is_required:
            raise EnvironmentError(message or f'Please set {name} env variable')
        else:
            return default
    return os.environ[name]


def get_deployer_account(is_live):
    if is_live and 'DEPLOYER' not in os.environ:
        raise EnvironmentError(
            'Please set DEPLOYER env variable to the deployer account name')

    deployer = accounts.load(os.environ['DEPLOYER']) \
        if is_live or 'DEPLOYER' in  os.environ \
        else accounts[0]
    
    return deployer


def prompt_bool():
    choice = input().lower()
    if choice in {'yes', 'y'}:
       return True
    elif choice in {'no', 'n'}:
       return False
    else:
       sys.stdout.write("Please respond with 'yes' or 'no'")

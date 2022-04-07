# @version 0.3.1
# @license MIT

from vyper.interfaces import ERC20

struct BalancerReward:
    token: address
    distributor: address
    period_finish: uint256
    rate: uint256
    last_update: uint256
    integral: uint256


reward: public(BalancerReward)


@external
def __init__(distributor: address, token: address):
    self.reward.distributor = distributor
    self.reward.token = token


@external
@view
def reward_data(addr: address) -> BalancerReward: 
    if (addr == self.reward.token):
        return self.reward
    return BalancerReward({
        token: 0x0000000000000000000000000000000000000000,
        distributor: 0x0000000000000000000000000000000000000000,
        period_finish: 0,
        rate: 0,
        last_update: 0,
        integral: 0
    })


@external
def deposit_reward_token(_reward_token: address, _amount: uint256):
    assert msg.sender == self.reward.distributor
    self.reward.last_update = block.timestamp
    self.reward.period_finish = block.timestamp + 604800
    ERC20(self.reward.token).transferFrom(msg.sender, self, _amount)


@external
def set_reward_distributor(_reward_token: address, _distributor: address): 
    assert msg.sender == self.reward.distributor
    assert _reward_token == self.reward.token
    self.reward.distributor = _distributor

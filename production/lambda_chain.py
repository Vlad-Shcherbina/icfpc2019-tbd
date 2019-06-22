'''
Interface to Lamda-chain.
'''

import urllib
import json
from pprint import pprint
from dataclasses import dataclass
from datetime import datetime

import requests


BLOCKCHAIN_ENDPOINT = 'https://lambdacoin.org/lambda/'

# demo
# PRIVATE_KEY = '34fbde3097374e7d6f3465f7'
# PUBLIC_KEY = 1

# team TBD
PRIVATE_KEY = 'b25e2580b16d891a4f1b3272'
PUBLIC_KEY = 151


@dataclass
class BlockInfo:
    number: int
    num_subs: int
    we_can_submit: bool
    timestamp: int
    balances: dict

    puzzle: str
    task: str

    @property
    def time(self):
        return datetime.fromtimestamp(self.timestamp)


def get_block_info() -> BlockInfo:
    url = urllib.parse.urljoin(BLOCKCHAIN_ENDPOINT, 'getblockinfo')
    with urllib.request.urlopen(url) as s:
        j = json.loads(s.read())

    number = j.pop('block')
    num_subs = j.pop('block_subs')
    timestamp = j.pop('block_ts')
    excluded = j.pop('excluded')
    puzzle = j.pop('puzzle')
    task = j.pop('task')
    balances = j.pop('balances')
    assert not j, f'unrecognized fields {j}'

    return BlockInfo(
        number=number,
        num_subs=num_subs,
        we_can_submit=str(PUBLIC_KEY) not in excluded,
        timestamp=timestamp,
        balances=balances,

        puzzle=puzzle,
        task=task,
    )


def main():
    b = get_block_info()
    print(f' block number:  {b.number}')
    print(f'         time:  {b.time} ')
    print(f'                ({datetime.now() - b.time} ago)')
    print(f'we can submit:  {b.we_can_submit}')

    # for method in 'getblockchaininfo', 'getmininginfo', 'getbalances', 'getblockinfo/1':
    #     print(method)
    #     url = urllib.parse.urljoin(BLOCKCHAIN_ENDPOINT, method)
    #     with urllib.request.urlopen(url) as s:
    #         pprint(json.loads(s.read()))
    #     print()

    # pass


if __name__ == '__main__':
    main()

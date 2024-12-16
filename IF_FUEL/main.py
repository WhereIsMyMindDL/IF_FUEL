import os
import time
import random
import asyncio
import platform
import questionary
import pandas as pd

from web3 import Web3
from sys import stderr
from loguru import logger
from web3.eth import AsyncEth
from eth_account.account import Account
from curl_cffi.requests import AsyncSession

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger.remove()
logger.add(stderr,
           format="<lm>{time:HH:mm:ss}</lm> | <level>{level}</level> | <blue>{function}:{line}</blue> "
                  "| <lw>{message}</lw>")

headers = {
    'accept': 'application/json',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://app.impossible.finance',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://app.impossible.finance/',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 '
                  'Safari/537.36',
}


class Acc:
    def __init__(self, privatekey: str, number_acc: int) -> None:
        self.private_key = privatekey
        self.client = None
        self.id: int = number_acc
        self.account = Account().from_key(private_key=self.private_key)
        self.w3 = Web3(
            provider=Web3.AsyncHTTPProvider(endpoint_uri='https://rpc.ankr.com/arbitrum'),
            modules={"eth": AsyncEth},
            middlewares=[])

    async def send_tx(self, data: str, x: int = 0) -> None:
        tx_data = {
            "chainId": 42161,
            "from": self.account.address,
            "to": self.w3.to_checksum_address('0x49092EEF13108404260dF7919B66fd64A5DB410e'),
            "nonce": await self.w3.eth.get_transaction_count(self.account.address),
            "value": 0,
            "data": data,
            "gasPrice": random.randint(4500000000, 7000000000),
            "gas": random.randint(5000000, 8000000),
        }

        signed_txn = self.w3.eth.account.sign_transaction(tx_data, self.private_key)

        tx_hash = await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logger.info(f'send txs...')

        tx_hash = self.w3.to_hex(tx_hash)
        while x <= 10:
            try:
                receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
                if receipt['status'] == 1:
                    logger.success(f'{self.id} | Success send tx | hash: {tx_hash}')
                    return
                else:
                    logger.error(f'{self.id} | Failed send tx | hash: {tx_hash}')
                    return

            except Exception as e:
                x += 1
                logger.error(f'{self.id} | {e}')

    async def approve(self, x: int = 0) -> None:
        tx_data = {
            "chainId": 42161,
            "from": self.account.address,
            "to": self.w3.to_checksum_address('0xaf88d065e77c8cC2239327C5EDb3A432268e5831'),
            "nonce": await self.w3.eth.get_transaction_count(self.account.address),
            "value": 0,
            "data": '0x095ea7b3'
                    '00000000000000000000000049092eef13108404260df7919b66fd64a5db410e'
                    '0000000000000000000000000000000000000000000000000000000017D78400',
            "gasPrice": random.randint(450000000, 700000000),
            "gas": random.randint(500000, 800000),
        }

        signed_txn = self.w3.eth.account.sign_transaction(tx_data, self.private_key)

        tx_hash = await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logger.info(f'send approve tx...')

        tx_hash = self.w3.to_hex(tx_hash)
        while x <= 10:
            try:
                receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
                if receipt['status'] == 1:
                    logger.success(f'{self.id} | Success approve | hash: {tx_hash}')
                    return
                else:
                    logger.error(f'{self.id} | Failed approve | hash: {tx_hash}')
                    return

            except Exception as e:
                x += 1
                logger.error(f'{self.id} | {e}')

    async def get_data(self) -> None:
        data = '0x2316448c0000000000000000000000000000000000000000000000000000000017d78400000000000000000000000000000' \
               '00000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000017d78400' \
               '000000000000000000000000000000000000000000000000000000000000000c'
        async with AsyncSession(headers=headers) as client:
            r = await client.get(
                url='https://backend.impossible.finance/api/backend-service/merkle/proof',
                params={
                    'address': self.account.address,
                    'saleId': '851',
                },
            )
            if r.status_code == 200:
                response_json: dict = r.json()
                for d in response_json['data']:
                    data += d[2:]

            with open('accounts_data.xlsx', 'rb') as f:
                e = pd.read_excel(f)
            e['merkleProof'] = e['merkleProof'].astype(str)
            e.loc[(self.id - 1), 'merkleProof'] = str(data)
            e.to_excel('accounts_data.xlsx', header=True, index=False)
            logger.success(f'{self.id} | Success get data')


async def start(account_excel, semaphore, idx) -> None:
    async with semaphore:
        try:
            account = Acc(privatekey=account_excel[0], number_acc=idx)
            if choice.__contains__('Get data for tx'):
                await account.get_data()

            elif choice.__contains__('Approve USDC'):
                await account.approve()

            elif choice.__contains__('Wait and Send tx'):
                logger.info(f'Wait start sale')
                while time.time() < 1734429600:
                    pass
                await account.send_tx(data=account_excel[1])

        except Exception as e:
            logger.error(f'Failed: {account.id} | {str(e)}')


async def main() -> None:
    threads = 1 if choice.__contains__('Get data for tx') else len(accounts)
    semaphore: asyncio.Semaphore = asyncio.Semaphore(threads)
    tasks: list[asyncio.Task] = [
        asyncio.create_task(start(account_excel=account, semaphore=semaphore, idx=idx))
        for idx, account in enumerate(accounts, start=1)
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    with open('accounts_data.xlsx', 'rb') as file:
        exel = pd.read_excel(file)
    os.system('cls')
    accounts: list[list] = [
        [
            row["Private Key"],
            row["data"] if isinstance(row["data"], str) else None,
        ]
        for index, row in exel.iterrows()
    ]
    logger.info(f'My channel: https://t.me/CryptoMindYep')
    logger.info(f'Total accounts: {len(accounts)}\n')

    choice = questionary.select(
        "Select work mode:",
        choices=[
            "Get data for tx",
            "Approve USDC",
            "Wait and Send tx",
            "Exit"
        ]
    ).ask()

    if 'Exit' in choice:
        exit()

    asyncio.run(main())

    logger.success('The work completed')
    logger.info('Thx for donat: 0x5AfFeb5fcD283816ab4e926F380F9D0CBBA04d0e')

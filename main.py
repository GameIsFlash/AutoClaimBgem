from web3 import Web3
from eth_account import Account
import json
import datetime


def load_addresses(file_path: str) -> list:
    """
    Функция для загрузки списка адресов из файла
    :param file_path: путь к файлу
    :return: список адресов
    """
    with open(file_path, 'r') as f:
        addresses = [line.strip() for line in f.readlines()]
    return addresses


def load_accounts(file_path: str) -> dict:
    """
    Функция для загрузки словаря аккаунтов из json файла
    :param file_path: путь к файлу
    :return: словарь аккаунтов
    """
    with open(file_path, 'r') as f:
        accounts = json.load(f)
    return accounts


def connect_to_web3(rpc_url: str) -> Web3:
    """
    Функция для создания экземпляра Web3 с указанием адреса RPC-узла
    :param rpc_url: адрес RPC-узла
    :return: экземпляр Web3
    """
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if web3.isConnected():
        print('Подключение к RPC узлу прошло успешно')
    else:
        print('Не удалось подключиться к RPC узлу')
    return web3


def withdraw_tokens(contract_address: str, contract_abi_path: str, mm_addresses: list, accounts_path: str,
                    gas_limit: int, gas_price: int) -> None:
    """
    Функция для вывода токенов со всех адресов, которые доступны для вывода
    :param contract_address: адрес контракта
    :param contract_abi_path: путь к файлу с abi контракта
    :param mm_addresses: список адресов, с которых будет производиться вывод
    :param accounts_path: путь к файлу с аккаунтами
    :param gas_limit: лимит газа для транзакции
    :param gas_price: цена газа в wei
    """
    web3 = connect_to_web3('https://rpc-mainnet.maticvigil.com')
    web3.transaction_pool_pending_timeout = 300
    contract_abi = json.load(open(contract_abi_path))
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    accounts = load_accounts(accounts_path)

    n = 1
    for account in mm_addresses:
        try:
            result = contract.functions.withdrawTime(account).call({'from': account})
            dt_object = datetime.datetime.fromtimestamp(result)
            if result == 0:
                print(n, '- доступен для клэйма, готовлю транзакцию')
                if account in accounts:
                    address = account
                    private_key = accounts[account]

                    function_name = 'requestTokens'
                    function_params = {}

                    transaction = contract.functions[function_name](**function_params).buildTransaction({
                        'nonce': web3.eth.getTransactionCount(address),
                        'gas': gas_limit,
                        'gasPrice': gas_price,
                    })

                    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
                    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                    print('Транзакция отправлена, хэш:', tx_hash.hex())
                    print('Ссылка на Etherscan:', f'https://polygonscan.com/tx/{tx_hash.hex()}')
                    print('Статус транзакции:', receipt['status'])
                    print('---------------------------------------------')
                    n += 1

                else:
                    print(f'Не найден адрес {account} в файле аккаунтов')
                    print('---------------------------------------------')


            else:
                print(n, '- будет доступен для клэйма:', dt_object.strftime("%d-%b-%Y (%H:%M)"))
                print('---------------------------------------------')
                n += 1

        except Exception as e:
            print(f'Ошибка: {str(e)}')
            print('---------------------------------------------')
            n += 1


if __name__ == "__main__":
    contract_address = "0x3a1F862D8323138F14494f9Fb50c537906b12B81"  # адрес контракта
    contract_abi_path = "ABI.json"  # путь к файлу с abi контракта
    mm_addresses = load_addresses("adresses.txt")  # список адресов, с которых будет производиться вывод
    accounts_path = "accounts.json"  # путь к файлу с аккаунтами
    gas_limit = 200000  # лимит газа для транзакции
    gas_price = Web3.toWei('210', 'gwei')  # цена газа в wei

    withdraw_tokens(contract_address, contract_abi_path, mm_addresses, accounts_path, gas_limit, gas_price)

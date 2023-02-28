import time
import pyupbit
import datetime
import requests
import json

access = "Accesskey를 입력하세요"
secret = "Secretkey를 입력하세요"
myToken = "kakao token을 입력하세요"
ticker = "KRW-BTC"


def post_message(token, channel, text):
    """카카오톡 메시지 전송 함수"""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": "Bearer " + token
    }
    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text,
            "link": {
                "web_url": "https://developers.kakao.com",
                "mobile_web_url": "https://developers.kakao.com"
            },
        })
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()


def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time


def get_balance(ticker):
    """해당 코인 잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


def get_k_value(ticker):
    """변동성 돌파 전략에 사용될 k값 계산"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=14)
    delta = df["high"] - df["low"]
    atr = delta.rolling(window=14).mean()
    k = 2.0 / (1 + len(atr[~atr.isna()]))
    return k


def buy_crypto_currency(ticker, krw_balance):
    """매수 함수"""
    orderbook = pyupbit.get_orderbook(ticker)
    sell_price = orderbook[0]['orderbook_units'][0]['bid_price']
    unit = krw_balance / float(sell_price)
    buy_result = upbit.buy_limit_order(ticker, sell_price, unit)
    return buy_result


def sell_crypto_currency(ticker, volume):
    """매도 함수"""
    current_price = get_current_price(ticker)
    sell_result = upbit.sell_market_order(ticker, volume)
    return sell_result

def calculate_buy_units(balance, price):
    """
    가용한 원화 잔액과 현재 가격을 이용하여 매수할 수 있는 코인 수량을 계산합니다.
    """
    available_balance = balance * 0.95  # 최대 95% 까지만 사용합니다.
    buy_units = available_balance / price
    return buy_units


upbit = pyupbit.Upbit(access, secret)
post_message(myToken, "#cryptocurrency", "자동매매를 시작합니다.")
k_value = get_k_value(ticker)

while True:
    try:
        now = datetime.datetime.now()
        if now.hour < 7 or now.hour >= 23:
            time.sleep(60)
            continue
        
        current_price = get_current_price(ticker)
        target_price = get_target_price(ticker, k_value)
        if current_price >= target_price:
            krw_balance = upbit.get_balance("KRW")
            if krw_balance > 5000:
                units = calculate_buy_units(krw_balance, current_price)
                buy_crypto_currency(ticker, current_price, units)
        else:
            btc_balance = upbit.get_balance(ticker)
            if btc_balance > 0.00008:
                sell_crypto_currency(ticker, current_price, btc_balance)

        time.sleep(1)
        
    except Exception as e:
        print(e)
        post_message(myToken, "#cryptocurrency", e)
        time.sleep(1)


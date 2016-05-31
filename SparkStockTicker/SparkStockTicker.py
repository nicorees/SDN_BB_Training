import requests
import json

STOCK_TICKER_URL = 'http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol=CSCO'

stock_ticker_request = requests.get(STOCK_TICKER_URL)

price = stock_ticker_request.json()['LastPrice']
change_percent = stock_ticker_request.json()['ChangePercent']
change_percent_ytd = stock_ticker_request.json()['ChangePercentYTD']
mkt_cap = stock_ticker_request.json()['MarketCap']

message = """==============================
Sharing Live Cisco Stock Data
==============================
Price: {0}
Change in Percent Today: {1:+.2f}
Change in Percent YTD: {2:+.2f}
Market Cap: {3:3}\n==============================
Source: {4}""".format(price, change_percent, change_percent_ytd, mkt_cap, STOCK_TICKER_URL)

SPARK_AUTH_TOKEN = #insert token here
SPARK_ROOM_ID = #insert room id here

SPARK_URL = 'https://api.ciscospark.com/v1/messages'
SPARK_HEADERS = {'Content-type' : 'application/json; charset=utf-8', 'Authorization' : SPARK_AUTH_TOKEN}
SPARK_PAYLOAD = json.dumps({'roomId':SPARK_ROOM_ID, 'text':message}	)

spark_request = requests.post(SPARK_URL, headers=SPARK_HEADERS, data=SPARK_PAYLOAD, verify=False)

#print result of request for debug
print(spark_request.text)
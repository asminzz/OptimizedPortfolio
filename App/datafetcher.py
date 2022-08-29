import json
import datetime
import time
import pandas as pd
import numpy as np

companyList = []
newCompanyList = []
companyData = {}
allData = {}
dailyjsonData = {}

def getAllData():
    global allData
    with open('alldata.json', 'r+') as outfile:
        print("Reading all Data")
        allData = json.loads(outfile.read())
    return allData


def getCompanyHistoricData(companyName):
    global allData
    if len(allData) == 0:
        allData = getAllData()
    return (allData[companyName]["data"])


def getCompaniesList():
    global companyList
    if len(companyList) == 0:
        with open('companies.json', 'r+') as outfile:
            companyList = json.loads(outfile.read())["content"]
    return companyList


def getCompaniesListForTradedDays(tradedDays):
    global companyList
    companyList = getCompaniesList()
    newCompanyList = []
    for i in companyList:
        try:
            if getCompanyHistoricData(i)['s'] != "no_data":
                if len(getCompanyHistoricData(i)['t']) > tradedDays:
                    newCompanyList.append(i)
        except:
            print("failed for "+i)
    return newCompanyList


def getFrontierData(selected_companies, days, iterations):
    t = pd.Series(getCompanyHistoricData("NEPSE")["t"], name="Date").tail(int(days))
    df = pd.DataFrame(index=t)

    for company in selected_companies:
        if company in getCompaniesList():
            df[company] = (pd.Series(getCompanyHistoricData(company)["c"]).tail(int(days))).to_numpy()
    # print(df)

    log_ret= np.log(df/df.shift(1))
    # print(log_ret.head())

    np.random.seed(42)
    num_ports = iterations
    all_weights = np.zeros((num_ports, len(df.columns)))

    ret_arr = np.zeros(num_ports)
    vol_arr = np.zeros(num_ports)
    sharpe_arr = np.zeros(num_ports)

    print("calculating...")
    for x in range(num_ports):
        # Weights
        weights = np.array(np.random.random(len(df.columns)))
        weights = weights / np.sum(weights)

        # Save weights
        all_weights[x, :] = weights
        # Expected return
        ret_arr[x] = np.sum((log_ret.mean() * weights * days))

        # Expected volatility
        vol_arr[x] = np.sqrt(np.dot(weights.T, np.dot(log_ret.cov() * days, weights)))

        # Sharpe Ratio
        sharpe_arr[x] = ret_arr[x] / vol_arr[x]

    print('max sharpe ratio in array: {}'.format(sharpe_arr.max()))
    print("location in array: {}".format(sharpe_arr.argmax()))

    print(all_weights[sharpe_arr.argmax()])
    max_sr_ret = ret_arr[sharpe_arr.argmax()]
    max_sr_vol = vol_arr[sharpe_arr.argmax()]

    # print(max_sr_ret)
    # print(max_sr_vol)

    return {'vol_arr': vol_arr,
            'ret_arr': ret_arr,
            'sharpe_arr': sharpe_arr,
            'all_weights': all_weights
            }

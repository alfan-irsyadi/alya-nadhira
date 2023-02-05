from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import math
import numpy as np
import requests
import json


class fuzzy:
    def __init__(self, D1=0, D2=70, start="2020-01-01", end="2022-12-31"):
        url = "https://api.investing.com/api/financialdata/101599/historical/chart/?period=P5Y&interval=P1W&pointscount=120"
        proxy = "http://8b80c78b6cdd52c1ad2d302bf47c37f17adec017:antibot=true@proxy.zenrows.com:8001"
        proxies = {"http": proxy, "https": proxy}
        response = requests.get(url, proxies=proxies, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.find('pre').get_text()
        data = json.loads(text)['data']
        data = pd.DataFrame(
            data, columns=['Date', 'Open', 'High', 'Low', 'Price', 'Vol', '-'])
        # self.df = yf.download("PTBA.JK", start="2020-01-01", end="2022-12-31")
        self.df = data.copy()
        self.df.loc[:, 'Date'] = pd.to_datetime(self.df.Date, unit='ms')
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')
        self.df = self.df[self.df.Date >= start]
        self.df = self.df[self.df.Date <= end].reset_index(drop=True)
        # self.df = pd.read_csv(filename, thousands=',')
        self.U = [self.df.Price.min()-D1, self.df.Price.max()+D2]
        self.R = self.U[1]-self.U[0]
        self.K = int(round(1+3.322*math.log10(len(self.df))))
        self.I = self.R/self.K
        self.bb = [self.U[0]]
        self.ba = [self.U[0]+self.I]
        for i in range(1, self.K):
            self.bb.append(self.bb[i-1]+self.I)
            self.ba.append(self.ba[i-1]+self.I)
        self.labels = ["A"+str(i) for i in range(1, self.K+1)]

    def fit(self):
        cat = pd.cut(self.df.Price, bins=[*self.bb, self.ba[self.K-1]], right=False, labels=self.labels)
        self.df['Fuzzifikasi'] = cat
        self.df.Date = pd.to_datetime(self.df.Date)
        self.df.sort_values(by=['Date'], inplace=True)
        self.data = self.df[['Date','Price','Fuzzifikasi']].reset_index(drop=True)
        LH = ["", *self.data['Fuzzifikasi'].iloc[range(len(self.df)-1)]]
        self.data.loc[:,'LH'] = LH
        self.data.loc[:,'RH'] = self.data['Fuzzifikasi']
        self.data.loc[:,'FLRG'] = self.data['LH'].str.replace('A','G')
        self.data = self.data.iloc[range(1,len(self.df)),:]
        self.pivot = self.data.groupby(by=['LH','RH']).agg({'FLRG':np.count_nonzero}).dropna()                
        m = (np.array(self.bb)+np.array(self.ba))/2
        self.m = {}
        self.prediksi = {}
        a = self.data.FLRG.unique()
        a.sort()
        for index,key in enumerate(self.labels):
            self.m[key] = m[index]        
        for key in self.labels:                        
            self.prediksi[key] = 0
            bobot = 0
            for key2 in self.pivot.loc[key].index:
                self.prediksi[key] += self.m[key2]*self.pivot.loc[(key,key2)][0]
                bobot += self.pivot.loc[(key,key2)][0]
            self.prediksi[key] /= bobot
        print(self.prediksi)
        self.data['Peramalan'] = self.data['LH'].map(self.prediksi)
        del a        
    def forecast(self):
        return self.prediksi[self.data['Fuzzifikasi'][len(self.data)]]
    # def plot(self):
    #     fig = Figure()
    #     ax = fig.subplots()
    #     # ax.plot(self.data.Date, self.data.Price)
    #     up = self.df[self.df.Price >= self.df.Open].iloc[-12:]
  
    #     # "down" dataframe will store the self.data
    #     # when the closing stock price is
    #     # lesser than the Opening stock prices
    #     down = self.df[self.df.Price < self.df.Open].iloc[-12:]
        
    #     # When the stock prices have decreased, then it
    #     # will be represented by blue color candlestick
    #     col1 = 'green'
        
    #     # When the stock prices have increased, then it 
    #     # will be represented by green color candlestick
    #     col2 = 'red'
        
    #     # Setting width of candlestick elements
    #     width = 5
    #     width2 = .5
        
    #     # Plotting up prices of the stock
    #     ax.bar(up.Date, up.Price-up.Open, width, bottom=up.Open, color=col1)
    #     ax.bar(up.Date, up.High-up.Price, width2, bottom=up.Price, color=col1)
    #     ax.bar(up.Date, up.Low-up.Open, width2, bottom=up.Open, color=col1)
        
    #     # Plotting down prices of the stock
    #     ax.bar(down.Date, down.Price-down.Open, width, bottom=down.Open, color=col2)
    #     ax.bar(down.Date, down.High-down.Open, width2, bottom=down.Open, color=col2)
    #     ax.bar(down.Date, down.Low-down.Price, width2, bottom=down.Price, color=col2)
        
    #     # rotating the x-axis tick labels at 30degree 
    #     # towards right
    #     # ax.set_xticklabels(rotation=30, ha='right')
    #     # fig.show()
    #     # Save it to a temporary buffer.
    #     buf = BytesIO()
    #     fig.savefig(buf, format="png")
    #     # Embed the result in the html output.
    #     data = base64.b64encode(buf.getbuffer()).decode("ascii")
    #     return data
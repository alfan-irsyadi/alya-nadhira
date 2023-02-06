# from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import math
import numpy as np
import http.client
import base64
from io import BytesIO
from matplotlib import pyplot as plt
import json
from lxml import html
text = "<pre style='a'>aa</pre>"



class fuzzy:
    def __init__(self, D1=0, D2=70, start="2020-01-01", end="2022-12-31"):        
        conn = http.client.HTTPSConnection("api.scrapingant.com")
        conn.request("GET", "/v2/general?url=https%3A%2F%2Fapi.investing.com%2Fapi%2Ffinancialdata%2F101599%2Fhistorical%2Fchart%2F%3Fperiod%3DP5Y%26interval%3DP1W%26pointscount%3D120&x-api-key=670698b978da4d5f813e0b613dffe0b1&wait_for_selector=pre")
        res = conn.getresponse()
        data = res.read()
        text = data.decode("utf-8")
        tree = html.fromstring(text)
        text = [td.text for td in tree.xpath("//pre")][0]
        # soup = BeautifulSoup(data.decode("utf-8"), 'html.parser')
        # text = soup.find('pre').get_text()
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
    def plot(self):        
        fig, ax = plt.subplots()
        data = self.data.iloc[-40:]
        plt.xlabel('Month')
        # plt.ylabel('Temp')
        plt.title('Harga Saham PT Bukit Asam TBK 40 Minggu Terakhir')
        ax.plot(data['Date'], data['Price'], color='blue')
        ax.plot(data['Date'], data['Peramalan'], color='red')
        ax.legend(['Harga Asli', 'Harga Ramalan'])        
        plt.setp(ax.get_xticklabels(), rotation=30);
        buf = BytesIO()
        fig.savefig(buf, format="png")
        # Embed the result in the html output.
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        return data
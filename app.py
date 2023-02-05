from flask import Flask,render_template, request
import pandas as pd
from datetime import datetime, timedelta, date
from fuzzy import fuzzy
    

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "GET":        
        return render_template('home1.html',  method=request.method)
    if request.method == 'POST':                 
        fz = fuzzy(D2=14, start="2020-01-01", end=request.form['end'])        
        fz.fit()        
        date1 = fz.data.Date[len(fz.data)]+timedelta(days=7)
        hasil = pd.DataFrame([[date1, fz.forecast()]], columns=['Tanggal','Harga'])
        print(hasil)
        return render_template('home1.html', fz=fz, method=request.method, max=date.today().strftime('%Y-%m-%d'), hasil=hasil)
        
    

if __name__ == '__main__':
    app.run(debug=True)
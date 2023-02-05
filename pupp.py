import asyncio
import json
from pyppeteer import launch
from pyppeteer_stealth import stealth
import pandas as pd

async def main():
    browser = await launch(headless=True)
    page = await browser.newPage()

    await stealth(page)  # <-- Here
    # await page.waitFor(5000)
    await page.goto("https://api.investing.com/api/financialdata/101599/historical/chart/?period=P5Y&interval=P1W&pointscount=120")
    element = await page.querySelector('pre')
    content = await page.evaluate('(element) => element.textContent', element)
    global data
    data = json.loads(content)['data']
    # await page.screenshot({'path': 'example.png'})
    await browser.close()
asyncio.get_event_loop().run_until_complete(main())
data = pd.DataFrame(data, columns=['Date','Open', 'High','Low','Price','Vol','-'])
data.to_csv('data.csv',index=False)

# print(alfan)
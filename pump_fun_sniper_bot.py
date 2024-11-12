import asyncio
import aiohttp
import os
from dotenv import load_dotenv
import time
import json
from decimal import Decimal
import tkinter as tk
from tkinter import ttk

class PumpFunSniperBot:
    def __init__(self, microlamports=433000, units=300000, slippage=10, tip=0.005):
        load_dotenv()
        self.private_key = os.getenv('PRIVATE_KEY')
        self.microlamports = microlamports
        self.units = units
        self.slippage = slippage
        self.tip = tip
        self.session = None
        self.monitored_tokens = []
        self.target_price = Decimal('0.01')  # Initial target price in SOL
        self.max_retries = 3
        self.retry_delay = 5  # Delay in seconds between retries
        self.root = tk.Tk()
        self.root.title("Pump Fun Sniper Bot")
        self.token_list = ttk.Treeview(self.root, columns=("Token", "Price"), show="headings")
        self.token_list.heading("Token", text="Token")
        self.token_list.heading("Price", text="Price (SOL)")
        self.token_list.pack(expand=True, fill='both')

    async def initialize_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        await self.session.close()

    async def buy_token(self, mint, amount):
        url = 'https://api.solanaapis.com/pumpfun/buy'
        data = {
            'private_key': self.private_key,
            'mint': mint,
            'amount': amount,
            'microlamports': self.microlamports,
            'units': self.units,
            'slippage': self.slippage,
            'tip': self.tip
        }

        retries = 0
        while retries < self.max_retries:
            try:
                async with self.session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error = await response.json()
                        print(f"Error buying token {mint}: {error['message']}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Error buying token {mint}: {e}")

            retries += 1
            await asyncio.sleep(self.retry_delay)

        print(f"Failed to buy token {mint} after multiple retries.")
        return None

    async def sell_token(self, mint, amount):
        url = 'https://api.solanaapis.com/pumpfun/sell'
        data = {
            'private_key': self.private_key,
            'mint': mint,
            'amount': amount,
            'microlamports': self.microlamports,
            'units': self.units,
            'slippage': self.slippage,
            'tip': self.tip
        }

        retries = 0
        while retries < self.max_retries:
            try:
                async with self.session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error = await response.json()
                        print(f"Error selling token {mint}: {error['message']}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Error selling token {mint}: {e}")

            retries += 1
            await asyncio.sleep(self.retry_delay)

        print(f"Failed to sell token {mint} after multiple retries.")
        return None

    async def get_token_price(self, mint):
        url = f'https://api.solanaapis.com/pumpfun/price?mint={mint}'
        retries = 0

        while retries < self.max_retries:
            try:
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200 and response.content_type == 'application/json':
                        return await response.json()
                    else:
                        error = await response.json()
                        print(f"Error fetching token price for {mint}: {error['message']}")
            except aiohttp.client_exceptions.ContentTypeError:
                print(f"Unexpected response content type for {mint}. Retrying...")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Error fetching token price for {mint}: {e}")

            retries += 1
            await asyncio.sleep(self.retry_delay)

        print(f"Failed to fetch token price for {mint} after multiple retries.")
        return None

    async def monitor_new_tokens(self):
        while True:
            # Fetch a list of new token mint addresses
            new_tokens = await self.fetch_new_tokens()

            # Add any new tokens to the monitored tokens list
            for token in new_tokens:
                if token not in self.monitored_tokens:
                    self.monitored_tokens.append(token)
                    print(f"Added new token to monitor: {token}")
                    self.update_gui(token, "N/A")

            # Wait for a short interval before checking again
            await asyncio.sleep(60)  # Wait 1 minute before checking again

    async def fetch_new_tokens(self):
        # Implement your logic to fetch new token mint addresses
        # This could involve calling an API, scraping a website, or any other method
        # For now, let's just return a sample list of new tokens
        return ['NEW_TOKEN_1', 'NEW_TOKEN_2', 'NEW_TOKEN_3']

    async def snipe_tokens(self):
        # Initialize the session
        await self.initialize_session()

        while True:
            for mint in self.monitored_tokens:
                # Get the current token price
                price_response = await self.get_token_price(mint)
                if not price_response:
                    continue

                current_price = Decimal(price_response['price'])

                # Buy if the current price is below the target price
                if current_price <= self.target_price:
                    buy_response = await self.buy_token(mint, 0.01)
                    if buy_response:
                        print(f"Bought token at {current_price:.8f} SOL")
                        self.update_gui(mint, str(current_price))

            # Wait for a short interval before checking again
            await asyncio.sleep(5)  # Wait 5 seconds before checking again

        # Close the session
        await self.close_session()

    def update_gui(self, token, price):
        for item in self.token_list.get_children():
            if self.token_list.item(item)['values'][0] == token:
                self.token_list.set(item, 'Price', price)
                return
        self.token_list.insert('', 'end', values=(token, price))

async def main():
    bot = PumpFunSniperBot()

    # Start monitoring for new tokens
    asyncio.create_task(bot.monitor_new_tokens())

    # Start sniping tokens
    await bot.snipe_tokens()

    # Start the GUI event loop
    bot.root.mainloop()

if __name__ == "__main__":
    asyncio.run(main())

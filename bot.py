import asyncio
import sys

import discord
import requests
import yaml
import os

def kill(msg):
    print(msg)
    sys.exit(1)

def load_config():
    if not os.path.exists("config.yaml"):
        return None

    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def check_url_available(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException as _:
        return False

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self._config = load_config()
        
        if not self._config:
            kill("The config.yaml file is missing. Copy the default one from github.")
        
        self.validate_config()
            
    def start_bot(self):
        self.run(self._config["bot_token"])
        pass
    
    def validate_config(self):
        for key in ["bot_token", "discord_user_id", "url_check_delay", "urls_to_check"]:
            if key not in self._config:
                kill(f"config.yaml is missing required configuration parameter: {key}")

        if not isinstance(self._config["urls_to_check"], list) or not self._config["urls_to_check"]:
            kill(f"The 'urls_to_check' parameter in config.yaml must be a non-empty list.")

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await self.check_urls_periodically()
        
    async def check_urls_periodically(self):
        delay = self._config["url_check_delay"]
        user = await self.fetch_user(self._config["discord_user_id"])

        print(f"Now fetching urls for {user} every {delay} seconds")

        while True:
            for url in list(self._config["urls_to_check"]):
                if check_url_available(url):
                    try:
                        await user.send(f"Website at {url} is now reachable")
                    except Exception as _:
                        print("Unable to send message")
                    
                else:
                    print("Website not available")
            await asyncio.sleep(delay)

if __name__ == "__main__":
    bot = Bot()
    bot.start_bot()

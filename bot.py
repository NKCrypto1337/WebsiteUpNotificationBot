import asyncio
import sqlite3
import sys

from contextlib import contextmanager
from discord import app_commands

import discord
import requests
import yaml
import os

MAX_USER_CAP = 10000

CREATE_STATEMENT = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_user_id INTEGER UNIQUE NOT NULL,
    is_subscribed BOOLEAN DEFAULT 1
    )
"""

GET_USER_COUNT_STATEMENT = """
SELECT COUNT(*) FROM users
"""

GET_USER_STATEMENT = """
SELECT discord_user_id FROM users
WHERE is_subscribed = 1
"""

EXISTS_USER_STATEMENT = """
SELECT COUNT(*) FROM users
WHERE discord_user_id = ?
"""

ADD_USER_STATEMENT = """
INSERT OR IGNORE INTO users (discord_user_id) VALUES (?)
"""

REMOVE_USER_STATEMENT = """
DELETE FROM users
WHERE discord_user_id = ?
"""

def kill(msg):
    print(msg)
    sys.exit(1)

def load_config():
    if not os.path.exists("config.yaml"):
        return None

    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

@contextmanager
def db_conn(path):
    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def check_url_available(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException as _:
        return False

class BotConfig:
    def __init__(self):
        self._config = load_config()
        
        self.validate_config()
        
        self._bot_token = self._config["bot_token"]
        self._admin_id = self._config["admin_id"]
        self._database_path = self._config["database_path"]
        self._url_check_delay = self._config["url_check_delay"]
        self._urls_to_check = self._config["urls_to_check"]
    
    @property
    def bot_token(self):
        return self._bot_token

    @property
    def admin_id(self):
        return self._admin_id
    
    @property
    def database_path(self):
        return self._database_path
    
    @property
    def url_check_delay(self):
        return self._url_check_delay
    
    @property
    def urls_to_check(self):
        return self._urls_to_check

    def validate_config(self):
        if not self._config:
            kill("The config.yaml file is missing. Copy the default one from github.")

        for key in ["bot_token", "admin_id", "database_path", "url_check_delay", "urls_to_check"]:
            if key not in self._config:
                kill(f"config.yaml is missing required configuration parameter: {key}")

        if not isinstance(self._config["urls_to_check"], list) or not self._config["urls_to_check"]:
            kill(f"The 'urls_to_check' parameter in config.yaml must be a non-empty list.")

class BotDatabase:
    def __init__(self, config: BotConfig):
        self._config: BotConfig = config
    
    def ensure_created(self) -> None:
        with db_conn(self._config.database_path) as cursor:
            cursor.execute(CREATE_STATEMENT)

        print(f"Successfully initialized database at {self._config.database_path}")
        
    def get_user_count(self) -> int:
        with db_conn(self._config.database_path) as cursor:
            print(f"Getting user count")
            cursor.execute(GET_USER_COUNT_STATEMENT)
            return int(cursor.fetchone()[0])
    
    def get_subscribed_users(self) -> list[int]:
        with db_conn(self._config.database_path) as cursor:
            cursor.execute(GET_USER_STATEMENT)
            return [user[0] for user in cursor.fetchall()]
    
    def subscribe_user(self, user_id: int):
        with db_conn(self._config.database_path) as cursor:
            print(f"Adding user {user_id}")
            cursor.execute(ADD_USER_STATEMENT, (user_id, ))
    
    def unsubscribe_user(self, user_id: int):
        with db_conn(self._config.database_path) as cursor:
            print(f"Removing user {user_id}")
            cursor.execute(REMOVE_USER_STATEMENT, (user_id, ))
    
    def is_user_subscribed(self, user_id: int) -> bool:
        with db_conn(self._config.database_path) as cursor:
            print(f"Checking if user {user_id} exists")
            cursor.execute(EXISTS_USER_STATEMENT, (user_id, ))
            return int(cursor.fetchone()[0]) == 1

class WebsiteMonitor:
    def __init__(self, config: BotConfig):
        self._config: BotConfig = config
        self._url_status = {}
        
    def monitor(self):
        for url in self._config.urls_to_check:
            if check_url_available(url):
                self._url_status[url] = True
            else:
                self._url_status[url] = False
    
    @property
    def url_status(self):
        return self._url_status
    
    def url_status_for(self, url) -> bool:
        return self._url_status.get(url)

class WebsiteMonitorApp(discord.ui.View):
    def __init__(self, config: BotConfig, database: BotDatabase, monitor: WebsiteMonitor):
        super().__init__(timeout=None)
        self._config = config
        self._database = database
        self._monitor = monitor

    async def update_buttons(self, interaction: discord.Interaction):
        self.clear_items()

        if self._database.is_user_subscribed(interaction.user.id):
            self.add_item(self.create_unsubscribe_button())
        else:
            self.add_item(self.create_subscribe_button())

        self.add_item(self.create_status_button())

        embed = discord.Embed(
            title="Website Monitor Dashboard",
            description="Monitor your favorite websites and get subscribe for notifications, when they're available!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Active Monitors",
            value=f"{len(self._config.urls_to_check)} websites",
            inline=True
        )
        embed.add_field(
            name="Subscribers",
            value=f"{self._database.get_user_count()} users",
            inline=True
        )

        await interaction.edit_original_response(embed=embed, view=self)

    def create_subscribe_button(self):
        button = discord.ui.Button(
            label="Subscribe",
            style=discord.ButtonStyle.green,
            custom_id="subscribe_button"
        )
        button.callback = self.subscribe_button
        return button

    def create_unsubscribe_button(self):
        button = discord.ui.Button(
            label="Unsubscribe",
            style=discord.ButtonStyle.red,
            custom_id="unsubscribe_button"
        )
        button.callback = self.unsubscribe_button
        return button

    def create_status_button(self):
        button = discord.ui.Button(
            label="View Status",
            style=discord.ButtonStyle.blurple,
            custom_id="view_status"
        )
        button.callback = self.view_status
        return button

    async def subscribe_button(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id

        if self._database.is_user_subscribed(user_id):
            await interaction.followup.send("You are already subscribed!", ephemeral=True)
            return

        self._database.subscribe_user(user_id)
        await interaction.followup.send("Successfully subscribed to website monitoring!", ephemeral=True)
        await self.update_buttons(interaction)

    async def unsubscribe_button(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id

        if not self._database.is_user_subscribed(user_id):
            await interaction.followup.send("You are not subscribed!", ephemeral=True)
            return

        self._database.unsubscribe_user(user_id)
        await interaction.followup.send("Successfully unsubscribed from website monitoring!", ephemeral=True)
        await self.update_buttons(interaction)

    async def view_status(self, interaction: discord.Interaction):
        embed = await self.create_status_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def create_status_embed(self):
        embed = discord.Embed(title="Website Status", color=discord.Color.blue())
        for url in self._config.urls_to_check:
            status = "🟢 Online" if self._monitor.url_status_for(url) else "🔴 Offline"
            embed.add_field(name=url, value=status, inline=False)
        return embed

class WebsiteMonitorClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self._tree = app_commands.CommandTree(self)
        self._config = BotConfig()
        self._database = BotDatabase(self._config)
        self._database.ensure_created()
        self._website_monitor: WebsiteMonitor = WebsiteMonitor(self._config)

    def start_client(self):
        self.run(self._config.bot_token)

    async def setup_hook(self):
        self._tree.add_command(
            app_commands.Command(
                name="monitor",
                description="Open the Website Monitor dashboard",
                callback=self.open_dashboard
            )
        )

        self._tree.add_command(
            app_commands.Command(
                name="status",
                description="View current website status",
                callback=self.show_status
            )
        )

        await self._tree.sync()
        
    async def on_ready(self):
        await self.start_monitoring()

    async def open_dashboard(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Website Monitor Dashboard",
            description="Subscribe for notifications, when any websites are available!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Active Monitors",
            value=f"{len(self._config.urls_to_check)} websites",
            inline=True
        )
        embed.add_field(
            name="Subscribers",
            value=f"{self._database.get_user_count()} users",
            inline=True
        )

        view = WebsiteMonitorApp(self._config, self._database, self._website_monitor)
        if interaction.user:
            if self._database.is_user_subscribed(interaction.user.id):
                view.add_item(view.create_unsubscribe_button())
            else:
                view.add_item(view.create_subscribe_button())
            view.add_item(view.create_status_button())

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def start_monitoring(self):
        while True:
            self._website_monitor.monitor()

            for url, available in self._website_monitor.url_status.items():
                if not available:
                    print(f"Url '{url}' not available")
                    continue

                print(f"Url '{url}' available")
                for user_id in self._database.get_subscribed_users():
                    try:
                        user = await self.fetch_user(user_id)
                        embed = discord.Embed(
                            title="🟢 Website Available!",
                            description=f"<@{user_id}> The website at {url} is now accessible.",
                            color=discord.Color.green()
                        )
                        await user.send(embed=embed)
                    except Exception as e:
                        print(f"Error notifying user {user_id}: {e}")

            await asyncio.sleep(self._config.url_check_delay)

    async def show_status(self, interaction: discord.Interaction):
        view = WebsiteMonitorApp(self._config, self._database, self._website_monitor)
        embed = await view.create_status_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    client = WebsiteMonitorClient()
    client.start_client()

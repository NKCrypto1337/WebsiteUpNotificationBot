(Created with the help of GPT, not motivated to type out manually)

# Discord Bot Setup Guide

This README explains how to set up a new Discord bot, retrieve its token, find your user ID, and create a new application on Discord.

## 0. Install python and required packages

### Steps:
1. **Install python**
2. **Install required packages**
    - Run `pip install -r requirements.txt`


## 1. Get a Bot Token ID

Follow these steps to obtain a **bot token**:

### Steps:
1. **Go to the Discord Developer Portal**:
    - Open your browser and navigate to the [Discord Developer Portal](https://discord.com/developers/applications).

2. **Create a New Application**:
    - In the Developer Portal, click the **"New Application"** button.
    - Give your application a name and click **"Create"**.

3. **Create a Bot**:
    - In the application settings on the left panel, navigate to the **"Bot"** tab.
    - Click **"Add Bot"**.
    - You can customize the bot (e.g., set its username, avatar).
    - Make sure to **enable** the "Message" intent

4. **Get the Bot Token**:
    - Under the **"Bot"** tab, you'll see a **"TOKEN"** section.
    - Click **"Copy"** to copy your bot token (this is important as you'll need it for your bot to authenticate).
    - **Important**: Keep your bot token secure! Do not share it with anyone.

---

## 2. Get Your User ID

To interact with the Discord API, you'll need your **Discord User ID**.

### Steps:
1. **Enable Developer Mode**:
    - Open Discord and click the gear icon (**User Settings**) near the bottom left corner.
    - In the settings menu, go to the **"Advanced"** section and enable **Developer Mode**.

2. **Copy Your User ID**:
    - Once Developer Mode is enabled, right-click your profile picture or username in Discord.
    - Click **"Copy ID"** to copy your **User ID**.

You can now use this User ID for various purposes, such as sending direct messages or interacting with the Discord API.

---

## 3. Open a new chat with the bot

### Steps:
1. **Go to the Application Settings**:
    - In the Discord Developer Portal, select your application (bot) under **"Applications"**.

2. **Navigate to the "General Information" Tab**:
    - Copy the Application ID

3. **Generate an URL**:
    - Paste the application id into this url: `https://discord.com/users/<BOT_USER_ID>` and open the link

Now you will see the bot in your friend list on discord

---

## 4. Add the bot as application to your account

### Steps:
1. **Go to the bot profile**:
    - Click on "Open APP" upon opening
    - Click on the "..." options button
    - Click on "Add app"
    - Click on "Add to my apps"
    - Authorize the application

Now the bot will be able to dm you

---

## 5. Start the bot

### Steps:
1. **Go into the bot directory**
    - Run the bot by typing `python bot.py` and pressing enter

## Troubleshooting

---

That's it! If you have any questions, feel free to reach out!

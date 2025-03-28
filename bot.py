import discord
from discord.ext import commands
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from manager import main as update_lunch_menu

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel ID where the bot will post updates
LUNCH_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

async def post_lunch_menu():
    """Update and post the lunch menu"""
    try:
        # Update the lunch menu
        update_lunch_menu()
        
        # Read the updated menu
        with open('lunch_data.json', 'r', encoding='utf-8') as f:
            lunch_data = json.load(f)
        
        # Create the message
        today = datetime.now().strftime('%Y-%m-%d')
        message = f"🍽️ **Lunch Menu for {today}**\n\n"
        
        for restaurant in lunch_data:
            message += f"**{restaurant['restaurant_name']}**\n"
            if isinstance(restaurant['daily_special'], list):
                for special in restaurant['daily_special']:
                    message += f"• {special}\n"
            else:
                message += f"• {restaurant['daily_special']}\n"
            message += f"Price: {restaurant['price']}\n"
            if restaurant['included_items']:
                message += f"Included: {', '.join(restaurant['included_items'])}\n"
            message += f"Hours: {restaurant['lunch_hours']}\n"
            if restaurant['special_notes']:
                message += f"Note: {restaurant['special_notes']}\n"
            message += "\n"
        
        # Get the channel and send the message
        channel = bot.get_channel(LUNCH_CHANNEL_ID)
        if channel:
            await channel.send(message)
        else:
            print(f"Could not find channel with ID {LUNCH_CHANNEL_ID}")
            
    except Exception as e:
        print(f"Error posting lunch menu: {e}")

@bot.command(name='lunch')
async def lunch(ctx):
    """Command to manually trigger lunch menu update"""
    await post_lunch_menu()
    await ctx.send("Lunch menu has been updated!")

def run_bot():
    """Run the bot with the token from environment variables"""
    bot.run(os.getenv('DISCORD_BOT_TOKEN')) 
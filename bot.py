import openai
import discord
import os

from utils import get_embed_message, verify_env_variables, get_or_create_thread, create_thread, cleanup_inactive_threads
from messaging import send_user_message, create_and_poll_run, retrieve_response

from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

# Define Discord bot intents
intents = discord.Intents.all()

# Initialize the Discord bot with the specified intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize the OpenAI client with the API key
client = openai.Client(api_key=OPENAI_API_KEY)

# Event listener for when the bot is ready and online
@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user.name}')
    bot.loop.create_task(cleanup_inactive_threads(client))
    print("cleanup_inactive_threads job started")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)
        
# Command definition for "ask_the_bot"
@bot.tree.command(name="ask_the_bot")
@app_commands.describe(question="Ask a question.")
async def ask_the_bot(ctx: discord.Interaction, question: str):
    try:
        user_id = str(ctx.user.id)  # Get user ID as string
        await ctx.response.send_message(question)

         # Here we check if somebody is asking who is the best - Kay ofcourse
        if "who is the best" in question.lower() or "vem är den bästa" in question.lower():
            embededMessage = await get_embed_message(f"Definitely <@{user_id}>", discord.Color.pink())
            await ctx.followup.send(embed=embededMessage)
            
        else:
            thread_id = await get_or_create_thread(user_id, client)
            await send_user_message(thread_id, question, client)
            run_id = await create_and_poll_run(thread_id, ASSISTANT_ID, client)  
            response = await retrieve_response(thread_id, client)

            await ctx.followup.send(embed=response)

    except Exception as e:
        print(e)
        await ctx.followup.send("Sorry, I encountered an error. Please try again later.")

# Listen for bot mentions
@bot.event
async def on_message(message):

    user_id = str(message.author.id)  # Get user ID as string
    question = message.content.replace(bot.user.mention, '').strip() 

    if bot.user.mention in message.content.split():

        # Here we check if somebody is asking who is the best - Kay ofcourse
        if "who is the best" in question.lower() or "vem är den bästa" in question.lower():
            embededMessage = await get_embed_message(f"Definitely <@{user_id}>", discord.Color.pink())
            await message.channel.send(embed=embededMessage)

        elif question:
           
            thread_id = await get_or_create_thread(user_id, client)
            await send_user_message(thread_id, question, client)
            run_id = await create_and_poll_run(thread_id, ASSISTANT_ID, client)        
            embededMessage = await retrieve_response(thread_id, client)
            await message.channel.send(embed=embededMessage)

        else:
            await message.channel.send("You mentioned me! Do you have a question or something I can help with?")

# Check if the DISCORD_TOKEN or OPENAI_API_KEY or ASSISTANT_ID is not empty
verify_env_variables(DISCORD_TOKEN, OPENAI_API_KEY, ASSISTANT_ID)

# Run the bot using the Discord token
bot.run(DISCORD_TOKEN)

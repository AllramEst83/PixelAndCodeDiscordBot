import openai
import discord
import asyncio
import os

from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv() # This loads the variables from .env

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

# Define intents
intents = discord.Intents.all()

# Create an instance of a bot with the defined intents
bot = commands.Bot(command_prefix="!", intents=intents)


# Initialize the OpenAI client
client = openai.Client(api_key = OPENAI_API_KEY)

# Event listener for when the bot has switched from offline to online
@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
        for cmd in synced:
            print(f"Command: /{cmd.name}")
    except Exception as e:
        print(e)


# A simple command to respond with 'Hello!' and mention the user who invoked it
@bot.tree.command(name="ask_the_bot")
@app_commands.describe(question = "Ask a question.")
async def ask_the_bot(ctx: discord.Interaction, question:str):
    
    print(f"User question: {question}")
     # Immediate feedback to user
    await ctx.response.send_message("Processing your request, please wait...")

    # Run the blocking API calls in the background thread
    loop = asyncio.get_running_loop()

    # Create a thread using OpenAI API
    thread = await loop.run_in_executor(None, lambda: client.beta.threads.create())
    thread_id = thread.id

    # Get user input from the command message
    # user_input = ctx.message.content[len('/ask '):]  # Assumes your command is '.ask'
    user_input = question
    # Create a message with the user input using OpenAI API in an async way
    await loop.run_in_executor(None, lambda: client.beta.threads.messages.create(
        role="user",
        content=user_input,
        thread_id=thread_id
    ))

    # Create a run with the assistant and the thread using OpenAI API in an async way
    run = await loop.run_in_executor(None, lambda: client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    ))
    run_id = run.id

    # Polling for run completion
    while True:
        run_status = await loop.run_in_executor(None, lambda: client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        ).status)

        if run_status in ['completed', 'failed', 'cancelled', 'expired']:
            break
        await asyncio.sleep(1)  # Async sleep to prevent blocking

    # Get the messages using OpenAI API in an async way
    messages = await loop.run_in_executor(None, lambda: client.beta.threads.messages.list(
        thread_id=thread_id
    ))

     # Check if there are any messages from the assistant
    assistant_messages = [m for m in messages.data if m.role == 'assistant']
    # After processing, use follow-up for subsequent messages
    if assistant_messages:
        # Send the assistant's message as a follow-up
        await ctx.followup.send(f"{assistant_messages[0].content[0].text.value}.")
    else:
        # Send a message if no response was received from the assistant
        await ctx.followup.send("Sorry, I couldn't fetch a response. Please try again later or a different question.")


# Run the bot with your token
bot.run(DISCORD_TOKEN)

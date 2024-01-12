import openai
import discord
import asyncio
import os
import sys
import time
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

def verify_env_variables():
    """Check if all required environment variables are set."""
    if not DISCORD_TOKEN or not OPENAI_API_KEY or not ASSISTANT_ID:
        print("Error: Required environment variables are missing.")
        sys.exit(1)

# Define Discord bot intents
intents = discord.Intents.all()

# Initialize the Discord bot with the specified intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize the OpenAI client with the API key
client = openai.Client(api_key=OPENAI_API_KEY)

# User-thread mapping with last interaction time
user_threads = {}

# Function to get or create a thread for a user
async def get_or_create_thread(user_id):
    current_time = time.time()
    if user_id in user_threads:
        thread_info = user_threads[user_id]
        # Check if 30 minutes have passed since the last interaction
        if current_time - thread_info['last_interaction'] < 1800:
            thread_info['last_interaction'] = current_time
            return thread_info['thread_id']
        else:
            # Remove old thread info and create a new thread
            del user_threads[user_id]

    thread = await create_thread()
    user_threads[user_id] = {'thread_id': thread.id, 'last_interaction': current_time}
    return thread.id

# Function to create a new thread for OpenAI API
async def create_thread():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: client.beta.threads.create())

# Cleanup function for inactive threads
async def cleanup_inactive_threads():
    loop = asyncio.get_running_loop()  # Get the current event loop
    current_time = time.time()
    inactive_users = [user_id for user_id, thread_info in user_threads.items() 
                      if current_time - thread_info['last_interaction'] >= 1800]
    for user_id in inactive_users:
        # Delete the thread at OpenAI's end
        thread_id = user_threads[user_id]['thread_id']
        await loop.run_in_executor(None, lambda: client.beta.threads.delete(thread_id))

        # Remove the thread info from the user_threads dictionary
        del user_threads[user_id]

    await asyncio.sleep(600)  # Check every 10 minutes
    await cleanup_inactive_threads()

# Function to send a message from the user to the OpenAI API thread
async def send_user_message(thread_id, user_input):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: client.beta.threads.messages.create(
        role="user",
        content=user_input,
        thread_id=thread_id
    ))

# Function to create a run with the assistant and poll for its completion
async def create_and_poll_run(thread_id, assistant_id):
    loop = asyncio.get_running_loop()
    run = await loop.run_in_executor(None, lambda: client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    ))
    run_id = run.id

    while True:
        run_status = await loop.run_in_executor(None, lambda: client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        ).status)

        if run_status in ['completed', 'failed', 'cancelled', 'expired']:
            return run_id

# Function to retrieve the response from the assistant and send it to the user
async def retrieve_and_send_response(ctx, thread_id):
    loop = asyncio.get_running_loop()
    messages = await loop.run_in_executor(None, lambda: client.beta.threads.messages.list(thread_id=thread_id))
    assistant_messages = [m for m in messages.data if m.role == 'assistant']

    if assistant_messages:
        await ctx.followup.send(f"{assistant_messages[0].content[0].text.value}.")
    else:
        await ctx.followup.send("Sorry, I couldn't fetch a response. Please try again later or a different question.")

# Event listener for when the bot is ready and online
@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user.name}')
    bot.loop.create_task(cleanup_inactive_threads())
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
        await ctx.response.send_message("Processing your request, please wait...")

        thread_id = await get_or_create_thread(user_id)
        await send_user_message(thread_id, question)
        run_id = await create_and_poll_run(thread_id, ASSISTANT_ID)
        await retrieve_and_send_response(ctx, thread_id)

    except Exception as e:
        await ctx.followup.send("Sorry, I encountered an error. Please try again later.")

# Run the bot using the Discord token
bot.run(DISCORD_TOKEN)

# utils.py

import discord
import sys
import time
import asyncio
import openai

# User-thread mapping with last interaction time
user_threads = {}

# Creates and returns a Discord embed with the specified response and color.
async def get_embed_message(title:str, response:str, color: discord.Color):
        # Create an embed object
        embed = discord.Embed(
            title=title,
            color=color
        )
        embed.add_field(name="", value=response, inline=False)

        return embed

# Check if the DISCORD_TOKEN or OPENAI_API_KEY or ASSISTANT_ID is not empty
def verify_env_variables(DISCORD_TOKEN:str, OPENAI_API_KEY:str, ASSISTANT_ID:str):
    if not DISCORD_TOKEN or not OPENAI_API_KEY or not ASSISTANT_ID:
        print("Error: Required environment variables are missing.")
        sys.exit(1)

# Function to get or create a thread for a user
async def get_or_create_thread(user_id, client: openai.Client):
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

    thread = await create_thread(client)
    user_threads[user_id] = {'thread_id': thread.id, 'last_interaction': current_time}
    return thread.id

# Function to create a new thread for OpenAI API
async def create_thread(client: openai.Client):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: client.beta.threads.create())

async def cleanup_inactive_threads(client: openai.Client):
    while True:
        current_time = time.time()
        inactive_users = [user_id for user_id, thread_info in user_threads.items() 
                          if current_time - thread_info['last_interaction'] >= 1800]
        for user_id in inactive_users:
            # Delete the thread at OpenAI's end
            thread_id = user_threads[user_id]['thread_id']
            await client.beta.threads.delete(thread_id)

            # Remove the thread info from the user_threads dictionary
            del user_threads[user_id]

        await asyncio.sleep(600)  # Check every 10 minutes
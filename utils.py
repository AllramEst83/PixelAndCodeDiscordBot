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

# Creates and returns a embed for voting.
async def get_embed_voting_message(question:str, description:str, role_mention_str:str, color: discord.Color):
        # Create an embed object
        embed = discord.Embed(title=question, description=description, color=color)    
        embed.add_field(name="", value=f"{role_mention_str}", inline=False)
        embed.set_footer(text=f"Vote by reacting with the corresponding emoji.")
       
        return embed

async def create_help_embed_message(pixies_channel_str:str, color: discord.Color):

        embed = discord.Embed(
            title="Kommandon och Events",
            description="Här är Pixies alla kommandon och events",
            color=color
        )
        # Kommandon
        embed.add_field(
            name="Kommandon",
            value="- **help**: En lista över Pixies kommandon (Bara för oss med rollen 'pixel&code').\n"
                "- **ask_the_bot**: Ställ frågor till boten om Pixel&Code. Detta kommando är tänkt för kunder i lobbyn\n"
                "- **vote**: Skapa en enkel omröstning. Max 10 val (Bara för oss med rollen 'pixel&code').",
            inline=False
        )

        # Event
        embed.add_field(
            name="Event",
            value=f"- **on_member_join**: Meddelar i kanalen {pixies_channel_str} när en medlem gått med.\n"
                f"- **on_member_remove**: Pixie meddelar i kanalen {pixies_channel_str} när en medlem lämnat servern.\n"
                "- **Mention**: Som ask_the_bot fast man kan göra en mention och ställa sin fråga om Pixel&Code.",
            inline=False
        )
     
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

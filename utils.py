# utils.py

import discord
import sys
import time
import asyncio
import openai
import discord
from discord.ext import commands

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
        embed.set_footer(text=f"Rösta genom att reagera med motsvarande emoji.")
       
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
                "- **ask**: Ställ frågor till boten om Pixel&Code. Detta kommando är tänkt för kunder i lobbyn\n"
                "- **vote**: Skapa en enkel omröstning. Max 10 val (Bara för oss med rollen 'pixel&code').\n"
                "- **summarize**: Summerar kanalens innehåll. Bra om man vill komma ikapp men inte läsa igenom allt (Bara för oss med rollen 'pixel&code').",
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

         # Tasks
        embed.add_field(
            name="Automation",            
            value=f"- **Random encouraging messages**: Pixie kommer då och då att skicka uppmuntrande kommentarer till kollegorna på Pixel&Code i Pixie-Push\n"
                  f"- **Time report reminder**: Pixie skickar en påminnelse om att lämna in tidrapporten varje måndag samt den sista dagen i månaden till kanalen {pixies_channel_str}, förutsatt att den inte infaller på en lördag eller söndag. Om den sista dagen i månaden är en lördag eller söndag, kommer påminnelsen istället att skickas på fredagen (OBS! Denna version tar inte hänsyn till röda dagar)\n"
        )

        return embed
     
# Check if the varbles are not empty
def verify_env_variables(DISCORD_TOKEN: str, OPENAI_API_KEY: str, ASSISTANT_ID: str, SUMMARY_ASSISTANT_ID: str, GUILD_ID: str, PIXIE_PUSH_CHANNEL: str, BOT_CREATOR_USER_ID: str):
    if not DISCORD_TOKEN or not OPENAI_API_KEY or not ASSISTANT_ID or not SUMMARY_ASSISTANT_ID or not GUILD_ID or not PIXIE_PUSH_CHANNEL or not BOT_CREATOR_USER_ID:
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
            client.beta.threads.delete(thread_id)

            # Remove the thread info from the user_threads dictionary
            del user_threads[user_id]

        await asyncio.sleep(600)  # Check every 10 minutes

async def get_chat_history_by_limit(ctx: discord.interactions, limit: int, gpt_instruction:str):
         # Check if the limit is positive
    if limit <= 0:
        await ctx.response.send_message("Please provide a positive number for the limit.")
        return

    messages = []
    last_id = None
   
    while len(messages) < limit:
        # Calculate how many more messages we need to reach the limit
        remaining = limit - len(messages)

        # If last_id is set, get the message object for it
        before_message = None
        if last_id is not None:
            try:
                before_message = await ctx.channel.fetch_message(last_id)
            except discord.NotFound:
                # If the message is not found, break the loop
                break

        # Fetch the next batch of messages asynchronously
        batch = [message async for message in ctx.channel.history(limit=min(remaining, 100), before=before_message)]
        
        if not batch:
            # No more messages to fetch, break the loop
            break

        messages.extend(batch)
        last_id = batch[-1].id

        # Break if we have reached the limit
        if len(messages) >= limit:
            break

    # Summarize messages
    summary = f"{gpt_instruction}\n" + '\n'.join([f"{message.author.name}: {message.content}" for message in messages])

    return summary

async def send_dm_to_user(bot: commands.Bot, user_id: int, message:str):
    user = await bot.fetch_user(user_id)
    if user:
        print(f"bot-creator notified.")
        await user.send(message)
    else:
        print(f"Could not find user. Message: ({message}) not sent as DM")
        

def split_messages(content, chunk_size=2000):
    # Split the content into chunks of up to chunk_size characters
    return [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
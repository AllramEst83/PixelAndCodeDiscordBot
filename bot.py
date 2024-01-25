import openai
import discord
import os
import datetime
import asyncio
import pytz
import random

from utils import get_embed_message, verify_env_variables, get_or_create_thread, cleanup_inactive_threads, get_embed_voting_message, create_help_embed_message, get_chat_history_by_limit, send_dm_to_user
from messaging import send_user_message, create_and_poll_run, retrieve_response
from constants import pixies_channel_name, pixel_and_code_role_name, gpt_summary_instruction, supportive_messages, scheduled_times,bot_creator_role_name

from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime, timedelta
from datetime import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SUMMARY_ASSISTANT_ID = os.getenv('SUMMARY_ASSISTANT_ID')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
GUILD_ID = os.getenv('GUILD_ID')
PIXIE_PUSH_CHANNEL = os.getenv('PIXIE_PUSH_CHANNEL')
BOT_CREATOR_USER_ID = os.getenv('BOT_CREATOR_USER_ID')

# Varibles for random encouraging messages
chosen_time = None
sent_today = False
is_task_active = False

# Define Discord bot intents
intents = discord.Intents.all()

# Initialize the Discord bot with the specified intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize the OpenAI client with the API key
client = openai.Client(api_key=OPENAI_API_KEY)
summary_client = openai.Client(api_key=OPENAI_API_KEY)

# Event listener for when the bot is ready and online
@bot.event
async def on_ready():    
    global is_task_active
    try:
        print(f'--------------------------------')
        print(f'Bot logged in as {bot.user.name}')
        bot.loop.create_task(cleanup_inactive_threads(client))
        print("cleanup_inactive_threads done")

        print(f'--------------------------------')

        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
        print(f"Time on server is {datetime.now().strftime('%H:%M')} and we are ready to go!!!")

        print(f'--------------------------------')

        print("Starting scheduled_message loop.")
        scheduled_message.start()  # Start the scheduled task
    except Exception as e:
        print(e)

@bot.event
async def on_shutdown():
    print("Bot is shutting down. Cleaning up tasks...")
    scheduled_message.cancel()  # Cancel the scheduled_message task loop
    await scheduled_message()  # Wait for the task loop to finish

    # Add any additional cleanup code here
    print("Cleanup complete. Bot shutdown.")


#Tasks
# Function to calculate wait time until the next message
async def calculate_wait_time():
    global chosen_time
    
    # Define the Stockholm timezone
    stockholm_tz = pytz.timezone('Europe/Stockholm')
    
    # Get the current time in Stockholm
    now = datetime.now(stockholm_tz)
    
    # Get today's times that are still upcoming
    today_times = [t for t in scheduled_times if t >= now.strftime("%H:%M")]

    # If there are no times left today, return None (no wait time needed)
    if not today_times:
        print(f"No time slots left to send message today")
        return None
    
   # Check if we already have a chosen time for today
    if chosen_time is None or now > chosen_time:
        # Randomly choose one of the remaining times for today
        chosen_time_str = random.choice(today_times)
    
    # Parse the chosen time string into a datetime object
    chosen_datetime = datetime.strptime(chosen_time_str, "%H:%M").time()
    
    # Replace the current time with the chosen time keeping the same date
    chosen_time = now.replace(hour=chosen_datetime.hour, minute=chosen_datetime.minute, second=0, microsecond=0)
    
    # If the chosen time is in the past, schedule it for the next day
    if chosen_time < now:
        chosen_time += timedelta(days=1)
    
    print(f"Next message will be sent {chosen_time.strftime('%H:%M')}")

    # Calculate the number of seconds until the chosen time
    wait_seconds = (chosen_time - now).total_seconds()
    
    return wait_seconds

# Function to send a supportive message
async def send_supportive_message():
    global sent_today
    guild = bot.get_guild(int(GUILD_ID))
    if guild:
        channel = guild.get_channel(int(PIXIE_PUSH_CHANNEL))
        
        if channel:
            message = random.choice(supportive_messages)
            role = discord.utils.get(guild.roles, name=pixel_and_code_role_name)

            if role:
                message += f"\n{role.mention}"            

            await channel.send(message)
            sent_today = True  # Mark as message sent
        else:
            print("Channel not found.")
    else:
        print("Guild not found.")



# Scheduled task for sending messages
@tasks.loop(hours=1)
async def scheduled_message():
    global chosen_time, sent_today

    if not is_task_active:
        print("Task is on pause by the user. Will not run scheduled_message. Run toggle_task to activate the Task")
        return  # Skip the task if it's not active

    print("Running scheduled_message")

    stockholm_tz = pytz.timezone('Europe/Stockholm')
    now = datetime.now(stockholm_tz)
    current_time = now.time()

    # Define the reset time window
    reset_start_time = time(21, 0)
    reset_end_time = time(23, 0)

    # Check if current time is within the reset window and if a message has been sent today
    if reset_start_time <= current_time <= reset_end_time and sent_today:
        sent_today = False
        chosen_time = None
        print("Variables have been reset.")

    # If today's message has already been sent, skip the rest of the function
    if sent_today:
        
        return

    # Check if it's a weekday and current time is between the first and last scheduled times
    if now.weekday() < 5 and (time(8, 0) <= current_time < time(16, 0)):
        wait_seconds = await calculate_wait_time()
        if wait_seconds is not None:
            
            chosen_time_str = (now + timedelta(seconds=wait_seconds)).strftime("%H:%M")
            message = f"Chosen time to wake up and post message is {chosen_time_str}"
            
            print(message)
            await send_dm_to_user(bot, int(BOT_CREATOR_USER_ID), message)
            
            try:
                print("Going to sleep")
                await asyncio.sleep(wait_seconds)
                
                # Only proceed to send the message if sleep completes without interruption
                print("Sending message")
                await send_supportive_message()
                sent_today = True
                chosen_time = datetime.strptime(chosen_time_str, "%H:%M")
                print("Message sent")

            except asyncio.CancelledError as e:
                print(f"Scheduled_message was cancelled: {e}")
                return
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                # Do not send the message, just return from the function
                return
        else:
            print("No scheduled times left for today.")

#Events
# Notifies when somebody joins the server
@bot.event
async def on_member_join(member):
    # Find the channel named 'general'
    pixies_channel = discord.utils.get(member.guild.channels, name=pixies_channel_name)
    role_to_mention = discord.utils.get(member.guild.roles, name=pixel_and_code_role_name) 

    if pixies_channel and role_to_mention:
        # Format the role mention using the role's ID
        role_mention_str = role_to_mention.mention
        welcome_message = f"Med trumpeter och fanfar, välkomnar vi stolt vår nyaste medlem, {member.mention}, till denna ärevördiga sammankomst!, {role_mention_str}"

        embed = await get_embed_message("Ny medlem har gått med! <:pc_heart_orange:1197121879375355915>", welcome_message, discord.Color.purple())   
        await pixies_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    # Find the channel named 'general'
    pixies_channel = discord.utils.get(member.guild.channels, name=pixies_channel_name)
    role_to_mention = discord.utils.get(member.guild.roles, name=pixel_and_code_role_name)

    if pixies_channel and role_to_mention:

        role_mention_str = role_to_mention.mention
        exit_message = f"{member.mention} har lämnat vårt sällskap. Vi höjer våra glas till hen's ära! {role_mention_str}"

        embed = await get_embed_message("Medlem har lämnat <:pc_heart:1197121144248074341>", exit_message, discord.Color.red())   
        await pixies_channel.send(embed=embed)

# Listen for bot mentions
@bot.event
async def on_message(message):

    if message.author == bot.user:
        return
    
    user_id = str(message.author.id)  # Get user ID as string
    question = message.content.replace(bot.user.mention, '').strip() 

    if bot.user.mention in message.content.split():

        # Here we check if somebody is asking who is the best - Kay ofcourse
        if "who is the best" in question.lower() or "vem är den bästa" in question.lower():
            embededMessage = await get_embed_message("Svar",f"Definitely <@{user_id}>", discord.Color.pink())
            await message.channel.send(embed=embededMessage)

        elif question:
           
            thread_id = await get_or_create_thread(user_id, client)
            await send_user_message(thread_id, question, client)
            run_id = await create_and_poll_run(thread_id, ASSISTANT_ID, client)        
            embededMessage = await retrieve_response(thread_id, client)
            await message.channel.send(embed=embededMessage)

        else:
            await message.channel.send("Du nämnde mig! Har du en fråga eller är det något jag kan hjälpa till med?")

#Commands
# Create a voting. Maximum amount of options is 10.
@app_commands.checks.has_any_role(pixel_and_code_role_name)
@bot.tree.command(name='vote', description="Skapa en omröstning.")
@app_commands.describe(question="Skapa en omröstning.", options_str="Ange alternativen separerade med kommatecken.")
async def vote(ctx: discord.Interaction, question: str, options_str: str):    
    options = [opt.strip() for opt in options_str.split(',') if opt.strip()]

    if len(options) > 10:        
        await ctx.response.send_message("You can only provide a maximum of 10 options.")        
        return
    if len(options) < 2:        
        await ctx.response.send_message("You need at least two options to create a poll.")        
        return
    
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    description = []    
    
    for x, option in enumerate(options):        
        description.append(f"{emojis[x]} {option}")

    role_to_mention = discord.utils.get(ctx.guild.roles, name=pixel_and_code_role_name)
    role_mention_str = role_to_mention.mention

    embededDescription = description="\n".join(description)
    embed = await get_embed_voting_message(question, embededDescription, role_mention_str, discord.Color.blue())

    # If you expect the command to take longer than 3 seconds, use this line:
    await ctx.response.defer()

    await ctx.followup.send(embed=embed)  # Send the poll as a follow-up message


@vote.error
async def vote_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        # Check if the interaction has been responded to
        if interaction.response.is_done():
            # If already responded (deferred), use followup
            await interaction.followup.send("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
        else:
            # If not responded yet, use response
            await interaction.response.send_message("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
    else:
        # Handle other types of errors
        if interaction.response.is_done():
            await interaction.followup.send("An error occurred while processing the command.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)


@bot.tree.command(name="help", description="Visa en lista över Pixies kommandon och events")
@app_commands.checks.has_any_role(pixel_and_code_role_name)
async def help(ctx: discord.Interaction):
    
        pixies_channel = discord.utils.get(ctx.guild.channels, name=pixies_channel_name)
        pixies_channel_str = ""

        if pixies_channel is None:
            pixies_channel_str = "(Ingen kanal är uppsatt för pixie-push)"
        else:
            pixies_channel_str = pixies_channel.mention

        embed = await create_help_embed_message(pixies_channel_str, discord.Color.yellow())

        await ctx.response.defer()
        await ctx.followup.send(embed=embed)

@help.error
async def help_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        # Check if the interaction has been responded to
        if interaction.response.is_done():
            # If already responded (deferred), use followup
            await interaction.followup.send("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
        else:
            # If not responded yet, use response
            await interaction.response.send_message("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
    else:
        # Handle other types of errors
        if interaction.response.is_done():
            await interaction.followup.send("An error occurred while processing the command.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)


@bot.tree.command(name="summarize_beta", description="Summera chathistoriken.")
@app_commands.describe(limit="Summeringsgräns, 100 är max gräns.")
@app_commands.checks.has_any_role(pixel_and_code_role_name)
async def summarize(ctx: discord.Interaction, limit: int):
    # Ensure the limit does not exceed 100
    if limit > 100:
        await ctx.response.send_message("Gränsen kan inte vara högre än 100. Försök igen med en lägre gräns.")
        return

    # Defer the response as the next operations might take longer
    await ctx.response.defer()

     # Send an initial update to the user after deferring
    await ctx.followup.send("Ett ögonblick så ska jag summera historiken.")

    summary = await get_chat_history_by_limit(ctx, limit, gpt_summary_instruction)

    try:
        # Process the summary (e.g., sending to a thread, polling for a response, etc.)
        user_id = str(ctx.user.id)
        thread_id = await get_or_create_thread(user_id, client)
        await send_user_message(thread_id, summary, client)
        run_id = await create_and_poll_run(thread_id, SUMMARY_ASSISTANT_ID, summary_client)  
        embededResponse = await retrieve_response(thread_id, client)

        # Send the processed response as a follow-up
        await ctx.followup.send(embed = embededResponse)
    except Exception as e:
        print(e)
        # Send an error message as a follow-up if an exception occurs
        await ctx.followup.send("Sorry, I encountered an error. Please try again later.")


@summarize.error
async def summarize_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        # Check if the interaction has been responded to
        if interaction.response.is_done():
            # If already responded (deferred), use followup
            await interaction.followup.send("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
        else:
            # If not responded yet, use response
            await interaction.response.send_message("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
    else:
        print(f"An error occurred: {error}")  # Alternatively, use print for simple logging

        # Handle other types of errors
        if interaction.response.is_done():
            await interaction.followup.send("An error occurred while processing the command.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)


@bot.tree.command(name="toggle_task", description="Toggle the scheduled message task on or off.")
@app_commands.checks.has_any_role(bot_creator_role_name)
async def toggle_task(ctx: discord.Interaction):
    global is_task_active

    is_task_active = not is_task_active
    status = "active" if is_task_active else "paused"
    message = f"Scheduled message task is now {status}."
    print(message)
    await ctx.response.send_message(message, ephemeral=True)

@toggle_task.error
async def toggle_task_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        # Check if the interaction has been responded to
        if interaction.response.is_done():
            # If already responded (deferred), use followup
            await interaction.followup.send("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
        else:
            # If not responded yet, use response
            await interaction.response.send_message("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
    else:
        print(f"An error occurred: {error}")  # Alternatively, use print for simple logging

        # Handle other types of errors
        if interaction.response.is_done():
            await interaction.followup.send("An error occurred while processing the command.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)

@bot.tree.command(name="is_task_running", description="Checks if the scheduled message task is active or paused.")
@app_commands.checks.has_any_role(bot_creator_role_name)  # Adjust role check as needed
async def is_task_running(ctx: discord.Interaction):
    global is_task_active

    await ctx.response.send_message(f"Is Task scheduled_message active: {is_task_active}", ephemeral=True)

@is_task_running.error
async def is_task_running_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        # Check if the interaction has been responded to
        if interaction.response.is_done():
            # If already responded (deferred), use followup
            await interaction.followup.send("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
        else:
            # If not responded yet, use response
            await interaction.response.send_message("Ledsen, men du kan tyvärr inte använda detta kommando. Prova gärna 'ask' istället.", ephemeral=True)
    else:
        print(f"An error occurred: {error}")  # Alternatively, use print for simple logging

        # Handle other types of errors
        if interaction.response.is_done():
            await interaction.followup.send("An error occurred while processing the command.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)

# Command definition for "ask_the_bot"
@bot.tree.command(name="ask", description="Ställ frågor till boten om Pixel&Code.")
@app_commands.describe(question="Ställ en fråga.")
async def ask(ctx: discord.Interaction, question: str):
    try:
        user_id = str(ctx.user.id)  # Get user ID as string
        await ctx.response.send_message(question)

         # Here we check if somebody is asking who is the best - Kay ofcourse
        if "who is the best" in question.lower() or "vem är den bästa" in question.lower():
            embededMessage = await get_embed_message("Svar", f"Giventvis <@{user_id}>", discord.Color.pink())
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


# Check if the DISCORD_TOKEN or OPENAI_API_KEY or ASSISTANT_ID is not empty
verify_env_variables(DISCORD_TOKEN, OPENAI_API_KEY, ASSISTANT_ID, SUMMARY_ASSISTANT_ID)

# Run the bot using the Discord token
bot.run(DISCORD_TOKEN)

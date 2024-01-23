import openai
import discord
import os

from utils import get_embed_message, verify_env_variables, get_or_create_thread, create_thread, cleanup_inactive_threads, get_embed_voting_message, create_help_embed_message
from messaging import send_user_message, create_and_poll_run, retrieve_response
from constants import pixies_channel_name, pixel_and_code_role_name, gpt_instruction

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


# Command definition for summarizing chat history
@bot.tree.command(name="summarize(beta)", description="Summera chathistoriken.")
@app_commands.describe(limit="Summeringsgräns, 100 är rekomenderad max gräns (Men prova högre om du vill).")
@app_commands.checks.has_any_role(pixel_and_code_role_name  )
async def summarize(ctx: discord.Interaction, limit: int):    

    # Check if the limit is positive
    if limit <= 0:
        await ctx.response.send_message("Please provide a positive number for the limit.")
        return

    # Defer the response as the next operations might take longer
    await ctx.response.defer()

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

    try:
        # Process the summary (e.g., sending to a thread, polling for a response, etc.)
        user_id = str(ctx.user.id)
        thread_id = await get_or_create_thread(user_id, client)
        await send_user_message(thread_id, summary, client)
        run_id = await create_and_poll_run(thread_id, ASSISTANT_ID, client)  
        embededResponse = await retrieve_response(thread_id, client)

        # Send the processed response as a follow-up
        await ctx.followup.send(embed = embededResponse)
    except Exception as e:
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
verify_env_variables(DISCORD_TOKEN, OPENAI_API_KEY, ASSISTANT_ID)

# Run the bot using the Discord token
bot.run(DISCORD_TOKEN)

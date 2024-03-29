# messaging.py

import asyncio
import openai

from utils import split_messages

# Function to send a message from the user to the OpenAI API thread
async def send_user_message(thread_id, user_input, client: openai.Client):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: client.beta.threads.messages.create(
        role="user",
        content=user_input,
        thread_id=thread_id
    ))

# Function to create a run with the assistant and poll for its completion
async def create_and_poll_run(thread_id, assistant_id, client: openai.Client):
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
async def retrieve_response(thread_id, client: openai.Client):
    try:
        loop = asyncio.get_running_loop()
        messages = await loop.run_in_executor(None, lambda: client.beta.threads.messages.list(thread_id=thread_id))
        assistant_messages = [m for m in messages.data if m.role == 'assistant']

        if assistant_messages:
            assistant_reply = assistant_messages[0].content[0].text.value
            
            split_message = split_messages(assistant_reply)
            
            return split_message
        else:
             return "Error: Sorry, I couldn't fetch a response. Please try again later or ask a different question."

    except Exception as e:
            print(f"Error in retrieve_response: {e}")
            return await "Error: An error occurred while fetching the response."


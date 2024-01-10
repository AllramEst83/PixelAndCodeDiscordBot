# Pixel&Code Discord Bot

## Overview
This repository contains the source code for the Pixel&Code Discord Bot, an advanced assistant designed to answer queries about the Pixel&Code company. Utilizing the OpenAI GPT model, this bot provides informative and context-aware responses to various user inquiries, enhancing the user experience on the Discord platform.

## Features
- **Slash Command Integration:** Users can interact with the bot using intuitive slash commands, offering a seamless and user-friendly experience.
- **OpenAI GPT Integration:** The bot leverages the powerful GPT model from OpenAI for generating accurate and relevant responses.
- **Asynchronous Processing:** Ensures efficient handling of user requests and interactions, maintaining optimal performance even under load.
- **Secure API Key Handling:** API keys and sensitive data are securely managed, ensuring best practices for security and privacy.

## Recent Updates
- **Transition to Slash Commands:** Migrated from traditional prefix commands to modern slash commands for an improved user interface.
- **Asynchronous OpenAI API Calls:** Implemented non-blocking calls to OpenAI's API, ensuring the bot remains responsive and efficient.
- **Dynamic Response Generation:** Enhanced the bot's ability to generate dynamic responses based on user input, leveraging the latest GPT model.
- **Error Handling and Logging:** Improved error handling and logging mechanisms for smoother operation and easier debugging.

## Configuration
To run the Pixel&Code Discord Bot, you will need to create a `config.py` file in the root directory. This file should contain your Discord bot token, OpenAI API key, and the assistant ID. Your `config.py` should look like this:

```python
# config.py
DISCORD_TOKEN = 'your_discord_bot_token_here'
OPENAI_API_KEY = 'your_openai_api_key_here'
ASSISTANT_ID = 'your_assistant_id_here'

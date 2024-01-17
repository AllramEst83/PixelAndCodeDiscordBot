# Pixel&Code Discord Bot

## Overview
This repository contains the source code for the Pixel&Code Discord Bot, a sophisticated assistant designed for answering queries about Pixel&Code. Incorporating OpenAI's GPT model, it offers context-aware and informative responses on Discord, enhancing user interaction and knowledge about the company.

## Features
- **Slash Command Integration**: Engages users with intuitive slash commands for a seamless experience.
- **User-Specific Thread Management**: Maintains individual conversation threads for users, improving context continuity.
- **OpenAI GPT Integration**: Utilizes OpenAI's GPT model for generating accurate and relevant responses.
- **Asynchronous Processing**: Handles user requests efficiently, ensuring optimal performance.
- **Secure API Key Handling**: Manages API keys and sensitive data securely, adhering to best practices for security and privacy.

## Recent Updates
- **Transition to Slash Commands**: Shifted from traditional prefix commands to modern slash commands for enhanced user interaction.
- **Thread-Based User Interaction**: Implemented user-specific threads for maintaining conversation history and context.
- **30-Minute Timeout Mechanism**: Introduced a timeout system to manage resources and improve efficiency, including deletion of inactive threads at OpenAI's end.
- **Error Handling and Logging**: Enhanced error handling and logging for smoother operations and easier troubleshooting.

## Configuration
To run the Pixel&Code Discord Bot, you will need to create a `.env` file in the root directory. This file should contain your Discord bot token, OpenAI API key, and the assistant ID. Your `.env` should look like this:

```python
# .env
DISCORD_TOKEN = 'your_discord_bot_token_here'
OPENAI_API_KEY = 'your_openai_api_key_here'
ASSISTANT_ID = 'your_assistant_id_here'

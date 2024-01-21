# Pixel&Code Discord Bot

## Overview
The Pixel&Code Discord Bot is an advanced assistant, leveraging OpenAI's GPT model to deliver context-aware and informative responses on Discord. It is specifically designed to enhance user interaction and knowledge about the Pixel&Code community.

## Features
- **Slash Command Integration**: Provides a user-friendly experience with intuitive slash commands.
- **User-Specific Thread Management**: Manages individual conversation threads for each user, ensuring continuity and context in interactions.
- **OpenAI GPT Integration**: Employs OpenAI's GPT model for generating accurate and relevant responses.
- **Asynchronous Processing**: Handles user requests efficiently, ensuring optimal performance.
- **Secure API Key Handling**: Manages API keys and sensitive data securely, adhering to best practices for security and privacy.
- **Welcome and Exit Messages**: Greets new members and bids farewell to departing ones, enhancing community engagement.
- **Customizable Role Mentions**: Incorporates role mentions in welcome and exit messages for specific notifications.

## Recent Updates
- **Transition to Slash Commands**: Shifted from traditional prefix commands to modern slash commands for enhanced user interaction.
- **Thread-Based User Interaction**: Implemented user-specific threads for maintaining conversation history and context.
- **30-Minute Timeout Mechanism**: Introduced a timeout system to manage resources and improve efficiency, including deletion of inactive threads at OpenAI's end.
- **Error Handling and Logging**: Enhanced error handling and logging for smoother operations and easier troubleshooting.
- **Embed Messaging**: Added embed messaging for visually appealing and structured responses.
- **Member Join/Leave Notifications**: Implemented welcome and farewell messages with role mentions in embeds.

## Configuration
To run the Pixel&Code Discord Bot, you will need to create a `.env` file in the root directory. This file should contain your Discord bot token, OpenAI API key, and the assistant ID. Your `.env` should look like this:

```python
# .env
DISCORD_TOKEN = 'your_discord_bot_token_here'
OPENAI_API_KEY = 'your_openai_api_key_here'
ASSISTANT_ID = 'your_assistant_id_here'

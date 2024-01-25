# Pixel&Code Discord Bot

## Overview
The Pixel&Code Discord Bot is a sophisticated assistant integrated with OpenAI's GPT model. Designed to provide informative and context-aware interactions within the Pixel&Code community on Discord.

## Features

### Core Features
- **Slash Command Integration**: Utilizes slash commands for enhanced user interaction.
- **Asynchronous Processing**: Ensures efficient handling of user requests.
- **Secure API Key Handling**: Manages sensitive data securely.
- **Discord and OpenAI GPT Integration**: Leverages OpenAI's GPT for generating responses and Discord API for communication.

### Interaction and Messaging
- **User-Specific Thread Management**: Maintains individual conversation threads for personalized interaction.
- **Welcome and Exit Messages**: Sends custom messages for new members joining and members leaving.
- **Embed Messaging**: Uses embeds for structured and visually appealing responses.
- **Direct Messaging**: Capable of sending direct messages to users.

### Scheduled and Supportive Messages
- **Random Encouraging Messages**: Sends scheduled motivational messages to a designated channel.
- **Time-Managed Messaging**: Schedules messages based on predefined times and checks for weekdays.

### Advanced Command Handling
- **Voting Mechanism**: Allows creation of polls with a maximum of 10 options.
- **Customizable Role Mentions**: Supports role mentions in messages for specific notifications.
- **Error Handling and Logging**: Enhances reliability with effective error handling and logging.

### OpenAI GPT Integration for Enhanced Responses
- **Chat Summarization**: Summarizes chat histories using GPT summary instructions.
- **Contextual Responses**: Generates responses based on user interactions and questions.

### User Interaction and Engagement
- **Member Join/Leave Notifications**: Notifies when a member joins or leaves the server.
- **Interactive Commands for Users**: Includes commands like `vote`, `help`, and `ask` for user engagement.

### Security and Performance
- **Environment Variable Verification**: Checks for the presence of necessary environment variables.
- **Thread Cleanup Mechanism**: Manages resource efficiency by cleaning up inactive threads.

### Additional Features
- **Task Management Commands**: Includes commands to toggle scheduled tasks and check task status.
- **Role-Based Command Access**: Restricts certain commands to users with specific roles.

## Configuration
To run the Pixel&Code Discord Bot, create a `.env` file with the following variables:
- `DISCORD_TOKEN`: Your Discord bot token.
- `OPENAI_API_KEY`: Your OpenAI API key.
- `ASSISTANT_ID`: Your assistant ID for OpenAI.
- `SUMMARY_ASSISTANT_ID`: Your summary assistant ID for OpenAI.
- `GUILD_ID`: The Guild ID for your Discord server.
- `PIXIE_PUSH_CHANNEL`: The channel ID for sending scheduled messages.
- `BOT_CREATOR_USER_ID`: The user ID of the bot creator for direct messaging.
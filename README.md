Telegram AI Bot
This project is a Telegram bot powered by Google Gemini API and other integrations to handle tasks like sentiment analysis, image/file uploads, web search, and storing user data in MongoDB. The bot uses several AI features, including generating content, performing sentiment analysis, and providing web search results.

Features
Welcome New Users: The bot welcomes users and requests their phone number using the contact button, saving the information in MongoDB.
Sentiment Analysis: Sentiment analysis of user messages with feedback using emojis.
Gemini API Integration: Generates AI responses based on user input using Google Gemini API.
File Upload Analysis: Supports file uploads, including image and PDF analysis.
Web Search: Allows users to search the web, summarizing the results with links.
MongoDB Integration: Stores user information, chat history, and file metadata in MongoDB.

Technologies
Python 3.11+
Telegram API
Google Gemini API
MongoDB
TextBlob
requests
python-dotenv
Pillow (PIL)
Setup
Prerequisites
Python 3.11 or later.
MongoDB setup (either local or hosted like MongoDB Atlas).
Telegram Bot Token (you can obtain it by creating a bot through BotFather).
Google Gemini API Key.
SerpAPI Key for web search integration.

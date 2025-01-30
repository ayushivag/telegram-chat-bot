import logging
from telegram import Update, InputFile, Contact
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pymongo import MongoClient
from textblob import TextBlob
import google.generativeai as genai
import requests
import os
import io
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB Setup
client = MongoClient(os.getenv("MONGO_URI"))

db = client["telegram_bot"]
users_collection = db["users"]
chat_history_collection = db["chat_history"]
files_collection = db["files"]

# Gemini API Setup
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Start Command
async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = update.message.chat_id

    # Check if user already exists
    if users_collection.find_one({"chat_id": chat_id}):
        await update.message.reply_text("Welcome back!")
    else:
        # Save user details in MongoDB
        users_collection.insert_one({
            "first_name": user.first_name,
            "username": user.username,
            "chat_id": chat_id,
            "phone_number": None,
            "referral_points": 0
        })
        await update.message.reply_text("Welcome! Please share your phone number using the contact button.", reply_markup=ContactRequest())

# Handle contact sharing and store phone number
async def handle_contact(update: Update, context: CallbackContext):
    contact: Contact = update.message.contact
    chat_id = update.message.chat_id

    # Save phone number in MongoDB
    users_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"phone_number": contact.phone_number}}
    )
    await update.message.reply_text("Thank you! Your phone number has been saved.")

# Handle Messages (With Gemini API & Sentiment Analysis)
async def handle_message(update: Update, context: CallbackContext):
    user_input = update.message.text
    chat_id = update.message.chat_id

    # Perform sentiment analysis
    sentiment = TextBlob(user_input).sentiment.polarity
    emoji = "😊" if sentiment > 0 else "😠" if sentiment < 0 else ""

    # Get response from Gemini API
    response = model.generate_content(user_input)

    # Save chat history in MongoDB
    chat_history_collection.insert_one({
        "chat_id": chat_id,
        "user_input": user_input,
        "bot_response": response.text,
        "timestamp": update.message.date
    })

    # Send the response with sentiment emoji (if any)
    await update.message.reply_text(f"{response.text} {emoji}")

# Handle Image/File Upload (With Gemini API Analysis)
async def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    chat_id = update.message.chat_id

    # Download the file
    file_id = file.file_id
    new_file = await update.message.bot.get_file(file_id)
    file_path = new_file.file_path
    file_data = await new_file.download_as_bytearray()

    # Save file metadata in MongoDB
    files_collection.insert_one({
        "chat_id": chat_id,
        "file_name": file.file_name,
        "file_id": file.file_id,
        "file_size": file.file_size,
        "timestamp": update.message.date
    })

    # For image files (JPG/PNG) - use PIL to analyze
    if file.file_name.endswith(('.jpg', '.jpeg', '.png')):
        image = Image.open(io.BytesIO(file_data))
        description = "Image Analysis: This is an image file."
        await update.message.reply_text(description)

    # For PDF files - a simple description
    elif file.file_name.endswith('.pdf'):
        description = "PDF Analysis: This is a PDF file."
        await update.message.reply_text(description)

# Web Search Command
async def websearch(update: Update, context: CallbackContext):
    # Check if user has provided a query
    if context.args:
        query = " ".join(context.args)
    else:
        await update.message.reply_text("Please provide a search query.")
        return

    # Perform the web search
    search_url = f"https://api.serpapi.com/search?q={query}&api_key={os.getenv('SERPAPI_API_KEY')}"
    search_results = requests.get(search_url).json()

    # Generate a summary of search results
    if "organic_results" in search_results:
        summary = "Top search results:\n"
        for result in search_results["organic_results"][:5]:
            summary += f"- {result['title']}: {result['link']}\n"
        await update.message.reply_text(summary)
    else:
        await update.message.reply_text("No search results found.")

# Main function to run the bot
def main():
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("websearch", websearch))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.DOCUMENT, handle_document))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()

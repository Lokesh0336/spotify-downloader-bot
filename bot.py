import os
import subprocess
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

# Directly adding Spotify API credentials
SPOTIFY_CLIENT_ID = "3d3ca7d9786c4e5a8595e691afe14154"
SPOTIFY_CLIENT_SECRET = "c9f9f3ba13b14cc69bea2e405c05ab75"

# Directly adding Telegram bot token
BOT_TOKEN = "7087446727:AAGVvWy17UM0prkrgMBv-oicg5F1qFyHBXA"

# Initialize Spotify API client
spotify_client = Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
    )
)

# Global variable to store search results
search_results = []

# Function to handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! You can search for a song by typing the album or movie name. 🎶"
    )

# Function to handle search and send paginated results
async def search_and_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    
    if not query:
        await update.message.reply_text("Please provide a search query.")
        return
    
    await update.message.reply_text(f"Searching for '{query}' on Spotify...")
    
    try:
        # Search for tracks on Spotify
        results = spotify_client.search(q=query, type="track", limit=5)  # Limit to 5 results
        tracks = results.get("tracks", {}).get("items", [])
        
        if not tracks:
            await update.message.reply_text("No results found. Try a different search query.")
            return
        
        # Store search results globally
        global search_results
        search_results = tracks

        # Create a list of buttons for each track
        keyboard = [
            [InlineKeyboardButton(f"{track['name']} - {', '.join([artist['name'] for artist in track['artists']])}",
                                  callback_data=f"track_{index}") for index, track in enumerate(tracks)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Ask user to choose a track
        await update.message.reply_text(
            "Here are the search results. Choose a song to download:",
            reply_markup=reply_markup
        )
    
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

# Function to handle selection of a song
async def select_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Extract track index from callback data
    track_index = int(query.data.split("_")[1])
    
    # Get the selected track details
    track = search_results[track_index]
    track_name = track["name"]
    track_artist = ", ".join([artist["name"] for artist in track["artists"]])
    track_url = track["external_urls"]["spotify"]
    
    await query.edit_message_text(
        f"Selected: {track_name} by {track_artist}\nDownloading..."
    )
    
    try:
        # Clear any existing audio files before downloading a new one
        for file in os.listdir("."):
            if file.endswith(".mp3"):
                os.remove(file)
        
        # Download the song using spotdl
        command = [
            "C:\\Users\\PC\\AppData\\Roaming\\Python\\Python310\\Scripts\\spotdl.exe",
            track_url
        ]
        subprocess.run(command, check=True)
        
        # Find the downloaded file (assuming it has the .mp3 extension)
        for file in os.listdir("."):
            if file.endswith(".mp3"):
                with open(file, "rb") as audio:
                    await query.message.reply_audio(audio)
                os.remove(file)  # Clean up the downloaded file
                return
        
        await query.message.reply_text("Failed to find the downloaded file.")
    
    except Exception as e:
        await query.message.reply_text(f"An error occurred: {e}")

# Main function to start the bot
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_download))
    application.add_handler(CallbackQueryHandler(select_song))  # Handle song selection

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()

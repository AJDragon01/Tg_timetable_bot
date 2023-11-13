import logging
import telegram.ext.filters as filters
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler
from .handlers import add_shift_conversation_handler, view_schedule_handler, delete_shift_handler, start, help_command
from telegram import Update



# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def set_commands(application):
    commands = [
        BotCommand(command="/start", description="Start the bot"),
        BotCommand(command="/help", description="Show help"),
        BotCommand(command="/add", description="Add a shift"),
        BotCommand(command="/delete", description="Delete a shift"),
        BotCommand(command="/view", description="View schedule")
    ]
    application.bot.set_my_commands(commands)

def main():
    application = Application.builder().token('6491579364:AAEOz0I1plMsEqd5QVCCcLas0W4-wGfcNuk').build()

    # Set the commands
    set_commands(application)

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(add_shift_conversation_handler)
    application.add_handler(view_schedule_handler)
    application.add_handler(delete_shift_handler)
    application.add_handler(add_shift_conversation_handler)
    

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()

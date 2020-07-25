from tg_token import token
from challenges import challenges
from datetime import datetime
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, PicklePersistence
from telegram import ParseMode

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hi! send /help if you don't know what to do")

def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text("""
    Available commands:
    /start: Print start message.
    /help: Print this help message.
    /flag: Submit flag. Usage: /flag [flag].
    /scoreboard: Print scoreboard.
    """)

def initialize_scoreboard(pp):
    """Create scoreboard if necessary."""
    bot_data =  pp.get_bot_data()
    if not "scoreboard" in bot_data.keys():
        bot_data["scoreboard"] = {}
        pp.update_bot_data(bot_data)

def initialize_user(scoreboard, user_id, user_name):
    """Add user to scoreboard if necessary."""
    if not user_id in scoreboard.keys():
        scoreboard[user_id] = {
            "user_name": user_name,
            "solved_challenges" : [],
            "score" : 0,
            "last_update": datetime.now().timestamp()
        }

def update_user_score(scoreboard, user_id, challenge, points):
    """Updates score if challenge has not been solved yet. Returns true on succes, false otherwise."""
    if not challenge in scoreboard[user_id]["solved_challenges"]:
        scoreboard[user_id]["solved_challenges"].append(challenge)
        scoreboard[user_id]["score"] += points
        scoreboard[user_id]["last_update"] = datetime.now().timestamp()
        return True
    else:
        return False

def check_flag(flag):
    """Checks if submited flag is correct. If correct returns tuple (challenge, points) else returns (None, None)."""
    for c in challenges:
        if c["flag"] == flag:
            return (c["name"], c["points"])
    return (None, None)

def check_flag_command(update, context):
    """Handle /flag command."""
    if len(context.args) != 1:
        update.message.reply_text("Usage: /flag [flag]")
    else:
        user_id = update["message"]["from_user"]["id"]
        user_name = update["message"]["from_user"]["first_name"]
        scoreboard = context.bot_data["scoreboard"]

        initialize_user(scoreboard, user_id, user_name)

        (challenge, points) = check_flag(context.args[0])
        
        if challenge:
            if update_user_score(scoreboard, user_id, challenge, points):
                update.message.reply_text("Flag is correct. Congrats on solving {}! You have been awarded {} points.".format(challenge, points))
            else:
                update.message.reply_text("Challenge {} already solved.".format(challenge))
        else:        
            update.message.reply_text("Flag is incorrect. Try harder!".format(context.args[0]))

def print_scoreboard(update, context):
    scoreboard = context.bot_data["scoreboard"]
    top = sorted(scoreboard.items(), key = lambda x: (-x[1]['score'], x[1]['last_update']))[:10]
    
    if top:
        table  = "```\nTop 10:\n"
        table += "".join(["{}\. {}:   {}\n".format(i+1, u[1]['user_name'],u[1]['score']) for i, u in enumerate(top)])
        table += "```"

        update.message.reply_text(table, parse_mode = ParseMode.MARKDOWN_V2)
        
        user_id = update["message"]["from_user"]["id"]
        top_ids = [u[0] for u in top]
        
        if (not user_id in top_ids) and (user_id in scoreboard.keys()):
            update.message.reply_text("```\nYour score is {} points.```".format(scoreboard[user_id]["score"]), parse_mode = ParseMode.MARKDOWN_V2)
    else:
        update.message.reply_text("No flags submited yet.")

def main():
    """Start the bot."""
    # Perstist bot_data which contains the scoreboard
    pp = PicklePersistence(filename='ctf_bot_scores', store_bot_data = True, store_user_data = False, store_chat_data = False)
    
    # Initialize scoreboard if necessary
    initialize_scoreboard(pp)

    # Create the Updater and pass your bot's token and the persistence object.
    updater = Updater(token, persistence=pp, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("flag", check_flag_command))
    dp.add_handler(CommandHandler("scoreboard", print_scoreboard))

    # on other message print help
    dp.add_handler(MessageHandler(Filters.text, help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
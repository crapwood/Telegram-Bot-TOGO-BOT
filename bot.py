from pprint import pprint

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from how_far_from import haversine
import secrets
import logging

import requests
import model

logging.basicConfig(
    format='[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

updater = Updater(token=secrets.BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

what_to_look_for = ""
lati = 0
long = 0
result = {}
base_url_nearby = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


# photo_base_url = "https://maps.googleapis.com/maps/api/place/photo" TODO Pictures


def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    logger.info(f"> Start chat #{chat_id}")
    context.bot.send_message(chat_id=chat_id, text="Welcome to Find_places_near_ME")
    context.bot.send_message(chat_id=chat_id, text="Please send your location")


def respond(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    global what_to_look_for
    what_to_look_for = update.message.text
    params = {
        "location": f"{lati},{long}",
        "keyword": what_to_look_for,
        "rankby": "distance",
        "key": secrets.GOOGLE_API_KEY
    }
    r = requests.get(base_url_nearby, params)
    r.raise_for_status()
    global result
    result = r.json()
    print("\n\n")

    custom_keyboard = []

    for x in range(3):  # return the first 3 results
        how_far_are_you = haversine(long, lati, result['results'][x]['geometry']['location']['lng'],
                                    result['results'][x]['geometry']['location']['lat'])

        res = f"{result['results'][x]['name']}\n{how_far_are_you:.2f} km's away from you"

        custom_keyboard.append([InlineKeyboardButton(res, callback_data=x)])

    reply_markup = InlineKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=chat_id, text=f"This are the 3 nearest {what_to_look_for}s from your location",
                             reply_markup=reply_markup)


def locate(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user
    global lati, long
    lati = update.message.location.latitude
    long = update.message.location.longitude
    context.bot.send_message(chat_id=chat_id, text=f"SUCCESS!!!")
    context.bot.send_message(chat_id=chat_id,
                             text=f"{user_id['first_name']} {user_id['last_name']} you are currently in Ramla\n\nWhat are you looking for?")


def menu_actions(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    query = update.callback_query
    if query.data.isdigit():
        global result
        place_name = f"{result['results'][int(query.data)]['name']}"
        address = f"{result['results'][int(query.data)]['vicinity']}"

        person = {
            "chat_id": chat_id,
            "places": {f'{what_to_look_for}': {"name": place_name, "address": address}}
        }
        changes = {f'{what_to_look_for}': {"name": place_name, "address": address}}
        pprint(person)
        model.add_user_to_db(person, changes)
        context.bot.send_message(chat_id=chat_id, text="SUCCESS!!!", reply_markup=None)
    else:
        model.remove_place_from_db(chat_id, query.data)
        results = model.get_places_from_db(chat_id)
        custom_keyboard = []
        for place in results:
            custom_keyboard.append([InlineKeyboardButton(f"{place[0]}, {place[1]}", callback_data=place[1])])
        print(custom_keyboard)
        if len(custom_keyboard) > 0:
            reply_markup = InlineKeyboardMarkup(custom_keyboard)
        else:
            reply_markup = ""
        context.bot.send_message(chat_id=chat_id, text="SUCCESSFULLY REMOVE!!!", reply_markup=reply_markup)


def show_places(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    results = model.get_places_from_db(chat_id)
    print(results)
    custom_keyboard = []
    index = 0
    for place in results:
        place_remove = f"remove-{index}"
        custom_keyboard.append([InlineKeyboardButton(f"{place[0]}, {place[1]}", callback_data=place_remove)])
        index += 1
    reply_markup = InlineKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=chat_id, text="OK", reply_markup=reply_markup)


def main():
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    echo_handler = MessageHandler(Filters.text, respond)
    dispatcher.add_handler(echo_handler)

    location_handler = MessageHandler(Filters.location, locate)
    dispatcher.add_handler(location_handler)

    dispatcher.add_handler(CallbackQueryHandler(menu_actions))

    places_handler = CommandHandler('places', show_places)
    dispatcher.add_handler(places_handler)

    logger.info("* Start polling...")
    updater.start_polling()  # Starts polling in a background thread.
    updater.idle()  # Wait until Ctrl+C is pressed
    logger.info("* Bye!")


if __name__ == '__main__':
    main()

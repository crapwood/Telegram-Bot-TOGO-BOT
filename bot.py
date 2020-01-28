from pprint import pprint

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from how_far_from import haversine
from reverse_geocode import print_user_location
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
    context.bot.send_message(chat_id=chat_id, text="Welcome to TO GO BOT 🏦📮🛒")
    context.bot.send_message(chat_id=chat_id, text="Please send your location/live location for real time update")


def respond(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    global what_to_look_for
    what_to_look_for = update.message.text
    params = {
        "location": f"{lati},{long}",
        "keyword": what_to_look_for,
        "rankby": "distance",
        "language": "iw",
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
        hebrew_meter = "מטרים ממך"
        res = f"{result['results'][x]['name']} {how_far_are_you * 1000:.2f} {hebrew_meter}"

        custom_keyboard.append([InlineKeyboardButton(res, callback_data=x)])

    reply_markup = InlineKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=chat_id, text=f"These are the 3 nearest {what_to_look_for}s from your location",
                             reply_markup=reply_markup)


def locate(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user
    global lati, long
    if update.message:
        lati = update.message.location.latitude
        long = update.message.location.longitude
        logger.info(f'{lati}{long}')
        data = print_user_location(lati, long)
        context.bot.send_message(chat_id=chat_id, text=f"SUCCESS!!!")
        context.bot.send_message(chat_id=chat_id,
                                 text=f"{user_id['first_name']} {user_id['last_name']} you are currently in {data}\n\nWhat are you looking for? ex. Bank, Supermarket, Doar, בית ספר")
    else:
        lati, long
        lati = update.edited_message.location.latitude
        long = update.edited_message.location.longitude
        logger.info(f'{lati}{long}')
        data = print_user_location(lati, long)
        # context.bot.send_message(chat_id=chat_id, text=f"SUCCESS!!!")
        context.bot.send_message(chat_id=chat_id,
                                 text=f"{user_id['first_name']} {user_id['last_name']} you are currently in {data} and moving\nyou can look for a place and see that your distance from it has change")


def menu_actions(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    query = update.callback_query
    global lati, long
    if query.data.isdigit():
        global result
        # pprint(result)
        place_name = f"{result['results'][int(query.data)]['name']}"
        address = f"{result['results'][int(query.data)]['vicinity']}"
        longitude = f"{result['results'][int(query.data)]['geometry']['location']['lng']}"
        latitude = f"{result['results'][int(query.data)]['geometry']['location']['lat']}"

        person = {
            "chat_id": chat_id,
            "places": {f'{what_to_look_for}': {"name": place_name, "address": address, "long": longitude, "lat": latitude}}
        }
        changes = {f'{what_to_look_for}': {"name": place_name, "address": address, "long": longitude, "lat": latitude}}
        pprint(person)
        model.add_user_to_db(person, changes)
        context.bot.send_message(chat_id=chat_id, text="SUCCESS!!! TO ADD MORE PLACE JUST TYPE IN THE PLACE", reply_markup=None)
    else:
        model.remove_place_from_db(chat_id, query.data)
        results = model.get_places_from_db(chat_id, lati, long)
        custom_keyboard = []
        for place in results:
            temp = place[2] * 1000
            hebrew_meter = "מטרים ממך"
            custom_keyboard.append([InlineKeyboardButton(f"{place[0]} {temp:.2f} {hebrew_meter}", callback_data=place[1])])
        if len(custom_keyboard) > 0:
            reply_markup = InlineKeyboardMarkup(custom_keyboard)
            context.bot.send_message(chat_id=chat_id, text="SUCCESSFULLY REMOVE!!!", reply_markup=reply_markup)
        else:
            reply_markup = ""
            context.bot.send_message(chat_id=chat_id, text="SUCCESSFULLY REMOVE!!!", reply_markup=reply_markup)


def show_places(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    global lati, long
    results = model.get_places_from_db(chat_id, lati, long)
    print(results)
    custom_keyboard = []
    index = 0
    for place in results:
        place_remove = f"remove-{index}"
        temp = place[2] * 1000
        hebrew_meter = "מטרים ממך"
        custom_keyboard.append([InlineKeyboardButton(f"{place[0]} {temp:.2f} {hebrew_meter}", callback_data=place_remove)])
        index += 1
    reply_markup = InlineKeyboardMarkup(custom_keyboard)
    if len(custom_keyboard) > 0:
        context.bot.send_message(chat_id=chat_id, text="OK", reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=chat_id, text="YOU'RE TO GO LIST IS DONE!!! 👍👍👍", reply_markup=reply_markup)


def follow(update: Update, context: CallbackContext):
    pass


def main():
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    places_handler = CommandHandler('places', show_places)
    dispatcher.add_handler(places_handler)

    follow_handler = CommandHandler('follow', follow)
    dispatcher.add_handler(follow_handler)

    echo_handler = MessageHandler(Filters.text, respond)
    dispatcher.add_handler(echo_handler)

    location_handler = MessageHandler(Filters.location, locate)
    dispatcher.add_handler(location_handler)

    dispatcher.add_handler(CallbackQueryHandler(menu_actions))

    logger.info("* Start polling...")
    updater.start_polling()  # Starts polling in a background thread.
    updater.idle()  # Wait until Ctrl+C is pressed
    logger.info("* Bye!")


if __name__ == '__main__':
    main()

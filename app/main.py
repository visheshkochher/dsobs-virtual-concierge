# uWSGI Deployed
# Expose VM endpoint
# CD via git

#https://gabimelo.medium.com/developing-a-flask-api-in-a-docker-container-with-uwsgi-and-nginx-e089e43ed90e
# Jai Khanna7:23 PM
# https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/
# Jai Khanna7:36 PM
# https://support.terra.bio/hc/en-us/articles/360035638032-Publish-a-Docker-container-image-to-Google-Container-Registry-GCR-

import logging
from heyoo import WhatsApp
from flask import Flask, request, make_response
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_ID = "1N1KhNKfTwVa69qo3-mKjWZXwK_kdlHpzhb_CMAkQAZc"
credential = ServiceAccountCredentials.from_json_keyfile_name("config.json",
                                                              ["https://spreadsheets.google.com/feeds",
                                                               "https://www.googleapis.com/auth/spreadsheets",
                                                               "https://www.googleapis.com/auth/drive.file",
                                                               "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(credential)


def get_ghseet_data(worksheet_name):
    client = gspread.authorize(credential)
    gsheet = client.open("DoscoBot").worksheet(worksheet_name)
    values = gsheet.get_all_records()
    return values


TOPICS = ['Alumni Events', 'Dosco Card Benefits', 'Dosco Memorabilia', 'DSOBS Activities']
TOPIC_MAPPING = {'Alumni Events': 'Events',
                 'Dosco Card Benefits': 'Benefits',
                 'Dosco Memorabilia': 'Memorabilia',
                 'DSOBS Activities': 'Activities'}
MAIN_DATA = {x: get_ghseet_data(x) for x in TOPIC_MAPPING.values()}

# Initialize Flask App
app = Flask(__name__)

# Initiate message list for this session
MSG_LIST = []
messenger = WhatsApp(
    # 'EAATj5Hxu7GEBALZBHCrDeEykQqO6gNDWFsh3SyKhH0sarfedZCJs7LgZB5oCDkAIKZBjCCWOljRSiZCZArFr1mIFblrYubyIx8SGaLNGSZBSE1T8alEpxmGerW5GvsiAAPZA6FegVLXyEX2x5qA0LVhe3StyweZB7T2xy9ZBcvQZCmie2i0zgnPBWqMXBWsitakPVZA19pQO0dJsGuHzPuDZB5MHa',
    'EAAJL3Mk0aHwBAA7LWZCGEIYvRyKsh1ZAlewWU495EzJzjDKQlLqZCt7hDuhwB6dN31fXR8PTlxapeZAaNpvpVZA2dRl6MpOC8tZA81HmikkNAasFPjybymibXjvuURpQKsLUQ8hUPsu2Lbj6R9fcbBVUPwSXPTlQnLzE8WYCnOZBk7pqix7HruukOOzhts5MRp5usYytI7blwZDZD',
    phone_number_id='105858425809204')  # TEST
    # phone_number_id='105580025836898')  # OFFICIAL
VERIFY_TOKEN = "CHANDBAGH"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def create_button(category, item_list, header, body):
    button = {
        "header": header,
        "body": body,
        # "footer": "Get immediate delivery",
        "action": {
            "button":
                "Make a selection",
            "sections": [{
                "title":
                    category,
                "rows": [
                    {
                        "id": f'{category}_{x}',
                        "title": x,
                        "description": ""
                    } for x in item_list
                ],
            }],
        },
    }
    return button


@app.route("/", methods=["GET", "POST"])
def hook():
    global MSG_LIST
    max_index = MSG_LIST[-1]['id'] if MSG_LIST else 0

    # FOR WEBHOOK TOKEN VERIFICATION
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            logging.info("Verified webhook")
            response = make_response(request.args.get("hub.challenge"), 200)
            response.mimetype = "text/plain"
            return response
        logging.error("Webhook Verification failed")
        return "Invalid verification token"

    # Handle Webhook Subscriptions
    data = request.get_json()
    logging.info("Received webhook data: %s", data)
    changed_field = messenger.changed_field(data)
    if changed_field == "messages":
        new_message = messenger.get_mobile(data)

        if new_message:  # RESPONSE TO MESSAGES
            mobile = messenger.get_mobile(data)
            name = messenger.get_name(data)
            message_type = messenger.get_message_type(data)
            logging.info(
                f"New Message; sender:{mobile} name:{name} type:{message_type}")
            print('printing_data')
            print(data)
            print('printed_data')
            data_dict = dict(id=max_index + 1,
                             mobile=mobile,
                             name=name,
                             message_type=message_type,
                             data=data
                             )
            MSG_LIST.append(data_dict)
            USER_MSG_LIST = [x for x in MSG_LIST if x['mobile'] == mobile]
            PREV_USER_MSG = USER_MSG_LIST[-2] if len(USER_MSG_LIST) >= 2 else []

            if message_type == "text":  # AND PREV MESSAGE NOT SENT MY BOT IN LAST 2 MINS
                message = messenger.get_message(data)
                name = messenger.get_name(data)
                logging.info("Message: %s", message)
                messenger.send_message(messenger.get_message(MSG_LIST[-1]['data']), mobile)
                # messenger.send_image(dsobs_header_url, mobile)
                messenger.send_button(
                    recipient_id=mobile,
                    button=create_button(category='Categories',
                                         item_list=TOPICS,
                                         header='Welcome',
                                         body="""Hello and welcome to the DSOBS chatbot! 

This chatbot is designed to connect you with your fellow ex-Doscos and keep you up-to-date on the latest news and events within the community. 

Find out about *upcoming events*, avail *DoscoCard Benefits*, or *Explore Memorabilia*. 

So sit back, relax, and let us help you stay connected with Chandbagh!

*Select a category to explore community offers ane events*""")

                )

            elif message_type == "interactive":
                message_response = messenger.get_interactive_response(data)
                interactive_type = message_response.get("type")
                message_id = message_response[interactive_type]["id"]
                message_text = message_response[interactive_type]["title"]
                interactive_message = f"Interactive Message; {message_id}: {message_text}; {message_type}"
                logging.info(interactive_message)
                if message_id.startswith('Categories'):
                    if message_text == 'Alumni Events':
                        data_list = MAIN_DATA[TOPIC_MAPPING[message_text]]  # get_ghseet_data(worksheet_name='Events')
                        data_categories = sorted(list(set([x['Region'] for x in data_list])))
                        messenger.send_button(
                            recipient_id=mobile,
                            button=create_button(category='Event Region',
                                                 item_list=data_categories,  # ['Delhi/NCR', 'Mumbai', 'Berlin'],
                                                 header='Select a Region',
                                                 body="Know about upcoming events in your area")
                        )
                    elif message_text == 'Dosco Card Benefits':
                        data_list = MAIN_DATA[TOPIC_MAPPING[message_text]]  # get_ghseet_data(worksheet_name='Benefits')
                        data_categories = sorted(list(set([x['Type'] for x in data_list])))
                        messenger.send_button(
                            recipient_id=mobile,
                            button=create_button(category='Benefit Type',
                                                 item_list=data_categories,  # ['Shopping', 'Hospitality', 'All'],
                                                 header='Select Benefit Type',
                                                 body="Avail benefits with your Dosco card")
                        )
                    elif message_text == 'Dosco Memorabilia':
                        data_list = MAIN_DATA[
                            TOPIC_MAPPING[message_text]]  # get_ghseet_data(worksheet_name='Memorabilia')
                        data_categories = sorted(list(set([x['Type'] for x in data_list])))
                        messenger.send_button(
                            recipient_id=mobile,
                            button=create_button(category='Memorabilia Section',
                                                 item_list=data_categories,  # ['Clothing', 'Ceramics', 'Collectibles'],
                                                 header='Explore Memorabilia',
                                                 body="The General Store now at your fingertips")
                        )
                    elif message_text == 'DSOBS Activities':
                        all_data = MAIN_DATA[TOPIC_MAPPING[message_text]]
                        relevant_data = ["\n".join(f"*{y}*: {str(x[y])}" for y in x.keys()) for x in all_data]
                        relevant_data_formatted = "\n\n".join(relevant_data)
                        messenger.send_message(
                            f"Here are the upcoming/ongoing activities ", mobile)
                        messenger.send_message(
                            f"{str(relevant_data_formatted)}", mobile)
                elif message_id.startswith('Event Region'):
                    all_data = MAIN_DATA['Events']  # get_ghseet_data('Events')
                    relevant_data = ["\n".join(f"*{y}*: {str(x[y])}" for y in x.keys()) for x in all_data if
                                     x['Region'] == message_text]
                    relevant_data_formatted = "\n\n".join(relevant_data)
                    messenger.send_message(
                        f"Here are the events in {message_text}", mobile)
                    messenger.send_message(
                        f"{str(relevant_data_formatted)}", mobile)
                elif message_id.startswith('Benefit Type'):
                    all_data = MAIN_DATA['Benefits']  # get_ghseet_data('Benefits')
                    # relevant_data = ["\n".join(f"*{y}*: {str(x[y])}" for y in x.keys() if y in ['Company', 'Benefit Details', 'Valid Until']) for x in all_data if x['Type'] == message_text]
                    relevant_data = [f"*{x['Company']}*\n{str(x['Benefit Details'])}" for x in all_data if
                                     x['Type'] == message_text]
                    relevant_data_formatted = "\n\n".join(relevant_data)
                    messenger.send_message(
                        f"Here are the Benefits in {message_text}", mobile)
                    messenger.send_message(
                        f"{str(relevant_data_formatted)}", mobile)
                elif message_id.startswith('Memorabilia Section'):
                    all_data = MAIN_DATA['Memorabilia']  # get_ghseet_data('Memorabilia')
                    relevant_data = ["\n".join(f"*{y}*: {str(x[y])}" for y in x.keys()) for x in all_data if
                                     x['Type'] == message_text]
                    relevant_data_formatted = "\n\n".join(relevant_data)
                    messenger.send_message(
                        f"Here are the items available in {message_text}", mobile)
                    messenger.send_message(
                        f"{str(relevant_data_formatted)}", mobile)

            else:
                print(f"{mobile} sent {message_type} ")
                print(data)
        else:  # FOR DELIVERY/READ STATUS OF A SPECIFIC MESSAGE
            delivery = messenger.get_delivery(data)
            if delivery:
                print(f"Delivery Message : {delivery}")
            else:
                print("No new message")
    return "ok"


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=8050, debug=True, use_reloader=False)
    app.run(host='0.0.0.0', debug=True, port=80)

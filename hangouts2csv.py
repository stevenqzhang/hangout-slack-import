import json
import csv
import argparse
import datetime
from pytz import timezone
import re

# returns true if string is a name
def is_name(string):
    m = re.match(r"([a-z]|[A-Z]|\s)*",string)
    if m.group(0) == string:
        return True
    else:
        return False

def main():
    DEBUG = False

    parser = argparse.ArgumentParser(description='Parse your Google data archives of Hangout into CSV for Slack import')
    parser.add_argument('-i', '--input', type=file, required=True, help='Hangout json file', metavar='<Hangouts.json>')
    parser.add_argument('-o', '--output', type=argparse.FileType('wb'), required=True, help='CSV output file', metavar='<hangouts.csv>')

    args = parser.parse_args()
    print args.input

    jsonObj = json.load(args.input)


    #hack by looking at google plus
    #Todo make this lookup using API https://developers.google.com/apis-explorer/#p/plus/v1/plus.people.get
    uniq_users = {}
    uniq_users[105790549405625095128] = "Sam Tzou"
    uniq_users[114788163999803911886] = "Tracy Zhang"
    uniq_users[109207454791961290004] = "Philip Zhang"
    uniq_users[113062463581502975242] = "Steven Zhang"


    with args.output as csvfile:
        hangoutswriter = csv.writer(csvfile)


        #debug
        uniq_event_types = set()
        unknown_gaia_ids = set()

        pacific = timezone('US/Pacific')

        for conv in jsonObj["conversation_state"]:
            for p in conv["conversation_state"]["conversation"]["participant_data"]:
                gaia_id = p["id"]["chat_id"]
                try:
                    # generate a table of participant Ids and phone numbers
                    if gaia_id in uniq_users:
                        uniq_users[gaia_id] += "___" + p["fallback_name"]
                    else:
                        uniq_users[gaia_id] = p["fallback_name"]
                except KeyError:
                    print "unknown fallback name for: " + str(p)

            for event in conv["conversation_state"]["event"]:
                timestamp = int(event["timestamp"]) / 1000000

                #TODO parameter
                timestamp_formatted = pacific.localize(datetime.datetime.fromtimestamp(timestamp))\
                    .strftime('%Y-%m-%d %H:%M:%S')

                username = uniq_users[event["sender_id"]["chat_id"]] if event["sender_id"]["chat_id"] in uniq_users else "unknown"

                # only select
                if ((event["event_type"] == u'REGULAR_CHAT_MESSAGE') or (event["event_type"] == u'SMS')):
                    if "segment" in event["chat_message"]["message_content"]:
                        text = event["chat_message"]["message_content"]["segment"][0]["text"]
                    else:
                        text = \
                            event["chat_message"]["message_content"]["attachment"][0]["embed_item"]["embeds.PlusPhoto.plus_photo"]["url"]
                    if username == "unknown":
                        if(DEBUG):
                            print "=== =========unknown user with gaiaid: \n",
                            print timestamp_formatted, event["sender_id"]["chat_id"], text, "\n"
                        unknown_gaia_ids.add(event["sender_id"]["chat_id"])

                    #TODO catch these exceptions

                    try:
                        if(DEBUG):
                            print timestamp_formatted, username, text

                        hangoutswriter.writerow([timestamp_formatted,
                                             username,
                                             event["event_type"],
                                             text.encode('utf-8')])
                    except UnicodeEncodeError:
                        print "=========problem with username or text- unicode error========= \n",
                        print timestamp_formatted, username, text, "\n"


                # otherwise skip
                else:
                    # HANGOUT_EVENT
                    # ADD_USER
                    # RENAME_CONVERSATION
                    # REMOVE_USER
                    uniq_event_types.add(event["event_type"])


        print "all non-event conversations: " + str(uniq_event_types)
        print "all unknown gaiaIds: " + str(unknown_gaia_ids)
        print "all users" + str(uniq_users)

if __name__ == "__main__":
    main()
import json
import csv
import argparse
import datetime
from pytz import timezone
import re
from collections import defaultdict
from bunch import *
import phonenumbers

# returns true if string is a name
def is_name(string):
    m = re.match(r"([a-z]|[A-Z]|\s)*", string)
    if m.group(0) == string:
        return True
    else:
        return False


# wrapper class for names
class UserNamesAndNumbers:
    def __init__(self, all_names_and_numbers):
        self.all_names_and_numbers = all_names_and_numbers
        self.canonical_name = "unknown"
        self.numbers = set()
        #todo use globals for the unknowns
        self.canonical_number = "unknown_number"

    def __repr__(self):
        return "<Canonical name: " + self.canonical_name + "; all names: " + str(self.all_names_and_numbers) + ">"

    # generates canonical name by finding name
    def generateCanonicalName(self):
        for name in self.all_names_and_numbers:
            if is_name(name):
                self.canonical_name = name

    #getter with logic
    def getCanonicalName(self):
        self.generateCanonicalName()
        return self.canonical_name

    #get either name, or if that isn't available, the number
    def generateNumbers(self):
        for name in self.all_names_and_numbers:
            try:
                self.numbers.add(UserNamesAndNumbers.formatNumber(name))
            except:
                pass
        self.canonical_number = min(self.numbers)

    def getCanonicalNumber(self):
        self.generateNumbers()
        return self.canonical_number

    # if no canonical name exists, then canonical number
    def getCanonicalNameOrNumber(self):
        canonicalName = self.getCanonicalName()
        if (canonicalName != "unknown"):
            return canonicalName
        return self.getCanonicalNumber()


    @staticmethod
    def formatNumber(string):
        z = phonenumbers.parse(string, region="US")  #google voice SMS only in US/Canada anyways
        return phonenumbers.format_number(z, phonenumbers.PhoneNumberFormat.E164)


def main():
    #organize data by person
    data = defaultdict(list)

    DEBUG = False

    parser = argparse.ArgumentParser(description='Parse your Google data archives of Hangout into CSV for Slack import')
    parser.add_argument('-i', '--input', type=file, required=True, help='Hangout json file', metavar='<Hangouts.json>')
    parser.add_argument('-o', '--output', type=argparse.FileType('wb'), required=True, help='CSV output file',
                        metavar='<hangouts.csv>')

    args = parser.parse_args()
    print args.input

    jsonObj = json.load(args.input)


    #hack by looking at google plus
    #Todo make this lookup using API https://developers.google.com/apis-explorer/#p/plus/v1/plus.people.get
    uniq_users = {}
    uniq_users[105790549405625095128] = UserNamesAndNumbers({"Sam Tzou"})
    uniq_users[114788163999803911886] = UserNamesAndNumbers({"Tracy Zhang"})
    uniq_users[109207454791961290004] = UserNamesAndNumbers({"Philip Zhang"})
    uniq_users[113062463581502975242] = UserNamesAndNumbers({"Steven Zhang"})

    with args.output as csvfile:
        hangoutswriter = csv.writer(csvfile)
        hangoutswriter.writerow(["Timestamp", "User ChatID", "Canonical name", "all names", "Type", "text"])


        #debug
        uniq_event_types = set()
        unknown_gaia_ids = set()

        pacific = timezone('US/Pacific')

        for conv in jsonObj["conversation_state"]:

            # look for accumulating names
            for p in conv["conversation_state"]["conversation"]["participant_data"]:
                current_chat_id = long(p["id"]["chat_id"])
                try:
                    if current_chat_id in uniq_users:
                        uniq_users[current_chat_id].all_names.add(p["fallback_name"])
                    else:
                        uniq_users[current_chat_id] = UserNamesAndNumbers({p["fallback_name"]})

                except KeyError:
                    print "unknown fallback name for: " + str(p)

            #look for accumulating conversations
            for event in conv["conversation_state"]["event"]:
                timestamp = int(event["timestamp"]) / 1000000

                #TODO parameter
                timestamp_formatted = pacific.localize(datetime.datetime.fromtimestamp(timestamp)) \
                    .strftime('%Y-%m-%d %H:%M:%S')

                #id is real canonical name
                current_chat_id = long(event["sender_id"]["chat_id"])

                # event
                if ((event["event_type"] == u'REGULAR_CHAT_MESSAGE') or (event["event_type"] == u'SMS')):
                    if "segment" in event["chat_message"]["message_content"]:
                        text = event["chat_message"]["message_content"]["segment"][0]["text"]
                    else:
                        text = \
                            event["chat_message"]["message_content"]["attachment"][0]["embed_item"][
                                "embeds.PlusPhoto.plus_photo"]["url"]

                    #TODO catch these exceptions

                    try:
                        if (DEBUG):
                            print timestamp_formatted, current_chat_id, text

                        row = Bunch()
                        row.timestamp_formatted = timestamp_formatted
                        row.chat_id = current_chat_id
                        row.event_type = event["event_type"]
                        row.text = text.encode('utf-8')

                        data[current_chat_id].append(row)

                    except UnicodeEncodeError:
                        print "=========problem with username or text- unicode error========= \n",
                        print timestamp_formatted, current_chat_id, username, uniq_users[current_chat_id], uniq_users[
                            current_chat_id].all_names, "\n"


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

        #write to csv
        for iter_chat_id in data:
            for row in data[iter_chat_id]:
                username = uniq_users[row.chat_id].getCanonicalName
                hangoutswriter.writerow()


if __name__ == "__main__":
    main()
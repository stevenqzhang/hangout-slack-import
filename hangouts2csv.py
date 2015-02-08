import json
import csv
import argparse
import datetime
from pytz import timezone
import re
from collections import defaultdict
from bunch import *
import phonenumbers
import pandas as pd

# reads optional contacts file
def read_parsed_contacts():
    xls = pd.read_pickle('contacts.pickle')
    return xls

# returns true if string is a name
def is_name(string):
    m = re.match(r"([a-z]|[A-Z]|\s)*", string)
    if m.group(0) == string:
        return True
    else:
        return False


# calculate metdata about responsiveness- the transition direction and time
def calc_metadata(msgs):
    # sort messages from earliest to latests
    msgs = sorted(msgs, key = lambda x: x.timestamp)

    for i, m in enumerate(msgs):
        if i > 0:
            m.transition = m.direction + last_m.direction
            m.transition_time = m.timestamp - last_m.timestamp

            #check order
            if m.transition_time <= 0:
                raise Exception("not ordered")

            msgs[i] = m
        else:
            m.transition = "Null"
            m.transition_time = "Null"


        last_m = m
    return msgs




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
        if self.canonical_name == "unknown":
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
        try:
            self.canonical_number = min(self.numbers)
        except ValueError as inst:
            # we expect empty seqeuence if has no number
            if (inst.message != "min() arg is an empty sequence"):
                print inst.message
                raise ValueError("some other value error besides excepted")

    def getCanonicalNumber(self):
        if self.canonical_number == "unknown_number":
            self.generateNumbers()
        return self.canonical_number

    # if no canonical name exists, then canonical number
    def getCanonicalNameOrNumber(self):
        canonicalName = self.getCanonicalName()
        if (canonicalName != "unknown"):
            return canonicalName
        return self.getCanonicalNumber()

    #returns formatter US number. else raise exception
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
        hangoutswriter.writerow([
            "Conversation ID",
            "Timestamp",
            "Event type",

            "transition",
            "transition time (microsec)",

            "Sender ID",
            "Sender Canonical name",
            "Sender all names",

            "Receiver ID",
            "Receiver Canonical name",
            "Receiver all names",

            "Other person ID",
            "Other person Canonical name",
            "Other person all names",
            "Direction",

            "text"])


        #debug
        uniq_event_types = set()
        unknown_gaia_ids = set()

        pacific = timezone('US/Pacific')

        #iterate over each conversation
        for conv in jsonObj["conversation_state"]:

            participant_data = conv["conversation_state"]["conversation"]["participant_data"]

            # we only care to analyze 2-person conversations for now
            if len(participant_data) != 2:
                continue

            all_two_participant_ids = []

            # look for accumulating names
            for p in participant_data:
                current_chat_id = long(p["id"]["chat_id"])
                all_two_participant_ids.append(current_chat_id)
                try:
                    #test for keyerrors
                    p["fallback_name"]

                    if current_chat_id in uniq_users:
                        uniq_users[current_chat_id].all_names_and_numbers.add(p["fallback_name"])
                    else:
                        uniq_users[current_chat_id] = UserNamesAndNumbers({p["fallback_name"]})


                except KeyError:
                    print "unknown fallback name for: " + str(p)

            # get lookup tables ready before conversation loop
            if len(all_two_participant_ids) != 2:
                raise Exception("All participant ids should be 2, we checked for this already!")
            sender_receiver_relationship = {}
            sender_receiver_relationship[all_two_participant_ids[0]] = all_two_participant_ids[1]
            sender_receiver_relationship[all_two_participant_ids[1]] = all_two_participant_ids[0]


            #look for accumulating conversations
            for event in conv["conversation_state"]["event"]:
                timestamp = int(event["timestamp"])

                #TODO parameter
                timestamp_formatted = pacific.localize(datetime.datetime.fromtimestamp(timestamp/ 1000000)) \
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
                        row.conversation_id = conv["conversation_id"]["id"]
                        row.timestamp = timestamp
                        row.timestamp_formatted = timestamp_formatted
                        row.sender_id = current_chat_id
                        row.receiver_id = sender_receiver_relationship[row.sender_id]
                        row.event_type = event["event_type"]
                        row.text = text.encode('utf-8')

                        # stuff I need for analysis
                        if(row.sender_id == 113062463581502975242L):
                            row.direction = 'outbound'
                            row.other_person_id = row.receiver_id
                        elif row.receiver_id == 113062463581502975242L:
                            row.direction = 'inbound'
                            row.other_person_id = row.sender_id
                        else:
                            raise Exception("Uh oh, not inbound nor outbound")

                        #sort by conversationid
                        data[row.conversation_id].append(row)

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

            # sort through event
            print "sorting through conversation: " + str(data[row.conversation_id])

            #makes sure that conversations are recorded and not just all voicemail events
            if(data[row.conversation_id]):
                data[row.conversation_id] = calc_metadata(data[row.conversation_id])

        print "all non-event conversations: " + str(uniq_event_types)
        print "all unknown gaiaIds: " + str(unknown_gaia_ids)
        print "all users" + str(uniq_users)

        #sort data by row

        # merge in google contacts to list of users
        uniq_users = merge_contacts(uniq_users, read_parsed_contacts())

        #write to csv
        for conv_id in data:
            for row in data[conv_id]:
                hangoutswriter.writerow([
                                        # basic metadata
                                         row.conversation_id,
                                         row.timestamp_formatted,
                                         row.event_type,

                                         # responsiveness
                                         row.transition,
                                         row.transition_time,

                                         #sender
                                         row.sender_id,
                                         uniq_users[row.sender_id].getCanonicalNameOrNumber(),
                                         uniq_users[row.sender_id].all_names_and_numbers,

                                         #receiver
                                         row.receiver_id,
                                         uniq_users[row.receiver_id].getCanonicalNameOrNumber(),
                                         uniq_users[row.receiver_id].all_names_and_numbers,

                                         #totally redundant, but oh well- other person besides me
                                         row.other_person_id,
                                         uniq_users[row.other_person_id].getCanonicalNameOrNumber(),
                                         uniq_users[row.other_person_id].all_names_and_numbers,
                                         row.direction,

                                         row.text])

def merge_contacts(uniq_users, contacts):
    print "====Merging in contacts (this could take a while)...."
    for key, user in uniq_users.items():
        num = user.getCanonicalNameOrNumber()
        print "current user: " + str(user)
        for i, row in contacts.iterrows():
            if (contacts.ix[i, 'Phone parsed'] == num):
                user.canonical_name = contacts.ix[i, 'Name']
    return uniq_users



if __name__ == "__main__":
    main()
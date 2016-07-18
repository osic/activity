#!/usr/bin/env python3
import os
import trello
import csv
import re
import datetime

#================ BEGIN HARDCODED STUFF =====================================

BOARD_IDS = [
    "56e88037fd1eb8bcf675b9d0", #Ceilometer/Horizon/FleetMgt
    "56e1cab9d126f75bd8ac907d", #Compute - Nova/Ironic/Magnum/Glance
    "56e8800d4e648e175ba7a6f2", #Deploy - OSA/OPS/ Ref Imp
    "56e87c1c58d87e4517c5baec", #Neutron / Octavia / Keystone
    "572ccc002ca1efed1b07a5f1", #QA
    "56e880575a938eb86099a1fd", #Security/Docs
    "56e6f2645f78497eaa9e4218", #Storage - Swift/Cinder
    # "52e9461fd04cfcc72a096aeb",   #Test board
]


OSIC_PRIORITIES = [
    "CFGDFT",
    "FLTMGT",
    "NOVEXP",
    "MULTCI",
    "RLGUPD",
    "DEMOUG",
    "FEATCL",
    "SECTEST",
    "CPNAVL",
    "LODTST",
    "THRDCI",
]

PROJECT_NAMES = [
    "Ceilometer",
    "Cinder",
    "Docs",
    "Fleet Management",
    "Glance",
    "Horizon",
    "Ironic",
    "Keystone",
    "Magnum",
    "Neutron",
    "Nova",
    "Octavia",
    "Ops",
    "OSA",
    "QA&CI",
    "Security",
    "Swift",
]

ACTIVE_COLUMNS = [
    "Accepted Backlog",
    "Doing",
    "Done",
    "Ready & Bite-Sized",
    "Review",
    "Waiting on External",
    "Waiting on OSIC",
]

MEMBER_FILE_NAME = "../data/trello_members.txt"
ONE_ROW_PER_CARD_NAME = "../data/one_row_per_card.csv"
CARD_FOR_EACH_LABEL_NAME = "../data/card_for_each_label.csv"
CARD_FOR_EACH_ASSIGNMENT_NAME = "../data/card_for_each_assignment.csv"

#================ END HARDCODED STUFF ========================================

MODE_ONE_ROW_PER_CARD = 0
MODE_CARD_FOR_EACH_LABEL = 1
MODE_CARD_FOR_EACH_ASSIGNMENT = 2


def print_board_ids (client : trello.TrelloClient):
    boards = client.list_boards()
    for board in boards: #type: trello.Board
        print (board.id + "\t" + board.name.decode(encoding='UTF-8'))


def generate_member_lookup_file(client, file_name):
    members={}
    try:
        for i in BOARD_IDS:
            board = client.get_board(i) #type: trello.Board
            print (board.name)
            for j in board.all_members(): #type: trello.Member
                members[j.username.decode(encoding='UTF-8')] = j.full_name.decode(encoding='UTF-8')

    except trello.exceptions.ResourceUnavailable as error:
        print ("Board not found: " + i)

    if len(members) > 0:
        with open(file_name, 'w') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(['trello_username', 'full_name'])
            for member_id, member_name in members.items():
                writer.writerow((member_id,member_name))

    print ("{0} entries written.".format(len(members)))


def write_one_row (writer, outrow):
    writer.writerow(
        [
            outrow['board_name'],
            outrow['list_name'],
            outrow['card_name'],
            outrow['osic_epic'],
            outrow['days_since'],
            outrow['checklist_count'],
            outrow['checklist_item_count'],
            outrow['checked_item_count'],
            outrow['label_count'],
            outrow['member_count'],
            outrow['label_detail'],
            outrow['member_detail'],
            outrow['card_url'],
        ]
    )

def active_cards_as_csv (client, mode, out_filename):
    re_string = "|".join(OSIC_PRIORITIES) #Type: String
    osic_priorities = re.compile(re_string)


    with open(out_filename, 'w') as export_file:
        csvwriter = csv.writer(export_file, quoting=csv.QUOTE_NONNUMERIC)
        csvwriter.writerow([
            'board_name',
            'list_name',
            'card_name',
            'osic_epic',
            'days_since',
            'checklist_count',
            'checklist_item_count',
            'checked_item_count',
            'label_count',
            'assignment_count',
            'label_detail',
            'assignnment_detail',
            'url',
                          ]
        )
        for b_id in BOARD_IDS:
            board = client.get_board(b_id) #type: trello.Board

            # Build a mapping of member ids to usernames
            member_cache = {}
            if mode == MODE_CARD_FOR_EACH_ASSIGNMENT:
                members = board.all_members()
                for member in members:
                    member_cache[member.id] = member.username.decode(encoding='UTF-8')

            print ("Retrieving data from " + board.name.decode(encoding='UTF-8'))
            cards = board.open_cards()
            for card in cards:  #Type: trello.Card
                outrow = {}

                # If the card isn't in one of the columns we care about, skip it.
                outrow['list_name'] = card.get_list().name.decode(encoding='UTF-8')
                if outrow['list_name'] not in ACTIVE_COLUMNS:
                    continue

                outrow['board_name'] = board.name.decode(encoding='UTF-8')

                # Determine the epic
                outrow['card_name'] = card.name.decode(encoding='UTF-8')
                result = re.search(osic_priorities, outrow['card_name'])
                outrow['osic_epic'] = 'opportunistic'
                if result: # Represents an OSIC priority, not opportunistic
                    outrow['osic_epic'] = result.group(0)

                # Determine days since last activity
                now = datetime.datetime.utcnow()
                last_activity = card.date_last_activity
                delta = now - last_activity.replace(tzinfo=None)
                outrow['days_since'] = delta.days

                # See how much stuff is in checklists
                outrow['checklist_count'] = 0
                outrow['checklist_item_count'] = 0
                outrow['checked_item_count'] = 0

                checklists = card.checklists #Type:trello.Checklist
                if checklists is not None and len(checklists) > 0:
                    outrow['checklist_count'] += len(checklists)
                    for checklist in checklists:
                        outrow['checklist_item_count'] += len(checklist.items)
                        for item in checklist.items:
                            if item['state'] == 'complete':
                                outrow['checked_item_count'] += 1

                labels = card.labels
                outrow['label_count'] = len(labels)
                outrow['label_detail'] = "<No detail>" #Default value may get overwritten

                member_ids = card.member_ids
                outrow['member_count'] = len(member_ids)
                outrow['member_detail'] = "<No detail>"  # Default value may get overwritten

                outrow['card_url'] = card.url

                if mode == MODE_CARD_FOR_EACH_LABEL:

                    if len(labels) > 0:
                        for label in labels:
                            outrow['label_detail'] = label.name.decode(encoding='UTF-8')
                            write_one_row(csvwriter,outrow)
                    else:
                        outrow['label_detail'] = "<No Labels>"
                        write_one_row(csvwriter, outrow)

                elif mode == MODE_CARD_FOR_EACH_ASSIGNMENT:

                    if len(member_ids) > 0:
                        for member_id in member_ids:
                            outrow['member_detail'] = member_cache[member_id]
                            write_one_row(csvwriter,outrow)
                    else:
                        outrow['member_detail'] = "<No Assignment>"
                        write_one_row(csvwriter, outrow)

                else:  # MODE_ONE_ROW_PER_CARD
                    write_one_row(csvwriter, outrow)

if __name__ == "__main__":

    passes = [
        (MODE_CARD_FOR_EACH_LABEL, CARD_FOR_EACH_LABEL_NAME),
        (MODE_CARD_FOR_EACH_ASSIGNMENT, CARD_FOR_EACH_ASSIGNMENT_NAME),
        (MODE_ONE_ROW_PER_CARD, ONE_ROW_PER_CARD_NAME),
    ]

    client = trello.TrelloClient(os.environ['TRELLO_API_KEY'],token=os.environ['TRELLO_TOKEN'])
    print ("Generating {0} files...".format(len(passes)))
    for this_pass in passes:
        print ("Writing data to {0}".format(this_pass[1]))
        active_cards_as_csv(client,this_pass[0],this_pass[1])

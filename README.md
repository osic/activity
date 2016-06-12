# OSIC Trello Activity Data

The data subdirectory of this repository includes CSV exports from the OSIC Trello boards, capturing information about cards existing in the following lists on Trello:

* Accepted Backlog
* Doing
* Done
* Ready & Bite-Sized
* Review
* Waiting on External
* Waiting on OSIC

The CSV exports include the following columns:

* board_name
* list_name
* card_name
* osic_epic
* days_since
* checklist_count
* checklist_item_count
* checked_item_count
* label_count
* assignment_count
* label_detail
* assignnment_detail
* url

## Three file flavors

Three different files are generated...

### one_row_per_card.csv

This file contains precisely one row for each Trello card in the columns listed above. The label_detail and assignment_detail columns will always say "<No Detail>".

### card_for_each_label.csv

This file contains each card at least once, with rows that repeat for each label on the card.  Use this with spreadsheet filters to find cards labeled with a specific milestone, project, or priority (or any other label, for that matter).  Cards without any labels will show "<No Labels>" in the label_detail field, and the assignment_detail field will always say "<No Detail>".

### card_for_each_assignment.csv

This file contains each card at least once, with rows that repeat for each assignment on the card.  Use this with spreadsheet filters and formulas to find cards assigned to a specific person, cards with no assignments, cards with too many assignments, and/or people with no assignments. Cards without assignments will show "<No Assignments>" in the assignment_detail field, and the label_detail field will always say "<No Detail>".

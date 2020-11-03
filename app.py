import objects
import datetime
import helpers
import sys
import function


def import_chart_of_account(filename='./data/chartofaccount/ChartofAccounts.csv'):
    objects.Account.import_accounts_from_file(filename=filename)


def process_statement(id_, force=False):
    # Force means that all lines will be forcefully reprocessed.
    # Force = False means that only the lines with incomplete user_amount will be reprocessed.
    statement = objects.Statement.objects.get(id_=id_)

    for line1 in objects.StatementLine.objects(statement=statement):

        if force == False:
            #confirm the line has not already been processed.
            line_entry = list(objects.JournalEntry.objects(statement_line=line1))
            # print(line_entry)
            if len(line_entry) > 0:
                for line2 in line_entry:
                    threat_line = False
                    for transaction in line2.transactions:
                        if len(transaction.user_amount) != len(objects.User.objects()):
                            # delete this transaction and retreat the line
                            threat_line = True
                    if threat_line == True:
                        print("DELETE LINE")
                        for transaction in line2.transactions:
                            transaction.delete()
                        line2.delete()
                        objects.JournalEntry.create_from_statement_line(line1.id_)

            else:
                objects.JournalEntry.create_from_statement_line(line1.id_)

        elif force == True:

            line_entry = list(objects.JournalEntry.objects(statement_line=line1))
            # print(line_entry)
            if len(line_entry) > 0:
                for line2 in line_entry:
                    
                    for transaction in line2.transactions:
                        transaction.delete()
                    line2.delete()

            objects.JournalEntry.create_from_statement_line(line1.id_)

def process_statement_lines(force=False):
    for line1 in list(objects.StatementLine.objects()):

        if force == False:
            #confirm the line has not already been processed.
            line_entry = list(objects.JournalEntry.objects(statement_line=line1))
            # print(line_entry)
            if len(line_entry) == 1:
                for line2 in line_entry:
                    threat_line = False
                    for transaction in line2.transactions:
                        if len(transaction.user_amount) != len(objects.User.objects()):
                            # delete this transaction and retreat the line
                            threat_line = True
                    if threat_line == True:
                        print("DELETE LINE")
                        for transaction in line2.transactions:
                            transaction.delete()
                        line2.delete()
                        objects.JournalEntry.create_from_statement_line(line1.id_)

            elif len(line_entry) > 1:
                # TODO: print the 2 entry and chose to delete 1 of them
                pass

            else:
                objects.JournalEntry.create_from_statement_line(line1.id_)

        elif force == True:

            line_entry = list(objects.JournalEntry.objects(statement_line=line1))
            # print(line_entry)
            if len(line_entry) > 0:
                for line2 in line_entry:
                    
                    for transaction in line2.transactions:
                        transaction.delete()
                    line2.delete()

            objects.JournalEntry.create_from_statement_line(line1.id_)




def process_journal_entry(id_, force=False):
    for journalentry in objects.JournalEntry.objects():
        if len(journalentry.transactions) > 2:
            continue
        
        # if journalentry.transactions[0].acount_number in 

def delete_transactions(id_):

    for journalentry in list(objects.JournalEntry.objects(id_=id_)):
        print('Entry found, deleting entry would delete this entry:')
        print(journalentry)
        choice = input('Are you sure you want to delete this entry ? [no]/yes >> ')
        if choice in ['y', 'yes',]:
            # print(journalentry)
            for transaction in journalentry.transactions:
                print(transaction)
                delete_choice = input('Delete item? [yes] >>')
                if delete_choice in ['y', '', ]:
                    transaction.delete()
                else:
                    print('skipped')
                    pass
            journalentry.delete()
        else: 
            print('cancelled')

def init_db(force=False):
    if force == True:
        choice = input('you want to reset the db, are you sure? >> ')
        if choice in ['yes', 'y', '']:
            pass
        else:
            print('cancelled')
            sys.exit()
    
    if not objects.Counters.objects():
        objects.init_counters()
        print('counters init')

    if not objects.User.objects():
        objects.User.init_2_users()
        print('User init')

    if not objects.Account.objects():
        import_chart_of_account()
        print('Account init')



    if  force == True:

        objects.Counters.drop_collection()
        objects.init_counters()

        objects.User.drop_collection()
        objects.User.init_2_users()

        objects.Account.drop_collection()
        import_chart_of_account()

        objects.Statement.drop_collection()
        objects.StatementLine.drop_collection()

        objects.JournalEntry.drop_collection()
        objects.Transaction.drop_collection()



if __name__ == "__main__":


    
    base_folder = './data'


    # NOTES: we need to add a separate column for the reconciled accounts.
    # these accounts will hold statement and will be reconciled between each other.
    # So if a transactino is destined  to another account with a statement, 
    # it needs to warn if there is not 2 statement lines linked to this transaction
    # ccurrently the line 980 that was added does not work properly.
    # transactions with same description should be held and dispatched later when another 
    # match the exact amount at same date. if not then we ask the user.

    # TODO: put the split description on amount after the statement line, so we keep the statement information integral.
    # All data should be saved in files so that it does not get lost. (until database is reliable)
    # init_db(force=True) # set Force=True to reset db
    init_db(force=False) # set Force=True to reset db

    user1 = objects.User.objects[0]
    user2 = objects.User.objects[1]


    print('initial lenght of statement line: ', len(objects.StatementLine.objects()))
    print('initial lenght of transactions: ', len(objects.Transaction.objects()))


    # # Process the accounts.
    # csv_files = helpers.find_csv_filenames(base_folder, ".csv")
    # csv_files.sort()
    # for file in csv_files:
    #     print(file)
    #     imported_lines = function.StatementFunction.import_file(base_folder + '/' + file, header=True)
    #     function.StatementFunction.import_statement_lines(imported_lines)
    # file = '2020-09-23_releve.csv'
    # imported_lines = function.StatementFunction.import_file(base_folder + '/' + file, header=True)
    # function.StatementFunction.import_statement_lines(imported_lines)
    # function.StatementFunction.process_statement_lines()

    
        
    
    

    # # process the credit card bills
    # txt_files = helpers.find_csv_filenames(base_folder, ".txt")
    # txt_files.sort()
    # for file in txt_files:
    #     print(file)
    #     statement1 = function.StatementFunction.credit_card_bill_parser(base_folder + '/' + file)
    # # # function.StatementFunction.process_statement_lines()
    # # statement1 = function.StatementFunction.credit_card_bill_parser(base_folder + '/' + '559828######4013_20201014.txt')
    # function.StatementFunction.process_statement_lines()

    print('final lenght of statement line: ', len(objects.StatementLine.objects()))
    print('final lenght of transactions: ', len(objects.Transaction.objects()))

    # delete_transactions(1323)

    
    # statement1 = objects.Statement.import_statement_from_file('./data/231305-2020-01.csv', ',', True)
    # process_statement(statement1.id_)

    # for transaction in objects.Transaction.objects():
    #     print(transaction)

    # objects.print_account_list()
    
    # objects.reports.user_balance(datetime.date(year=2020, month=7, day=1), datetime.date(year=2020, month=11, day=1))
    # delete_transactions(832)
    # objects.reports.income_statement(datetime.date(year=2020, month=1, day=1), datetime.date(year=2020, month=12, day=1))
    objects.reports.general_ledger(datetime.date(year=2019, month=1, day=1), datetime.date(year=2020, month=12, day=31))
    # objects.reports.general_ledger(datetime.date(year=2020, month=3, day=1), datetime.date(year=2020, month=12, day=1), 515005)

    objects.reports.account_recap(111001, datetime.date(year=2020, month=1, day=1), datetime.date(year=2020, month=12, day=1))

    # objects.find_reconciled_error()
    # objects.find_journal_entry(account_number_form=211100, account_number_to=515005)

    
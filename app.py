import objects
import datetime
import helpers


def import_chart_of_account(filename='./.data/ChartofAccounts.csv'):
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



if __name__ == "__main__":

    # objects.init_counters()
    
    base_folder = './.data'

    if not objects.User.objects():
        objects.User.init_2_users()


    
    # objects.Account.drop_collection()
    # import_chart_of_account()

    # objects.Statement.drop_collection()
    # objects.StatementLine.drop_collection()
    # objects.JournalEntry.drop_collection()
    # objects.Transaction.drop_collection()

    user1 = objects.User.objects[0]
    user2 = objects.User.objects[1]


    # #Print the list of statement id_
    # for object_ in list(objects.Statement.objects()):
    #     print(object_.id_)
    



    # objects.Statement.import_statement_from_file('./.data/509066_2020-01.csv', ',', True)
    # process_statement(114)

    # statement1 = objects.Statement.import_statement_from_file('./.data/2020-01_releve.csv', ',', True)
    # process_statement(statement1.id_)

    # Process the accounts.
    # csv_files = helpers.find_csv_filenames(base_folder, ".csv")
    # for file in csv_files:
    #     print(file)
    #     statement1 = objects.Statement.import_statement_from_file(base_folder + '/' + file, ',', True)
    #     process_statement(statement1.id_)

    # # process the credit card bills
    # txt_files = helpers.find_csv_filenames(base_folder, ".txt")
    # for file in txt_files:
    #     print(file)
    #     statement1 = objects.credit_card_bill_parser(base_folder + '/' + file)
    #     process_statement(statement1.id_)
    
    # objects.Statement.import_statement_from_file('./.data/2020-02_releve.csv', ',', True)
    # process_statement(20, force=True)

    #objects.Statement.import_statement_from_file('./.data/2020-03_releve.csv', ',', True)
    #process_statement(95)

    # objects.Statement.import_statement_from_file('./.data/2020-04_releve.csv', ',', True)
    # process_statement(96)

    # objects.Statement.import_statement_from_file('./.data/2020-05_releve.csv', ',', True)
    # process_statement(105)

    # objects.Statement.import_statement_from_file('./.data/2020-06_releve.csv', ',', True)
    # process_statement(108)

    # objects.Statement.import_statement_from_file('./.data/2020-07_releve.csv', ',', True)
    # process_statement(113)    
    #process_statement(4)
    

    
    # objects.credit_card_bill_parser('./.data/559828######4013_20200115.txt')
    # process_statement(12)

    # objects.credit_card_bill_parser('./.data/559828######4013_20200213.txt')
    # process_statement(91)
  
    # objects.credit_card_bill_parser('./.data/559828######4013_20200312.txt')
    # process_statement(114)

    # objects.credit_card_bill_parser('./.data/559828######4013_20200414.txt')
    # process_statement(115)

    # objects.credit_card_bill_parser('./.data/559828######4013_20200513.txt')
    # process_statement(116)

    # objects.credit_card_bill_parser('./.data/559828######4013_20200611.txt')
    # process_statement(117)

    # objects.credit_card_bill_parser('./.data/559828######4013_20200714.txt')
    # process_statement(118) 

    # objects.credit_card_bill_parser('./.data/559828######4013_20200813.txt')
    # process_statement(119) 

    # objects.credit_card_bill_parser('./.data/559828######4013_20200914.txt')
    # process_statement(121) 

    # objects.Statement.import_statement_from_file('./.data/2020-02_releve.csv', ',', True)
    # process_statement(92)

    #objects.Statement.import_statement_from_file('./.data/2020-03_releve.csv', ',', True)
    #process_statement(95)

    # objects.Statement.import_statement_from_file('./.data/2020-04_releve.csv', ',', True)
    # process_statement(96)

    # objects.Statement.import_statement_from_file('./.data/2020-05_releve.csv', ',', True)
    # process_statement(105)

    # objects.Statement.import_statement_from_file('./.data/2020-06_releve.csv', ',', True)
    # process_statement(108)

    # objects.Statement.import_statement_from_file('./.data/2020-07_releve.csv', ',', True)
    # process_statement(113)    



    objects.reports.user_balance(datetime.date(year=2020, month=8, day=1), datetime.date(year=2020, month=9, day=25))

    #objects.reports.income_statement(datetime.date(year=2020, month=1, day=1), datetime.date(year=2020, month=12, day=1))
    #objects.reports.general_ledger(datetime.date(year=2020, month=1, day=1), datetime.date(year=2020, month=12, day=1))
    
    
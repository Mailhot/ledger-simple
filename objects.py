
from mongoengine import *
from datetime import datetime
from bson import ObjectId
import csv
import collections

default_currency = "CAD"

# Connect the DB, just need to install mongoDB, might need to create the DB?
connect('ledger-simple')

ACCOUNT_TYPE = {'BC': 'Bank and Cash',
            'FA': 'Fixed Assets',
            'NCL': 'Non-Current Liability',
            'E': 'Expense',
            'CA': 'Current Assets',
            'R': 'Receivable',
            'CL': 'Current Liability',
            'P': 'Payable',
            'I': 'Income',
            'OI': 'Other Income',
            'DC': 'Direct Cost',
            'CYE': 'Current Year Earning',
            'SUM': 'Sum',
            }

def init_counters():
    # Init the DB for counters, only required initially.
    counter1 = Counters(id2='UserId', sequence_value=1)
    counter1.save()
    counter3 = Counters(id2='JournalEntryId', sequence_value=1)
    counter3.save()
    counter4 = Counters(id2='StatementLineId', sequence_value=1)
    counter4.save()
    counter5 = Counters(id2='StatementId', sequence_value=1)
    counter5.save()
    counter6 = Counters(id2='TransactionId', sequence_value=1)
    counter6.save()

class Counters(Document):
    id2 = StringField(max_length=20)
    sequence_value = IntField()

def getNextSequenceValue(sequenceName):
    # sequenceDocument = Database.find_one_update('counters', {"id": sequenceName}, {"$inc":{"sequence_value":1}})
    counter = Counters.objects.get(id2=sequenceName)
    # print("len(counter) = ", len(counter))
    Counters.objects(id2=sequenceName).update_one(inc__sequence_value=1)
    counter.reload()
    sequenceDocument = counter.sequence_value
    # print("sequence number for %s is now : %s" % (sequenceName, sequenceDocument))

    return sequenceDocument


class User(Document):
    id_ = IntField(unique=True, required=True)
    name = StringField(unique=True)

    def init_2_users():
        user1_name = input("What is the name of the user 1 >> ")
        user2_name = input("What is the name of the user 2 >> ")
        user1 = User.add_user(user1_name)
        user2 = User.add_user(user2_name)

    def add_user(name):
        new_user = User(id_=getNextSequenceValue('UserId'), name=name)
        new_user.save()
        return new_user

    def get_user(name):
        user1 = User.objects.get(name=name)
        return user1

class Account(Document):
    """This is the Chart of Account accounts items"""
    number = IntField(min_value=100000, max_value=999999, unique=True) 
    parent_account = ReferenceField("self", default=None) # Not in use
    child_account = ReferenceField("self", default=None) # Not in use
    description = StringField(max_length=200, required=True)
    type_ = StringField(max_length=3, choices=ACCOUNT_TYPE)
    user_ratio = DictField(default=None) # Needs testing, should be a dict
    account_number = IntField(default=None)
    account_type = StringField(max_length=3)

    def header():
        return "%6s %40s %5s %12s %14s %12s" %('number', 'description', 'type_', 'user_ratio', 
                                                                    'account_number', 'account_type')

    def __str__(self):
        return "%6s %40s %5s %12s %14s %12s" %(self.number, self.description, self.type_, self.user_ratio, self.account_number,
                                                                     self.account_type)



    def add_account(number, parent_account, child_account, description, type_, user_ratio, account_number=None, account_type=None):
        new_account = Account(number=number, 
                            parent_account=parent_account,
                            child_account=child_account,
                            description=description,
                            type_=type_,
                            user_ratio=user_ratio,
                            account_number=account_number, 
                            account_type=account_type,
                            )
        new_account.save()
        print(new_account.id)
        return new_account

    def get_account(account_number, account_type):
        account1 = Account.objects.get(account_number=account_number, account_type=account_type)
        return account1

    def import_accounts_from_file(filename):
        with open(filename, "r") as the_file:
            csv_reader = csv.reader(the_file, delimiter=',')
            line_count = 0
            last_sum = None
            for row in csv_reader:
                if line_count == 0:
                    print('skipping first line')
                    line_count += 1
                    continue

                else:
                    if row[4] == 'Sum':
                        parent_account = None
                    else:
                        parent_account = last_sum


                    # Get ratios
                    if row[5] != '':

                        user_ratio = {str(User.objects[0].id_): float(row[5])/100, str(User.objects[1].id_): float(row[6])/100}

                    else:
                        user_ratio = None

                    # Account type and number for bank account
                    if row[2] != '':
                        account_number = int(row[2])
                        account_type = row[3]
                    else:
                        account_type = None
                        account_number = None

                    dict_values = list(ACCOUNT_TYPE.values()).index(row[4])
                    print("dict_values = ", dict_values)
                    dict_keys = list(ACCOUNT_TYPE.keys())
                    new_account = Account.add_account(number=row[0],
                                                    parent_account=parent_account,
                                                    child_account=None, 
                                                    description=row[1],
                                                    type_=dict_keys[dict_values],
                                                    user_ratio=user_ratio,
                                                    account_number=account_number, 
                                                    account_type=account_type,
                                                    )
                    new_account.save()
                    

                    if row[4] == 'Sum':
                        last_sum = new_account

                line_count += 1


class Statement(Document):
    id_ = IntField(required=True)
    date = DateTimeField(default=datetime.now())
    filename = StringField(required=True)
    start_balance = FloatField()
    end_balance = FloatField()
    closed = BooleanField(default=False)
    #lines = ListField(ReferenceField(StatementLine))

    def init_statement(filename,):
        # check if already exist.
        new_statement = Statement(id_=getNextSequenceValue('StatementId'),
                                date=None,
                                filename=filename,
                                start_balance=None,
                                end_balance=None
                                )
        new_statement.save()

        print("new statement saved: ", new_statement.id)
        return new_statement



    def import_statement_from_file(filename, delimiter):
        """import a file into a statement and statement lines, 
        requires the filename and delimiter."""
        
        created_statement = False

        if Statement.objects(): # check if a statement objects already exists.
            if Statement.objects.get(filename=filename): # if a statement already exist confirm it has a different filename
                print("Filename already imported.")
                choice = input("Do you want to continue with file import? [yes] / no >> ")
                if choice == 'no' or choice == 'n':
                    return None
                elif choice == 'yes' or choice == 'y' or choice == "":
                    current_statement = Statement.objects.get(filename=filename)

        else:
            #create the new statement instance.
            current_statement = Statement.init_statement(filename)
            created_statement = True

        current_statement_list = list()
        current_statement_list.append(current_statement)

        with open(filename) as the_file:
            csv_reader = csv.reader(the_file, delimiter=delimiter)
            line_counter = 0
            first_line = True
            for line in csv_reader:
                if len(line) > 1: # find the first line that is now empty.
                    if created_statement == True:
                        new_line = StatementLine.create_line(date=line[3],
                                                            account_number=line[1],
                                                            account_type=line[2],
                                                            line_number=line[4],
                                                            description=line[5],
                                                            credit=StatementLine.to_float_or_zero(line[7]),
                                                            debit=StatementLine.to_float_or_zero(line[8]),
                                                            interest=StatementLine.to_float_or_zero(line[9]),
                                                            advance=StatementLine.to_float_or_zero(line[11]),
                                                            reimbursement=StatementLine.to_float_or_zero(line[12]),
                                                            balance=StatementLine.to_float_or_zero(line[13]),
                                                            statement=current_statement,
                                                            )

                        # add newly imported line to statement.
                        #current_statement.lines.append(new_line)

                    elif created_statement == False:
                        line_number_list = []
                        line_number_list.append(line[4])
                        new_line = list(StatementLine.objects(statement__in=current_statement_list).filter(line_number__in=line_number_list, account_number__in=[line[1]], account_type__in=[line[2]]))[0]
                        new_line.date = line[3]
                        new_line.account_number = line[1]
                        new_line.account_type = line[2]
                        new_line.line_number = line[4]
                        new_line.description = line[5]
                        new_line.credit = StatementLine.to_float_or_zero(line[7])
                        new_line.debit = StatementLine.to_float_or_zero(line[8])
                        new_line.interest = StatementLine.to_float_or_zero(line[9])
                        new_line.advance = StatementLine.to_float_or_zero(line[11])
                        new_line.reimbursement = StatementLine.to_float_or_zero(line[12])
                        new_line.balance = StatementLine.to_float_or_zero(line[13])
                        new_line.save()



                    if first_line == True:
                        current_statement.start_balance = new_line.balance
                        first_line = False
                    

                elif len(line) <= 1 and first_line == False: # This is the last line
                    current_statement.end_balance = new_line.balance

                current_statement.save()
                line_counter += 1




        for line in StatementLine.objects(statement__in=current_statement_list): 

            print(line)



class StatementLine(Document): #
    id_ = IntField(required=True)
    date = DateTimeField(default=datetime.now())
    account_number = IntField(required=True)
    account_type = StringField(max_length=3)
    line_number = IntField(required=True)
    description = StringField(default=None)
    credit = FloatField(default=0)
    debit = FloatField(default=0)
    interest = FloatField(default=0)
    advance = FloatField(default=0)
    reimbursement = FloatField(default=0)
    balance = FloatField(default=0)
    statement = ReferenceField(Statement)
    #journal_entry = ReferenceField(JournalEntry, default=None)
    def header():
        print("%4s %10s %8s %3s %4s %30s %6s %6s %6s %6s %6s %6s" %('id_', 'date', 'account_number', 'account_type', 'line_number', 'description',
                                                        'credit', 'debit', 'interest', 'advance', 'reimbursement', 'balance'))
    def __str__(self):
        return "%4s %10s %8s %3s %4s %30s %6s %6s %6s %6s %6s %6s" %(self.id_, self.date, self.account_number, self.account_type, self.line_number, self.description,
                                                        self.credit, self.debit, self.interest, self.advance, self.reimbursement, self.balance)

    def get_statement_line(id_):
        result = StatementLine.objects.get(id_=id_)
        return result

    def to_float_or_zero(value):
        # convert a value to a float, if not possible, return zero.
        try:
            result = float(value)
        except ValueError:
            result = 0
        return result




    def create_line(date, account_number, account_type, line_number, description, credit, debit, interest, advance, reimbursement, balance, statement):
        
        new_statement_line = StatementLine(id_=getNextSequenceValue('StatementLineId'),
                                        date=date,
                                        account_number=account_number,
                                        account_type=account_type,
                                        line_number=line_number,
                                        description=description,
                                        credit=credit,
                                        debit=debit,
                                        interest=interest,
                                        advance=advance,
                                        reimbursement=reimbursement,
                                        balance=balance,
                                        statement=statement,
                                        )
        new_statement_line.save()
        return new_statement_line


class Transaction(Document):
    """docstring for ClassName"""
    id_ = IntField(required=True)
    date = DateTimeField(default=datetime.now())
    account_number = ReferenceField("Account", required=True)
    credit = FloatField(default=1)
    debit = FloatField(default=1)
    # user_ratio = MapField(ReferenceField(User), default=None) # this should be used only in accounts i think
    source_ref = ReferenceField(StatementLine)
    source = StringField(default=None) # could be text or ref to other document ID (ex: Statment0001)
    user_amount = DictField()
    # We do not manage currency for now.
    #currency_amount = currency_rate = FloatField(default=0)
    #currency = StringField(max_length=3, default="CAD")
    #currency_rate = FloatField(default=1)
    def header():
        print("%4s %10s %15s %8s %8s %5s %6s %20s" %('id_', 'date', 'account_number', 'credit', 'debit', 'source_ref.id_',
                                                        'source', 'user_amount',))
    def __str__(self):
        if self.source_ref:
            source_ref_id = source_ref.id_
        else:
            source_ref_id = None
        return "%4s %10s %15s %8s %8s %5s %6s %20s" %(self.id_, self.date.date(), self.account_number.number, self.credit, self.debit, source_ref_id,
                                                        self.source, self.user_amount)

    def add_transaction(date, account_number, credit, debit, source, source_ref):

        #account_class = Account.get_account(account_number)

        # keep on
        if credit == '':
            credit = 0

        else:
            credit = float(credit)

        if debit == '':
            debit == 0

        else:
            debit = float(debit)

        if account_number.user_ratio != None:
            user_amount = dict()
            for user in account_number.user_ratio.keys():
                print('user_ratio', account_number.user_ratio[user])
                user_amount[user] = float(account_number.user_ratio[user]) * (credit + debit)
        else: # User ratio is None
            user_amount = None

        new_transaction = Transaction(id_=getNextSequenceValue('TransactionId'), 
                                    date=date,
                                    account_number=account_number,
                                    credit=credit,
                                    debit=debit,
                                    source=source,
                                    source_ref=source_ref,
                                    user_amount = user_amount,
                                    )
        new_transaction.save()

        print("New transaction saved : ", new_transaction.id)

        return new_transaction


class report():
    """Basid class for standard GAAP reports:

    income statement
    balance sheet
    cash flow

    """
    # ACCOUNT_TYPE = {'BC': 'Bank and Cash',
    #         'FA': 'Fixed Assets',
    #         'NCL': 'Non-Current Liability',
    #         'E': 'Expense',
    #         'CA': 'Current Assets',
    #         'R': 'Receivable',
    #         'CL': 'Current Liability',
    #         'P': 'Payable',
    #         'I': 'Income',
    #         'OI': 'Other Income',
    #         'DC': 'Direct Cost',
    #         'CYE': 'Current Year Earning',
    #         'SUM': 'Sum',
    #         }
    # Income Statement
    # Revenue
    # Cost of Sale (direct cost) this is the essential cost
    # Gross profit (revenue - direct cost)  
    # Operating Expense
    # Net Profit


    def income_statement(date_from, date_to):
        report_classify = dict()
        report_classify['BC'] = 'assets' # 'Bank and Cash',
        report_classify['FA'] = 'assets' # 'Fixed Assets',
        report_classify['NCL'] = 'liability' # 'Non-Current Liability',
        report_classify['E'] =  'expense' # 'Expense',
        report_classify['CA'] = 'assets' # 'Current Assets',
        report_classify['R'] = 'assets' # 'Receivable',
        report_classify['CL'] = 'liability' # 'Current Liability',
        report_classify['P'] = 'liability' # 'Payable',
        report_classify['I'] = 'revenue' # 'Income',
        report_classify['OI'] = 'revenue' # 'Other Income',
        report_classify['DC'] = 'direct_cost' # 'Direct Cost',
        report_classify['CYE'] = 'current_year_earning' # 'Current Year Earning',
        
        report_section = collections.OrderedDict()
        report_section['assets']['total'] = 0
        report_section['liability']['total'] = 0
        report_section['expense']['total'] = 0
        report_section['revenue']['total'] = 0
        report_section['direct_cost']['total'] = 0

        for user in list(User.objects()):
            for section in report_section.keys():
                report_section[section][str(user.id_)] = 0

        for journal_entry in list(JournalEntry.objects(date__gt=date_from, date__lt=date_to)):
            for transaction in journal_entry.transactions:
                report_section[report_classify[transaction.account_number.type_]]['total'] += (transaction.credit + transaction.debit)
                for user in list(User.objects()):
                    report_section[report_classify[transaction.account_number.type_]][str(user.id_)] += transaction.user_amount[str(user.id_)]

        line_value = []
        print('%12s   %12s  %12s  %12s' %('section', 'total', 'user1', 'user2'))
        for report_section_key in report_section.keys():
            for report_line_key in report_section_key.keys():
                # TODO: confirm this occurs in proper order
                line_value.append(report_section[report_section_key][report_line_key])
            print('%12s   %12s  %12s  %12s' %(report_section_key, line_value[0], line_value[1], line_value[2]))



class JournalEntry(Document):
    id_ = IntField(required=True)
    statement_line = ReferenceField(StatementLine)
    transactions = ListField(ReferenceField(Transaction))



    def create_from_statement_line(statement_line_id_):
        print('')
        # Confirm it does not already exist.
        statement_line = StatementLine.get_statement_line(statement_line_id_)
        StatementLine.header()
        print(statement_line)

        # Step 1
        # Check if existing transaction are present, update source if yes.
        open_transaction = list(Transaction.objects(account_number=Account.get_account(int(statement_line.account_number), statement_line.account_type),
                                                    source_ref=None, 
                                                    date=statement_line.date, 
                                                    #credit=statement_line.debit, 
                                                    #debit=statement_line.credit,
                                                    ))

        if len(open_transaction) > 0:

            print('here are the open transaction that matches this one. ')
            i = 0
            Transaction.header()
            for transaction in open_transaction:
                i += 1
                print(i, transaction)

            print("Select which transaction you would like to link to this one. (presse enter to skip and create a new one)")
            transaction_choice = input(">> ")

            if transaction_choice == '':
                print('transaction skipped')
                pass

            else:
                selected_transaction = open_transaction[int(transaction_choice)-1]
                selected_transaction.source_ref = statement_line
                selected_transaction.save()
                # TODO: need to add a parameter to show the line has been reconciled.


        else: # No transaction matches this statement line, so we create a new one.

            try:
                existing_journal_entry = JournalEntry.objects.get(statement_line=statement_line)
                print('line found')

            except:
                print('No JournalEntry exist on this line, creating new one.')

            
            # add first Transaction from the source account in statement line.
            transaction1 = Transaction.add_transaction(date=statement_line.date,
                                                        account_number=Account.get_account(int(statement_line.account_number), statement_line.account_type),
                                                        credit=statement_line.credit,
                                                        debit=statement_line.debit, 
                                                        source=None, 
                                                        source_ref=statement_line,
                                                        )
            transaction1.save()

            # add second Transaction from the found destination account in past journal entry.
            # But first check if past statement line were threated, if yes we will use the same account output.
            past_statement_line = list(StatementLine.objects(description=statement_line.description,
                                                            id__lt=statement_line.id, # make sure the statement_line has been evaluated before the one we are threating.
                                                            ))

            print('past_statement_line = ', past_statement_line)


            if len(past_statement_line) > 0:
                # TODO: Would need to find the most recent past_statement_line to be able to have proper account if modification were made.
                # Until we get the most recent, we use the last one.
                selected_past_statement_line = past_statement_line[-1] # Best way to find the earlyest line for now. (need improvement.)
                print(selected_past_statement_line.to_json())

                # Find the journal entry with this line (assuming it exist)
                # TODO: what if it does not exist?
                past_journal_entry = JournalEntry.objects.get(statement_line=selected_past_statement_line)
                past_output_transaction = past_journal_entry.transactions[-1]
                Account.header()
                print(past_output_transaction.account_number)

                # threat_choice = input('Would you like to select the destination account manually? (y)/n >> ')
                # if threat_choice == 'y':
                #     pass
                #     # TODO: revert to next else statement (manual account choice.)

                

                transaction2 = Transaction.add_transaction(date=statement_line.date,
                                                            account_number=past_output_transaction.account_number,
                                                            credit=statement_line.debit,
                                                            debit=statement_line.credit, 
                                                            source=None, 
                                                            source_ref=None, # will be either none or the other statement line that confirm this transaction if the account is bank and cash (has a statement)
                                                            )

                transaction2.save()

            else:
                exit_bol = False

                while True:
                    account_number_choice = input('what account should this statement go to? >> ')

                    try:
                        result_account = Account.objects.get(number=int(account_number_choice))
                        print('result found: ', result_account)
                    except Exception as e: 
                        print(e)
                        result_account = None

                    if result_account != None:
                        transaction2 = Transaction.add_transaction(date=statement_line.date,
                                    account_number=result_account,
                                    credit=statement_line.debit,
                                    debit=statement_line.credit, 
                                    source=None, 
                                    source_ref=None,
                                    )

                        transaction2.save()
                        exit_bol = True


                    else:
                        print('account not found, please try again.')
                        for account_ in Account.objects():
                            print(account_.number, account_.description, account_.account_number, '-', account_.account_type)


                        
                    if exit_bol == True:
                        break




            new_journal_entry = JournalEntry(id_=getNextSequenceValue('JournalEntryId'),
                                            statement_line=statement_line,
                                            )
            new_journal_entry.save()

            new_journal_entry.transactions.append(transaction1)
            new_journal_entry.transactions.append(transaction2)
            new_journal_entry.save()
            #################################
            # Check ratios and balance them
            # TODO: this would need a function to itself.
            print('transaction2.user_amount = ', transaction2.user_amount)
            if transaction2.user_amount == {}: # We take for granted the transaction1 has always a ratio as it's a know account with defined ratio.
                print('Output account has no ratio set, use parent ratio?')
                print('Parent ratio: ', transaction1.account_number.user_ratio)
                use_parent_ratio_choice = input('(y)/n >> ')
                if use_parent_ratio_choice == 'y' or use_parent_ratio_choice == '':
                    transaction2.user_amount = transaction1.user_amount
                    transaction2.save()
                    print('parent ratio used')

                else:
                    ratio_choice = input('What ratio should we set to user1? >> ')
                    users = list(User.objects())

                    transaction2.user_amount = {str(users[0].id_): float(ratio_choice) * (transaction2.credit + transaction2.debit), 
                                                str(users[1].id_): 1-float(ratio_choice) * (transaction2.credit + transaction2.debit)}
                    transaction2.save()

            elif transaction1.account_number.user_ratio != transaction2.account_number.user_ratio:
                transaction2.user_amount = transaction1.user_amount # take user amount from to affect to account.
                transaction2.save()



def get_exchange_rate():
    # Keep on
    pass

if __name__ == "__main__":
    #Statement.import_statement_from_file('./.data/2020-01_releve.csv', ',')
    pass

        
from mongoengine import *
from mongoengine.connection import _get_db
from datetime import datetime
from bson import ObjectId
import csv
import collections
import helpers
import unittest

default_currency = "CAD"

# Connect the DB, just need to install mongoDB, might need to create the DB?
connect('ledger-simple-test2')

# Exceptions are transaction that comes with same description but could go to different account.
# they hare going to an account that we are reconciling also.


EXCEPTIONS = [{'account_number': 213305,
                'account_type': 'PCA',
                'description': 'Transfer - AccesD - Internet', 
                'others_accounts': [709733, 716528]
                }]

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

# ACTION_VALUES = {'Previous balance': self.update_previous_balance,
#                         'Purchases/debits': self.update_purchase,
#                         'Payments/credits': self.update_payments,
#                         'New current balance ($):': self.update_new_balance,
#                         'Credit charges ($)': self.update_frais_credits,
#                         #'Statement date:': self.update_name,
#                         }

def init_counters():
    # Init the DB for counters, only required initially.
    counter1 = Counters(id2='UserId', sequence_value=0)
    counter1.save()
    counter3 = Counters(id2='JournalEntryId', sequence_value=0)
    counter3.save()
    counter4 = Counters(id2='StatementLineId', sequence_value=0)
    counter4.save()
    counter5 = Counters(id2='StatementId', sequence_value=0)
    counter5.save()
    counter6 = Counters(id2='TransactionId', sequence_value=0)
    counter6.save()
    counter7 = Counters(id2='MonthlyBillId', sequence_value=0)
    counter7.save()


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
    reconciled = BooleanField(default=False)

    def header():
        return "%6s %40s %5s %12s %14s %12s" %('number', 'description', 'type_', 'user_ratio', 
                                                                    'account_number', 'account_type')

    def __str__(self):
        return "%6s %40s %5s %12s %14s %12s" %(self.number, self.description, self.type_, self.user_ratio, self.account_number,
                                                                     self.account_type)


    def add_account(number, parent_account, child_account, description, type_, user_ratio, account_number=None, account_type=None, reconciled=False):
        new_account = Account(number=number, 
                            parent_account=parent_account,
                            child_account=child_account,
                            description=description,
                            type_=type_,
                            user_ratio=user_ratio,
                            account_number=account_number, 
                            account_type=account_type,
                            reconciled=reconciled
                            )
        new_account.save()
        print(new_account.id)
        return new_account

    def get_account(account_number, account_type):
        account1 = Account.objects.get(account_number=account_number, account_type=account_type)
        return account1

    def get_account_by_number(number):
        account1 = Account.objects.get(number=number)
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

                    #facultative reconciled parameter
                    if row[7] in ['TRUE', 'True', 'y', 'Y']:
                        reconciled_found = True
                    else:
                        reconciled_found = False

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
                                                    reconciled=reconciled_found
                                                    )
                    new_account.save()
                    

                    if row[4] == 'Sum':
                        last_sum = new_account

                line_count += 1



class Statement(Document):
    id_ = IntField(required=True)
    date = DateTimeField(default=datetime.now())
    stop_date = DateTimeField(default=None)
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

        new_statement.name = None
        new_statement.transactions = []
        new_statement.start_date = None
        new_statement.stop_date = None
        new_statement.previous_balance_report = 0
        # self.previous_balance = 0
        new_statement.purchase_report = 0
        new_statement.purchase = 0
        new_statement.payments_report = 0
        new_statement.payments = 0
        new_statement.frais_credits_report = 0
        new_statement.frais_credits = 0
        new_statement.new_balance_report = 0
        new_statement.new_balance = 0




        new_statement.save()

        print("new statement saved: ", new_statement.id)
        return new_statement



        

    def print(self): # TODO: to be arrange to work
        print("MonthlyBill for : %s to %s" %(self.start_date, self.stop_date))
        print("%10s, %30s, %10s, %3s" %('date', 'desctiption', 'amount', 'typed'))
        for transaction in self.transactions:
            print("%10s, %30s, %8.2f, %3s" %(transaction.date, transaction.description, transaction.amount, transaction.typed))

    def recap(self): # TODO: to be arrange to work
        self.purchase = 0
        self.payments = 0
        self.frais_credits = 0
        self.new_balance = 0

        grouped_expense = {} # expense grouped by category
        distributed_expense = {} # expense summed by paying entity

        for key in CATEGORY.keys():
            if CATEGORY[key]['paying'] == True:
                distributed_expense[key] = {"expense": 0, "payment": 0}

        for transaction in self.transactions:

            if transaction.typed not in grouped_expense.keys():
                grouped_expense[transaction.typed] = 0 

            if transaction.amount > 0:
                grouped_expense[transaction.typed] += transaction.amount
                
                if transaction.typed != "fc":
                    self.purchase += transaction.amount
                else:
                    self.frais_credits += transaction.amount

                if transaction.typed in RATIO.keys():
                    for key in RATIO[transaction.typed].keys():
                        distributed_expense[key]["expense"] += RATIO[transaction.typed][key]*transaction.amount
                else:
                    distributed_expense[transaction.typed]["expense"] += transaction.amount

            elif transaction.amount < 0:
                self.payments += transaction.amount
                if transaction.typed in RATIO.keys():
                    for key in RATIO[transaction.typed].keys():
                        distributed_expense[key]["payment"] += RATIO[transaction.typed][key]*transaction.amount
                else:
                    distributed_expense[transaction.typed]["payment"] += transaction.amount

            else:
                print("zero value transaction skipping.")
        print(" ")

        print("Printing recap for transaction between %s and %s." %(str(self.start_date)[:-9], str(self.stop_date)[:-9]))
        for element in grouped_expense:
            print(element, grouped_expense.get(element))
        for element in distributed_expense:
            print(element, distributed_expense.get(element))
        self.new_balance = self.previous_balance_report + self.purchase + self.payments + self.frais_credits

        print(" ")
        print("%20s %10s %10s" %('Total', 'Calculated', 'Actual'))

        print("%20s %10s %10.2f" %('Previous balance', "-", self.previous_balance_report))
        print("%20s %10.2f %10.2f" %('Purchase/debits', self.purchase, self.purchase_report))
        print("%20s %10.2f %10.2f" %('Payments/credits', self.payments, self.payments_report))
        print("%20s %10.2f %10.2f" %('Frais de credits', self.frais_credits, self.frais_credits_report))
        print("%20s %10.2f %10.2f" %('New current balance', self.new_balance, self.new_balance_report))


    def update_purchase(self, value):
        value = value.replace(',', '')
        self.purchase_report = float(value)
        print("Updated purchase = ", float(value))

    def update_payments(self, value):
        value = value.replace(',', '')
        self.payments_report = float(value)
        print("update_payments = ", float(value))

    def update_new_balance(self, value):
        value = value.replace(',', '')
        self.new_balance_report = float(value)
        print("update_new_balance = ", float(value))

    def update_previous_balance(self, value):
        value = value.replace(',', '')
        if self.previous_balance_report == 0:
            self.previous_balance_report = float(value)

        print("previous_balance = ", self.previous_balance_report)

    def update_frais_credits(self, value):
        value = value.replace(',', '')
        self.frais_credits_report = float(value)
        print("update frais de credits = ", value)

    # def update_name(self, value):
    #     self.name = value
    #     print("Updated name = ", self.name)

    def update_values(self, list_):
        ACTION_VALUES = {'Previous balance': self.update_previous_balance,
                'Purchases/debits': self.update_purchase,
                'Payments/credits': self.update_payments,
                'New current balance ($):': self.update_new_balance,
                'Credit charges ($)': self.update_frais_credits,
                #'Statement date:': self.update_name,
                }

        action = ACTION_VALUES.get(list_[0])
        if action:
            action(list_[1])



    def import_statement_from_file(filename, delimiter, header=False):
        """import a file into a statement and statement lines, 
        requires the filename and delimiter.
        header = True mean skip the first line.
        """
        
        created_statement = False
        current_statement = None

        if Statement.objects(): # check if a statement objects already exists.
            if len(list(Statement.objects(filename=filename))) > 1: # if a statement already exist confirm it has a different filename
                print("Filename already imported.")
                choice = input("Do you want to continue with file import? [yes] / no >> ")
                if choice == 'no' or choice == 'n':
                    return None
                elif choice == 'yes' or choice == 'y' or choice == "":
                    current_statement = Statement.objects.get(filename=filename)
        

        if current_statement == None:
            #create the new statement instance.
            current_statement = Statement.init_statement(filename)
            created_statement = True

        current_statement_list = list()
        current_statement_list.append(current_statement)

        with open(filename) as the_file:
            csv_reader = csv.reader(the_file, delimiter=delimiter)
            line_counter = 0
            first_line = True
            header_passed = False
            for line in csv_reader:
                if header == True and header_passed == False: # skip first line if header = true
                    header_passed = True
                    continue

                if len(line) > 1: # find the first line that is now empty.
                    if created_statement == True:
                        if len(line) == 15:
                            if line[14] not in [None, 0, '']:
                                destination_account = int(line[14])
                                
                        else:
                            destination_account = None

                        # check for description with amount, remove amount as it would wrongly not find accounts afterwards.
                        if '$' in line[5]:
                            description_list = line[5].split(':')
                            split_description = description_list[0]
                        else:
                            split_description = line[5]

                        new_line = StatementLine.create_line(date=line[3],
                                                            account_number=line[1],
                                                            account_type=line[2],
                                                            line_number=line[4],
                                                            description=split_description,
                                                            credit=StatementLine.to_float_or_zero(line[7]),
                                                            debit=StatementLine.to_float_or_zero(line[8]),
                                                            interest=StatementLine.to_float_or_zero(line[9]),
                                                            advance=StatementLine.to_float_or_zero(line[11]),
                                                            reimbursement=StatementLine.to_float_or_zero(line[12]),
                                                            balance=StatementLine.to_float_or_zero(line[13]),
                                                            statement=current_statement,
                                                            destination_account=destination_account,
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
        return current_statement



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
    destination_account = IntField(default=None)
    reconciled = BooleanField(default=False)
    # ratio_code = StringField(max_length=4, default=None)
    ratio_code = FloatField(default=None)
    threated = BooleanField(default=False)
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

    def search_line(date, account_number, description, credit, debit, interest, advance, reimbursement):
        # TODO: Finish this part.
        results = StatementLine.objects(date=date,
                                        account_number=account_number, 
                                        description=description, 
                                        credit=credit, 
                                        debit=debit, 
                                        interest=interest,
                                        advance=advance, 
                                        reimbursement=reimbursement,
                                        )



    def create_line(date, account_number, account_type, line_number, description, credit, debit, interest, advance, reimbursement, balance, statement, destination_account=0, reconciled=False, ratio_code=None):
        
        if destination_account == None or destination_account == '':
            destination_account = 0


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
                                        destination_account=destination_account,
                                        reconciled=reconciled,
                                        ratio_code=ratio_code
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
    description = StringField(max=250)
    # user_ratio = MapField(ReferenceField(User), default=None) # this should be used only in accounts i think
    source_ref = ReferenceField(StatementLine)
    source = StringField(default=None) # could be text or ref to other document ID (ex: Statment0001)
    user_amount = DictField()
    # We do not manage currency for now.
    #currency_amount = currency_rate = FloatField(default=0)
    #currency = StringField(max_length=3, default="CAD")
    #currency_rate = FloatField(default=1)
    def header():
        print("%4s %10s %15s %8s %8s %5s %20s" %('id_', 'date', 'account_number', 'credit', 'debit', 'source_ref.id_',
                                                        'user_amount',))
    def __str__(self):
        if self.source_ref:
            source_ref_id = self.source_ref.id_
        else:
            source_ref_id = None
        if self.user_amount:
            user_amount = self.user_amount
        else:
            user_amount = 'n/a'
        return "%4s %10s %15s %8s %8s %5s %20s" %(self.id_, self.date.date(), self.account_number.number, self.credit, self.debit, source_ref_id,
                                                        user_amount)

    def add_transaction(date, account_number, credit, debit, source, source_ref, description=None):

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
                #print('user_ratio', account_number.user_ratio[user])
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

        print("New transaction saved : ", new_transaction)

        return new_transaction

    def create_reverse_transaction(transaction):
        # create a new transaction with all the same thing except the credit and debit are reversed
        new_transaction = Transaction(id_=getNextSequenceValue('TransactionId'), 
                                    date=transaction.date,
                                    account_number=transaction.account_number,
                                    credit=transaction.debit,
                                    debit=transaction.credit,
                                    source=transaction.source,
                                    source_ref=transaction.source_ref,
                                    user_amount=transaction.user_amount,
                                    )
        new_transaction.save()

        return new_transaction


class reports():
    """Basid class for standard GAAP reports:

    income statement
    balance sheet
    cash flow

    """

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
        report_section['assets'] = {}
        report_section['assets']['total'] = 0
        report_section['liability'] = {}
        report_section['liability']['total'] = 0
        report_section['expense'] = {}
        report_section['expense']['total'] = 0
        report_section['revenue'] = {}
        report_section['revenue']['total'] = 0
        report_section['direct_cost'] = {}
        report_section['direct_cost']['total'] = 0


        for user in list(User.objects()):
            for section in report_section.keys():
                report_section[section][str(user.id_)] = 0

        journal_entry_filtered = list(JournalEntry.objects(date__gte=date_from, date__lte=date_to))
        #print(journal_entry_filtered)
        for journal_entry in journal_entry_filtered:
            print('journal_entry = ', journal_entry)
            for transaction in journal_entry.transactions:
                # this works unless there is debit and credit on same transaction, and this is not possible for the moment.
                if transaction.credit == 0:
                    debit = True
                    report_section[report_classify[transaction.account_number.type_]]['total'] += transaction.debit
                else:
                    debit = False

                    report_section[report_classify[transaction.account_number.type_]]['total'] -= transaction.credit
                
                print(transaction)
                for user in list(User.objects()):
                    if debit == True:

                        report_section[report_classify[transaction.account_number.type_]][str(user.id_)] += transaction.user_amount[str(user.id_)]
                    else:
                        report_section[report_classify[transaction.account_number.type_]][str(user.id_)] -= transaction.user_amount[str(user.id_)]
        
        print(report_section)

        print('%12s   %10s  %10s  %10s' %('section', 'total', 'user1', 'user2'))
        for report_section_key in report_section.keys():
            #print(report_section_key)
            line_value = []
            for report_line_key in report_section[report_section_key].keys():
                # TODO: confirm this occurs in proper order
                line_value.append(report_section[report_section_key][report_line_key])
            print('%12s   %10.2f  %10.2f  %10.2f' %(report_section_key, line_value[0], line_value[1], line_value[2]))

    def general_ledger(date_from, date_to, filter_account=None):
        
        if filter_account is not None:
            filter_account_class = Account.get_account_by_number(filter_account)

        filtered_transaction = []
        
        # Create the report dict
        report_section = collections.OrderedDict()
        for account_ in list(Account.objects()):
            #print(type(account_.number))
            report_section[account_.number] = {}
            report_section[account_.number]['total'] = 0
            report_section[account_.number]['credit'] = 0
            report_section[account_.number]['debit'] = 0

        for user in list(User.objects()):
            for section in report_section.keys():
                report_section[section][str(user.id_)] = 0
        
        journal_entry_filtered = list(JournalEntry.objects(date__gte=date_from, date__lte=date_to))


        for journal_entry in journal_entry_filtered:
            print('')
            print(journal_entry.statement_line)
            print('journal_entry = ', journal_entry)
            for transaction in journal_entry.transactions:
                
                

                # Skip if not the searched account
                if filter_account != None: 
                    if transaction.account_number != filter_account_class:
                        continue

                    else:
                        # filtered_transaction.append(transaction)
                        filtered_transaction += journal_entry.transactions
                        break


                print(transaction)
                # We do not count the transaction if it is reconciled from another transaction. The transaction will be taken care of in it's own journal entry.
                reconciled = helpers.check_reconciled_entry(transaction, journal_entry)

                if reconciled == True:
                    continue

                # # These reconciled transaction appears at 2 places even if they are the same transaction line. We need to make sure we dont count them twice.
                # if transaction.source_ref != None and journal_entry.statement_line != None:
                #     if transaction.source_ref.id_ != journal_entry.statement_line.id_: 
                #         continue
                




                # this works unless there is debit and credit on same transaction, and this is not possible for the moment.
                debit = False
                
                if transaction.credit == 0: 
                    debit = True
                    report_section[transaction.account_number.number]['total'] += transaction.debit
                    report_section[transaction.account_number.number]['debit'] += transaction.debit
                
                else:
                    report_section[transaction.account_number.number]['total'] -= transaction.credit
                    report_section[transaction.account_number.number]['credit'] += transaction.credit
                
                
                for user in list(User.objects()):
                    if transaction.user_amount:
                        if debit == True:
                            report_section[transaction.account_number.number][str(user.id_)] += transaction.user_amount[str(user.id_)]
                        
                        else:
                            report_section[transaction.account_number.number][str(user.id_)] -= transaction.user_amount[str(user.id_)]
        
        #print(report_section)
        print('')
        print('')
        print(date_from, date_to)
        print('')
        print('%12s   %-40s  %10s %10s %10s  %15s  %10s' %('section', 'description', 'total', 'credit', 'debit', 'user1', 'user2'))
        for report_section_key in report_section.keys():
            #print(report_section_key)
            line_value = []
            for report_line_key in report_section[report_section_key].keys():
                # TODO: confirm this occurs in proper order
                line_value.append(report_section[report_section_key][report_line_key])
            line_value_sum = 0
            for value_ in line_value:
                line_value_sum += value_
            if line_value_sum == 0:
                continue
            else:
                account_class = Account.get_account_by_number(number=report_section_key)
                print('%12s   %-40s  %10.2f %10.2f %10.2f  %15.2f  %10.2f' %(report_section_key, account_class.description, line_value[0], line_value[1], line_value[2], line_value[3], line_value[4]))

        for transaction in filtered_transaction:
            print(transaction)

    def balance_sheet(date):
        # Assets = Liabilities + Shareholders Equity
        # assets - liabilities = net worth
        pass

    def user_balance(date_from, date_to, recap=False):
        imbalance_journal_entry = dict()

        # TODO: if we proceed directly with transaction, there will be no double values, double are cross reference of same transactions.
        journal_entry_filtered = list(JournalEntry.objects(date__gte=date_from, date__lte=date_to))
        for journal_entry in journal_entry_filtered:
            print('journal_entry = ', journal_entry)
            active_transactions = []
            user_class  = list(User.objects())
            user_sum = dict()
            i = 0
            for transaction in journal_entry.transactions:

                print(transaction)

                # # Check if this transaction is a reconciled from another one.
                # reconciled = helpers.check_reconciled_entry(transaction, journal_entry)
                # if reconciled == True:
                #     continue
   

                # TODO: the missing user_amount should be handled else where automatically.
                if not transaction.user_amount:
                    print('error, no user amount found!')
                    continue

                if transaction.credit != 0: # if its a credit transaction, place it before the last one, else, after.
                    # print('true')
                    for user in user_class: # 0, 2, 4, are the credit and need to be substracted
                        user_sum = helpers.init_dict_or_substract(user_sum, user.id_, transaction.user_amount[str(user.id_)])
                
                else:
                    for user in user_class: # 1, 3, 5, are the debit
                        user_sum = helpers.init_dict_or_add(user_sum, user.id_, transaction.user_amount[str(user.id_)])

                # print('user.id_ = ', user.id_)
                i += 1

            
            # for i in range(len(journal_entry.transactions)):
                
                
            #     i += 1

            # print('user_sum', user_sum)
            if user_sum[user_class[0].id_] != 0:
                print('imbalance found!')
                imbalance_journal_entry[journal_entry.id_] = {}
                for user in user_class:

                    imbalance_journal_entry[journal_entry.id_][user.id_] = user_sum[user.id_]

        
        print(' ')
        sum1 = 0
        sum2 = 0
        # TODO: implement user based recap, not fixed values.
        print('%12s  %10s  %10s' %('journal', 'user1', 'user2'))
        for imbalance_journal_entry_keys in imbalance_journal_entry.keys():
            #print(report_section_key)
            line_value = []
            for imbalance_journal_entry_user_key in imbalance_journal_entry[imbalance_journal_entry_keys]:
                # TODO: confirm this occurs in proper order
                line_value.append(imbalance_journal_entry[imbalance_journal_entry_keys][imbalance_journal_entry_user_key])
            print('%12s  %10.2f  %10.2f' %(imbalance_journal_entry_keys, line_value[0], line_value[1]))
            sum1 += line_value[0]
            sum2 += line_value[1]
        print('%12s  %10.2f  %10.2f' %('sum', sum1, sum2))
        if sum1 > sum2:
            print('user1 owes %10.2f to user2' %sum1)
        elif sum2 > sum1:
            print('user2 owes %10.2f to user1' %sum2)

        # # this print all imblance statement line with user amount under it.
        # for key_ in imbalance_journal_entry.keys():
        #     journal_entry1 = JournalEntry.objects.get(id_=key_)
        #     print(journal_entry1.statement_line,)
        #     print('    ', imbalance_journal_entry[key_])
        if recap == True:
            # this print imbalance per user with their respective amount after it.
            for user in list(User.objects()):
                print(' ')
                print('Imbalance transaction for user ', user.name)
                for key_ in imbalance_journal_entry.keys():
                    journal_entry1 = JournalEntry.objects.get(id_=key_)
                    print(journal_entry1.id_, str(journal_entry1.statement_line.date)[:-9], journal_entry1.statement_line.account_number, journal_entry1.statement_line.description, imbalance_journal_entry[key_][user.id_])

    def account_recap(account_number, date_from, date_to):
        journal_entry_list =  list(JournalEntry.objects(date__gte=date_from, date__lte=date_to))
        account_class = Account.get_account_by_number(account_number)
        Transaction.header()
        credit = 0
        debit = 0
        for journal_entry in journal_entry_list:
            
            i = 0

            # for transaction in journal_entry.transactions:

            #     if transaction.account_number == account_class:
            #         print(journal_entry)
            #         # transaction = journal_entry.transactions[0]
            #         print(transaction)
            #         credit += transaction.credit
            #         debit += transaction.debit
            for transaction in journal_entry.transactions:

                if transaction.account_number == account_class and i == 0:
                    print(journal_entry)
                    print(transaction)
                    credit += transaction.credit
                    debit += transaction.debit
                    i += 1

        print('credit %s debit %s' %(credit, debit))




class JournalEntry(Document):
    id_ = IntField(required=True)
    date = DateTimeField(default=None)
    statement_line = ReferenceField(StatementLine)
    transactions = ListField(ReferenceField(Transaction))

    def header():
        print("%6s %10s %15s %10s %12s" %('id_', 'date', 'statement_line', 'amount' 'transactions',))

    def __str__(self):
        # output_transaction_id = []
        # if self.transactions:
        #     for transaction in self.transactions:
        #         output_transaction_id.append('%s, %s' %(transaction.account_number.number, transaction.account_number.description))
        amount = self.statement_line.credit + self.statement_line.debit + self.statement_line.interest + self.statement_line.advance + self.statement_line.reimbursement

        return "%6s %10s %15s %8.2f" %(self.id_, self.date.date(), self.statement_line.description, amount, )


    def create_from_statement_line(statement_line_id_):
        print('')
        # Confirm it does not already exist.
        statement_line = StatementLine.get_statement_line(statement_line_id_)
        StatementLine.header()
        print(statement_line)

        statement_line_interest = 0

        try: 
            existing_journal_entry = JournalEntry.objects.get(statement_line=statement_line)
            # existing_journal_entry = StatementLineToJournalEntry.objects.get(statement_line=statement_line)

            # print('line found')

        except DoesNotExist:
            pass
            # print('No JournalEntry exist on this line, creating new one.')

        # consolidate advance / reimbursement in credit / debit transaction.
        statement_line_credit, statement_line_debit, statement_line_interest = helpers.statement_line_group_money_transfer(statement_line)

        try:
            if not statement_line.account_type:
                print('no account type')
                account1 = Account.get_account_by_number(int(statement_line.account_number))
        
            else:
                account1 = Account.get_account(int(statement_line.account_number), statement_line.account_type)
        
        except DoesNotExist:
            print('account1 = ', account1)
            print('this account does not exist! %s' %statement_line.account_number)
            sys.exit()

        print('account1 = ', account1)
    
        # add first Transaction from the source account in statement line.
        transaction1 = Transaction.add_transaction(date=statement_line.date,
                                                    account_number=account1,
                                                    credit=statement_line_credit,
                                                    debit=statement_line_debit, 
                                                    source=None, 
                                                    source_ref=statement_line,
                                                    )
        
        transaction1.save()


        # Step 1
        # Check if existing transaction are present, update source if yes.
        # This actually happens when an inter account transaction is open (unreconciled)
        # print('statement_line.account_type=', statement_line.account_type)
        # if statement_line.account_type is not None:

        #     try:

        #         # statement_line_value = statement_line.credit + statement_line.debit

        #         # open_transaction = list(Transaction.objects().aggregate({"$addFields": {"total": {"$add": ["$credit", "$debit", ]}}}, {"$match": {"total":{"$eq": statement_line_value}, "account_number":{"$ne": Account.get_account(account_number=statement_line.account_number, account_type=statement_line.account_type).id, "$in": [account.id for account in list(Account.objects(reconciled=True))]}, "date":{"$eq": statement_line.date}}}))
        #         open_transaction = list(Transaction.objects().aggregate({"$match": {"credit":{"$eq": transaction1.debit}, "debit":{"$eq":transaction1.credit}, "account_number":{"$ne": transaction1.account_number.id, "$in": [account.id for account in list(Account.objects(reconciled=True))]}, "date":{"$eq": statement_line.date}}}))
        #         # print(open_transaction)
                
        #     except DoesNotExist:
        #         open_transaction = []

        # elif statement_line.account_type == None:
        try:
            # statement_line_value = statement_line.credit + statement_line.debit
            # filter transaction based on total value
            # Open transaction are same sum, reconciled account with same amount.
            # open_transaction = list(Transaction.objects().aggregate({"$match": {"cedit":{"$eq": transaction1.debit}, "debit":{"$eq": transaction1.credit}, "account_number":{"$ne": transaction1.account_number.id, "$in": [account.id for account in list(Account.objects(reconciled=True))]}, "date":{"$eq": statement_line.date}}}))
            open_transaction = list(Transaction.objects(credit=transaction1.debit, 
                                                        debit=transaction1.credit, 
                                                        account_number__ne=transaction1.account_number.id, 
                                                        account_number__in=[account.id for account in list(Account.objects(reconciled=True))], 
                                                        date=transaction1.date,

                                                        ))
        
        except DoesNotExist:
            open_transaction = []

        print('len open transaction = ', len(open_transaction))

        if len(open_transaction) > 0:
            # TODO: this can be removed as we now get transaction with same price with the aggregate function
            statement_line_sum = statement_line.credit + statement_line.debit + statement_line.interest + statement_line.advance + statement_line.reimbursement
            

            print('here are the open transaction that matches this one. ')
            i = 0
            # warning_transaction = None
            Transaction.header()
            transaction_document = []
            for transaction in open_transaction:
                i += 1
                # print('transaction =', transaction)
                # transaction = Transaction.objects.get(id=transaction['_id']) # we need to keep this as it transform open_transaction from a list of dict to list of documents
                # transaction_document.append(transaction)
                print(i, transaction)
                # transaction_sum = transaction.credit + transaction.debit
                # if transaction_sum != statement_line_sum:
                #     warning_transaction = True

            # open_transaction = transaction_document # we need a list of doc not a dict as the aggregate gives us.


            print("Select which transaction you would like to link to this one. (presse enter to skip and create a new one)")
            # if warning_transaction == True:
            #     print("Warning!!! some transaction does not have the same amount as statement_line!!!")
            
            if len(open_transaction) == 1: # So far most of result when 1 result came out were the good one, and we did not had same amount, now with same amount we can use result if only 1 comes out.
                transaction_choice = 1
            
            else:
                transaction_choice = input(">> ")

            if transaction_choice == '':
                print('transaction skipped')
                open_transaction = []
                pass

            else: # Transactoin choice is 1 so we select it by default
                selected_transaction = open_transaction[int(transaction_choice)-1]
                print('selected transaction = ', selected_transaction)
                print(selected_transaction.source_ref)
                journal_entry_from_transaction = list(JournalEntry.objects(statement_line=selected_transaction.source_ref))
                print('journal_entry from transaction = ')
                print(journal_entry_from_transaction)
                journal_entry1 = journal_entry_from_transaction[-1]

                # journal_entry1 = selected_transaction.source_ref
                journal_entry1.transactions.append(transaction1)
                journal_entry1.transactions[1].source_ref = statement_line
                journal_entry1.transactions[1].save()
                journal_entry1.save()

                new_journal_entry = JournalEntry(id_=getNextSequenceValue('JournalEntryId'),
                                            date=statement_line.date,
                                            statement_line=statement_line,
                                            )

                new_journal_entry.transactions.append(transaction1)
                print('selelcted transaction = ', selected_transaction)
                # reverse_transaction = Transaction.create_reverse_transaction(selected_transaction)
                reverse_transaction = selected_transaction
                reverse_transaction.source_ref = journal_entry1.transactions[0].source_ref
                reverse_transaction.save()

                new_journal_entry.transactions.append(reverse_transaction)
                new_journal_entry.save()


                print('journal entry added to existing one')

                # Now that the 2 transaction have been saved, manage the interest
                if statement_line_interest != 0 or statement_line.interest != 0:

                    # add 2 transaction to the journal entry to add interest expense to the entry.
                    # the interest expense were previously entered as credit to the account.
                    transaction3 = Transaction.add_transaction(date=statement_line.date,
                                account_number=Account.get_account(int(statement_line.account_number), statement_line.account_type),
                                credit=statement_line.interest,
                                debit=0, 
                                source=None, 
                                source_ref=statement_line,
                                )

                    transaction3.save()

                    transaction4 = Transaction.add_transaction(date=statement_line.date,
                                account_number=Account.objects.get(number=513010),
                                credit=0,
                                debit=statement_line.interest, 
                                source=None, 
                                source_ref=statement_line,
                                )

                    transaction4.save()
                    new_journal_entry.transactions.append(transaction3)
                    new_journal_entry.transactions.append(transaction4)
                    transaction4.user_amount = transaction3.user_amount # take the parent ratio as the interest expense ratio.
                    transaction4.save()
                    new_journal_entry.save()


                return 'ok'


                # find the journal entry for "selected_transaction" and add this transaction to it


                # TODO: need to add a parameter to show the line has been reconciled.
            # print('past_statement_line = ', past_statement_line)

            # HERE WE ARE
            # we should always look into all possible account for past statement line
            # exception_found = False
            # if len(past_statement_line) > 0:
            #     for exception in EXCEPTIONS:
            #         if exception['description'] == statement_line.description:
            #             if exception['account_number'] == statement_line.account_number:
            #                 past_statement_line.append(list(StatementLine.objects(account_number__in=exception['others_accounts'],
            #                                                     account_type=exception['account_type'],
            #                                                     description=exception['description'],
            #      
                # new_journal_entry = JournalEntry.objects.get(transactions__in=[selected_transaction])


        if len(open_transaction) == 0: 


            
            past_statement_line = list(StatementLine.objects(account_number=statement_line.account_number,
                                                account_type=statement_line.account_type,
                                                description=statement_line.description,
                                                id__lt=statement_line.id, # make sure the statement_line has been evaluated before the one we are threating.
                                                ))

            print('len past statement_line =', len(past_statement_line))

            #                 # print('past statement_line appened!')
            #                 # print(past_statement_line)
            #                 print('exception_found == True')
            #                 exception_found = True
            #                 break


            # print('statement_line destination account = ', statement_line.destination_account)

            if statement_line.destination_account not in ['', None, 0]:
                result_account = Account.objects.get(number=statement_line.destination_account)
            
            elif len(past_statement_line) > 0:
                # TODO: Would need to find the most recent past_statement_line to be able to have proper account if modification were made.
                # Until we get the most recent, we use the last one.
                selected_past_statement_line = past_statement_line[-1] # Best way to find the earlyest line for now. (need improvement.)
                # print(selected_past_statement_line.to_json())

                # Find the journal entry with this line (assuming it exist)
                # TODO: what if it does not exist?
                # if exception_found == False:
                #     print(past_statement_line)
                #     past_journal_entry = helpers.choose_from_list(list(JournalEntry.objects(statement_line=selected_past_statement_line)))
                # else:
                # print('extended past statement line!!')
                # past_journal_entry = helpers.choose_from_list(list(JournalEntry.objects(statement_line__in=past_statement_line)))
                past_journal_entry = list(JournalEntry.objects(statement_line__in=past_statement_line))
                past_output_transaction = past_journal_entry[-1].transactions[-1]
                Account.header()
                # print(past_output_transaction.account_number)

                # threat_choice = input('Would you like to select the destination account manually? (y)/n >> ')
                # if threat_choice == 'y':
                #     pass
                #     # TODO: revert to next else statement (manual account choice.)
                result_account = past_output_transaction.account_number

                
            else:
                result_account = helpers.choose_account()


            if result_account.reconciled == True and account1.reconciled == True:
                # this transaction should be reconciled at some point, we did not find it this time, but should when threating the other side of transaction.
                new_journal_entry = JournalEntry(id_=getNextSequenceValue('JournalEntryId'),
                                            date=statement_line.date,
                                            statement_line=statement_line,
                                            )

                new_journal_entry.transactions.append(transaction1)
                new_journal_entry.save()
                return 'ok' # we assume we will find the corresponding transaction at some other point.

            transaction2 = Transaction.add_transaction(date=statement_line.date,
                                                        account_number=result_account,
                                                        #credit=statement_line_debit,
                                                        credit=transaction1.debit,
                                                        #debit=statement_line_credit, 
                                                        debit=transaction1.credit,
                                                        source=None, 
                                                        source_ref=None,
                                                        )

            transaction2.save()

            new_journal_entry = JournalEntry(id_=getNextSequenceValue('JournalEntryId'),
                                            date=statement_line.date,
                                            statement_line=statement_line,
                                            )
            new_journal_entry.save()

            new_journal_entry.transactions.append(transaction1)
            new_journal_entry.transactions.append(transaction2)
            new_journal_entry.save()

            
            #################################
            # Check ratios
            # TODO: this would need a function to itself.
            # print('transaction2.user_amount = ', transaction2.user_amount)
            if transaction2.user_amount == {}: # We take for granted the transaction1 has always a ratio as it's a know account with defined ratio.
                ratio_choice = None

                output_ratio = check_rules(new_journal_entry) # this is a preset rules for specific transactions, instead of asking every time

                if output_ratio != None: 
                    ratio_choice = output_ratio[0]

                else:
                    print('Output account has no ratio set, use parent ratio?')
                    print('Parent ratio: ', transaction1.account_number.user_ratio)
                    if statement_line.ratio_code is not None:
                        # RATIO_CODE = {'f': 1,
                        #             'j': 0,
                        #             'e': 0.5,
                        #             'tf': 1,
                        #             'tj': 0,
                        #             'c': 0.5,
                        #             'm': 0.7,
                        #             }
                        # ratio_choice = RATIO_CODE.get(statement_line.ratio_code)
                        ratio_choice = statement_line.ratio_code

                    else:
                        use_parent_ratio_choice = input('(y)/n >> ')

                        if use_parent_ratio_choice == 'y' or use_parent_ratio_choice == '':
                            transaction2.user_amount = transaction1.user_amount
                            transaction2.save()
                            # print('parent ratio used')

                        else:
                            ratio_choice = input('What ratio should we set to user1 (0-1)? >> ')

                if ratio_choice != None:

                    users = list(User.objects())
                    transaction2.user_amount = {str(users[0].id_): float(ratio_choice) * (transaction2.credit + transaction2.debit), 
                                                str(users[1].id_): (1-float(ratio_choice)) * (transaction2.credit + transaction2.debit)}
                    transaction2.save()
            # we need to keep the difference between accounts to see the transfer difference somehow.
            # elif transaction1.account_number.user_ratio != transaction2.account_number.user_ratio:
            #     transaction2.user_amount = transaction1.user_amount # take user amount from to affect to account.
            #     transaction2.save()



        # this code is doubled at line 1058
        # Now that the 2 transaction have been saved, manage the interest
        if statement_line_interest != 0 or statement_line.interest != 0:

            # add 2 transaction to the journal entry to add interest expense to the entry.
            # the interest expense were previously entered as credit to the account.
            transaction3 = Transaction.add_transaction(date=statement_line.date,
                        account_number=Account.get_account(int(statement_line.account_number), statement_line.account_type),
                        credit=statement_line.interest,
                        debit=0, 
                        source=None, 
                        source_ref=statement_line,
                        )

            transaction3.save()

            transaction4 = Transaction.add_transaction(date=statement_line.date,
                        account_number=Account.objects.get(number=513010),
                        credit=0,
                        debit=statement_line.interest, 
                        source=None, 
                        source_ref=statement_line,
                        )

            transaction4.save()
            new_journal_entry.transactions.append(transaction3)
            new_journal_entry.transactions.append(transaction4)
            transaction4.user_amount = transaction3.user_amount # take the parent ratio as the interest expense ratio.
            transaction4.save()
            new_journal_entry.save()




class JournalEntryToTransaction(Document):

    journal_entry = ReferenceField(JournalEntry)
    transaction = ReferenceField(Transaction)

def get_exchange_rate():
    # Keep on
    pass

def check_rules(journal_entry, ):
    if journal_entry.statement_line.description == 'SUBWAY # 27934           COTEAU-DU-LACQC' and journal_entry.statement_line.credit < 20:
        return [1,0]

    elif journal_entry.statement_line.description == "MCDONALD'S #23799  Q04   SAINT-ZOTIQUEQC" and journal_entry.statement_line.credit < 20:
        return [1,0]

    elif journal_entry.statement_line.description == "JARDINS ST CLET          SAINT-CLET   QC":
        return [1.0]

    else:
        return None


def find_reconciled_error(account_number=None):
    # Account number shoudl be numeric and be an actual reconciled account
    # the transaction should all be recorded from a line, this check for discreptancy on this statement.

    if account_number:

        if account_number_classes.reconciled != True:
            print('Account is not reconciled, chose another one')
            return None

        account_number_class = Account.get_account_by_number(account_number)
        account_number_classes = list().append(account_number_class)

    else:
        account_number_classes = list(Account.objects(reconciled=True))



    transactions = list(Transaction.objects(account_number__in=account_number_classes))

    # reconciled account = list(Transaction.objects(reconciled=True))

    error_found = []

    for transaction in transactions:
        if transaction.source_ref == None:
            error_found.append(transaction)
            print(transaction)

def find_journal_entry(account_number_form, account_number_to):
    account_number_from_class = Account.get_account_by_number(account_number_form)
    account_number_to_class = Account.get_account_by_number(account_number_to)

    for journalentry in list(JournalEntry.objects()):
        if journalentry.transactions[0].account_number == account_number_from_class:
            if journalentry.transactions[-1].account_number == account_number_to_class:
                print(journalentry)
                for transaction in journalentry.transactions:
                    print(transaction)

def print_account_list():
    for account in list(Account.objects()):
        print(account)


if __name__ == "__main__":
    #Statement.import_statement_from_file('./.data/2020-01_releve.csv', ',')
    connect('test')
    unittest.main()

        

from mongoengine import *
from datetime import datetime
from bson import ObjectId
import csv

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
    id_ = IntField(required=True)
    name = StringField()

class Account(Document):
    """This is the Chart of Account accounts items"""
    number = IntField(min_value=100000, max_value=999999, unique=True) 
    parent_account = ReferenceField("self", default=None) # Not in use
    child_account = ReferenceField("self", default=None) # Not in use
    description = StringField(max_length=200, required=True)
    type_ = StringField(max_length=3, choices=ACCOUNT_TYPE)
    user_ratio = MapField(ReferenceField(User), default=None) # Needs testing, should be a dict

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

    def __str__(self):
        return "%s %s %s %s %s %s %s %s %s %s %s %s" %(self.id_, self.date, self.account_number, self.account_type, self.line_number, self.description,
                                                        self.credit, self.debit, self.interest, self.advance, self.reimbursement, self.balance)

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

    # We do not manage currency for now.
    #currency_amount = currency_rate = FloatField(default=0)
    #currency = StringField(max_length=3, default="CAD")
    #currency_rate = FloatField(default=1)

    def add_transaction(date, account_number, credit, debit, source, source_ref):
        # keep on
        new_transaction = Transaction(id_=getNextSequenceValue('TransactionId'), 
                                    date=date,
                                    account_number=account_number,
                                    credit=credit,
                                    debit=debit,
                                    source=source,
                                    source_ref=source_ref)
        new_transaction.save()

        print("New transaction saved : ", new_transaction.id)

        return new_transaction

class JournalEntry(Document):
    id_ = IntField(required=True)
    transactions = ListField(ReferenceField(Transaction))

def get_exchange_rate():
    # Keep on
    pass

if __name__ == "__main__":
    #Statement.import_statement_from_file('./.data/2020-01_releve.csv', ',')
    pass

        
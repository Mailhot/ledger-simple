import objects
import datetime


def import_chart_of_account(filename='./.data/ChartofAccounts.csv'):
    objects.Account.import_accounts_from_file(filename=filename)


def process_statement(id_):
    statement = objects.Statement.objects.get(id_=id_)

    for line in objects.StatementLine.objects(statement=statement):

        objects.JournalEntry.create_from_statement_line(line.id_) # To be finished


if __name__ == "__main__":
    #objects.init_counters()
    


    if not objects.User.objects():
        objects.User.init_2_users()

    user1 = objects.User.objects[0]
    user2 = objects.User.objects[1]
    #import_chart_of_account()
    #objects.Statement.import_statement_from_file('./.data/2020-01_releve.csv', ',', True)
    #process_statement(29)
    objects.reports.income_statement(datetime.date(year=2020, month=1, day=1), datetime.date(year=2020, month=12, day=1))
    #objects.reports.general_ledger(datetime.date(year=2020, month=1, day=1), datetime.date(year=2020, month=12, day=1))

    


    
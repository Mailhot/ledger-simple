import objects


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
    #objects.Statement.import_statement_from_file('./.data/2020-01_releve.csv', ',')
    process_statement(17)

    


    
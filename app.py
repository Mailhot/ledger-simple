import objects


def import_chart_of_account(filename='./.data/ChartofAccounts.csv'):
    objects.Account.import_accounts_from_file(filename=filename)


if __name__ == "__main__":
    #objects.init_counters()
    #objects.Statement.import_statement_from_file('./.data/2020-01_releve.csv', ',')


    if not objects.User.objects():
        objects.User.init_2_users()

    user1 = objects.User.objects[0]
    user2 = objects.User.objects[1]

    objects.JournalEntry.create_from_statement_line(statement_line_id_) # To be finished


    
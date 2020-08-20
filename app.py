import objects


if __name__ == "__main__":
    #objects.init_counters()
    #objects.Statement.import_statement_from_file('./.data/2020-01_releve.csv', ',')

    if not objects.User.objects():
        objects.User.init_2_users()

    user1 = objects.User.objects[0]
    user2 = objects.User.objects[1]

    # objects.Account.add_account(number=221020, 
    #                             parent_account=None, 
    #                             child_account=None, 
    #                             description='709733-LN3', 
    #                             type_='NCL', 
    #                             user_ratio={str(user1.id_): 0.7, str(user2.id_): 0.3},
    #                             account_number=None, 
    #                             account_type=None,
    #                             )

    objects.Account.import_accounts_from_file(filename='./.data/ChartofAccounts.csv')
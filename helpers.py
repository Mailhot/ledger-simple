import objects
def choose_account():
    exit_bol = False

    while True:
        account_number_choice = input('what account should this statement go to? >> ')

        try:
            result_account = objects.Account.objects.get(number=int(account_number_choice))
            print('result found: ', result_account)

        except Exception as e: 
            print(e)
            result_account = None

        if result_account != None:

            return result_account

            
            exit_bol = True


        else:
            print('account not found, please try again.')
            for account_ in objects.Account.objects():
                print(account_.number, account_.description, account_.account_number, '-', account_.account_type)


            
        if exit_bol == True:
            break



def statement_line_group_money_transfer(statement_line):
    """this function groups money transfers when the statement line include something different than the credit and debit standart. 
    for example, it could have the interest, advance and reimbursement line filled. 
    we group those lines into the debit and credit lines. 
    if there is an interest, we add a journalEntry with the interest expense.
    """

    credit = 0
    debit = 0
    interest = 0

    money_transfer = dict()
    money_transfer['debit'] = statement_line.debit
    money_transfer['credit'] = statement_line.credit
    money_transfer['interest'] = statement_line.interest
    money_transfer['advance'] = statement_line.advance
    money_transfer['reimbursement'] = statement_line.reimbursement

    values_keys = []
    for key in money_transfer.keys():
        if money_transfer[key] != 0:

            values_keys.append(key)

    if len(values_keys) == 1:
        if values_keys[0] in ['debit', 'credit']:
            credit = statement_line.credit
            debit = statement_line.debit

        elif values_keys[0] in ['advance', 'reimbursement']:
            credit = statement_line.reimbursement
            debit = statement_line.advance

        elif values_keys[0] in ['interest']:
            # This is an interes payment only, no effect on account amount. 
            credit = statement_line.interest
            debit = 0
            interest = statement_line.interest

    elif len(values_keys) > 1: # this should be an interest/ reimbursement combination of an automated payement.
        credit = statement_line.reimbursement + statement_line.interest
        debit = 0
        interest = statement_line.interest

    return credit, debit, interest

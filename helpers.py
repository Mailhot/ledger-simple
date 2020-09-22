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

def init_dict_or_add(dict_, key, value):
    """ this function takes a dict a key and a value.
    it check if the key already exist in the dict, if not it adds the key / value
    if it does it adds the value to the existing value
    """
    if key in dict_.keys():
        dict_[key] += value
    else:
        dict_[key] = 0
        dict_[key] += value
    return dict_

def init_dict_or_substract(dict_, key, value):
    """ this function takes a dict a key and a value.
    it check if the key already exist in the dict, if not it adds the key / value
    if it does it adds the value to the existing value
    """
    if key in dict_.keys():
        dict_[key] -= value
    else:
        dict_[key] = 0
        dict_[key] -= value
    return dict_

def choose_from_list(list_):
    if len(list_) > 1:

        item_number = 1
        for item in list_:

            print(item_number, item)
            item_number += 1
        while True:

            item_choice = input('what item would you like to choose? [1]>> ')
            if item_choice == '':
                item_choice = 1

            try:
                item_choice_int = int(item_choice)
            except ValueError:
                print('%s is not a valid choice, try again.' %item_choice)
                continue

            return list_[item_choice_int]
    elif len(list_) == 1:
        return list_[0]
    else:
        return None


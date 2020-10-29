import objects
import unittest
import csv






class StatementFunction():
    """This is an attempt to separate function from objects,
    we also want to make code clearer."""
    def find_description_amount(line):
        """take the description with potentially an amount added.
        remove the amount if it has, return the original description if it had not.
        """
        # check for description with amount, remove amount as it would wrongly not find accounts afterwards.
        if '$' in line:
            description_list = line.split(':')
            split_description = description_list[0]
        else:
            split_description = line

        return split_description

    def import_file(filename, delimiter=',', header=None):
        """This function import a file and split it into list of lines"""
        with open(filename) as the_file:
            lines = []
            csv_reader = csv.reader(the_file, delimiter=delimiter)
            header_passed = False
            for line in csv_reader:
                if header == True and header_passed == False: # skip first line if header = true
                    header_passed = True
                    continue

                if len(line) > 1:
                    lines.append(line)

        return lines      

    def import_statemet_line(lines, ):
        """ Import statement line regardless of files we imported it from."""
        threated_lines = 0
        imported_lines = 0

        for line in lines:
            line_counter = 0
            first_line = True

                
            # find the first line that is not empty.
            if len(line) == 15:
                if line[14] not in [None, 0, '']:
                    destination_account = int(line[14])
                    
            else:
                destination_account = None

            split_description = StatementFunction.find_description_amount(line[5])

            existing_lines = objects.StatementLine.objects(date=line[3],
                                                account_number=line[1],
                                                account_type=line[2],
                                                line_number=line[4],
                                                description=split_description,
                                                credit=objects.StatementLine.to_float_or_zero(line[7]),
                                                debit=objects.StatementLine.to_float_or_zero(line[8]),
                                                interest=objects.StatementLine.to_float_or_zero(line[9]),
                                                advance=objects.StatementLine.to_float_or_zero(line[11]),
                                                reimbursement=objects.StatementLine.to_float_or_zero(line[12]),
                                                balance=objects.StatementLine.to_float_or_zero(line[13]),
                                                destination_account=destination_account,
                                                )

            if len(existing_lines) > 1:
                print('line already existing, skipped!')
                continue

            else:
                new_line = objects.StatementLine.create_line(date=line[3],
                                                    account_number=line[1],
                                                    account_type=line[2],
                                                    line_number=line[4],
                                                    description=split_description,
                                                    credit=objects.StatementLine.to_float_or_zero(line[7]),
                                                    debit=objects.StatementLine.to_float_or_zero(line[8]),
                                                    interest=objects.StatementLine.to_float_or_zero(line[9]),
                                                    advance=objects.StatementLine.to_float_or_zero(line[11]),
                                                    reimbursement=objects.StatementLine.to_float_or_zero(line[12]),
                                                    balance=objects.StatementLine.to_float_or_zero(line[13]),
                                                    statement=None,
                                                    destination_account=destination_account,
                                                    )
                new_line.save()

            if first_line == True:
                first_line = False
                    
            line_counter += 1

        print('%s new lines imported.' %imported_lines)
        print('%s lines threaded' %threated_lines)


    def create_from_statement_line(statement_line_id_):
        print('')
        # Confirm it does not already exist.
        statement_line = objects.StatementLine.get_statement_line(statement_line_id_)
        objects.StatementLine.header()
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


    



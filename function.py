import objects
import unittest
import csv
import datetime
import helpers






class StatementFunction():
    """This is an attempt to separate function from objects,
    we also want to make code clearer."""
    def find_description_amount(description):
        """take the description with potentially an amount added.
        remove the amount if it has, return the original description if it had not.
        """
        # check for description with amount, remove amount as it would wrongly not find accounts afterwards.
        if '$' in description:
            description_list = line.split(':')
            split_description = description_list[0]
        else:
            split_description = description

        return split_description

    def export_statement_edit(filename, complete=False):
        ''' export all statement lines to be threated manuall in google sheet, 
        complete define if statement lines that already have completed values should be exported
        '''

        statement_lines = list(objects.StatementLine.objects())
        if complete == False:
            
            
            # print(transactions_ids)
            statement_lines_out = [x for x in statement_lines if x.destination_account is 0]
            print('Filtered export : %s out of %s statement_line exported' %(len(statement_lines_out), len(statement_lines)))
        else:
            statement_line_out = satement_lines

        # Export to file
        with open(filename, 'w') as the_file:
            file_writer = csv.writer(the_file, delimiter=',', quotechar='"', lineterminator="\n")


            for statement_line in statement_lines_out:
                statement_line_sum = -statement_line.credit + statement_line.debit - statement_line.interest + statement_line.advance - statement_line.reimbursement

                file_writer.writerow([statement_line.id,
                                    statement_line.account_number,
                                    statement_line.account_type, 
                                    statement_line.date, 
                                    statement_line.description,
                                    statement_line_sum,
                                    ])

    def import_statement_edit(filename):
        ''' re-import data from previous export (export_statement_edit)
        '''

        with open(filename) as the_file:
            file_reader = csv.reader(the_file, delimiter=',', quotechar='"')
            line_count = 0
            error_count = 0
            for row in file_reader:
                print(row)
                try:
                    statement_line = objects.StatementLine.objects.get(id=row[0])
                except ValueError:
                    print('Error statement line does not exist for: %s' %row[0])
                    error_count += 1
                    continue

                if row[6]:
                    print(row[7])
                    statement_line.destination_account = row[7]
                    if row[8] and row[8] is not '#N/A':
                        statement_line.ratio_code = float(row[8]) / 100
                    statement_line.save()

                line_count += 1
            print('Processed %s lines with %s errors' %(line_count, error_count))



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

    def import_statement_lines(lines=None,):
        """ Import statement line regardless of files we imported it from."""


        if lines == None: 
            lines = list(objects.StatementLine.objects())

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

            

            existing_lines = objects.StatementLine.objects(date=line[3],
                                                account_number=line[1],
                                                account_type=line[2],
                                                line_number=int(line[4]),
                                                description=line[5],
                                                credit=objects.StatementLine.to_float_or_zero(line[7]),
                                                debit=objects.StatementLine.to_float_or_zero(line[8]),
                                                # interest=objects.StatementLine.to_float_or_zero(line[9]),
                                                # advance=objects.StatementLine.to_float_or_zero(line[11]),
                                                # reimbursement=objects.StatementLine.to_float_or_zero(line[12]),
                                                balance=objects.StatementLine.to_float_or_zero(line[13]),
                                                # destination_account=destination_account,
                                                )


            if len(existing_lines) >= 1:
                print('existing lines')
                for line in existing_lines:

                    print(line)
                print('credit card line already existing, skipped!')
                continue

            else:
                new_line = objects.StatementLine.create_line(date=line[3],
                                                    account_number=line[1],
                                                    account_type=line[2],
                                                    line_number=line[4],
                                                    description=line[5],
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
                print('line added %s'% new_line.id)
                print(new_line)

            if first_line == True:
                first_line = False
                    
            line_counter += 1

        print('%s new lines imported out of %s lines threated.' %(imported_lines, threated_lines))


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

        if len(open_transaction) == 0: 

            past_statement_line = list(StatementLine.objects(account_number=statement_line.account_number,
                                                account_type=statement_line.account_type,
                                                description=find_description_amount(statement_line.description), # Remove the amount if there is in the description.
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
                                                        credit=transaction1.debit,
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


    def process_statement_lines(force=False):
        print('')
        print('processing statement')
        print('')

        lines_imported = 0
        lines_threated = 0

        for line1 in list(objects.StatementLine.objects()):
            lines_threated += 1

            if force == False:
                #confirm the line has not already been processed.
                line_entry = list(objects.JournalEntry.objects(statement_line=line1))
                # print(line_entry)
                if len(line_entry) >= 1:
                    print('entry skipped already processed')
                    continue

                    # for line2 in line_entry:
                    #     threat_line = False
                    #     for transaction in line2.transactions:
                    #         if len(transaction.user_amount) != len(objects.User.objects()):
                    #             # delete this transaction and retreat the line
                    #             threat_line = True
                    #     if threat_line == True:
                    #         print("DELETE LINE")
                    #         for transaction in line2.transactions:
                    #             transaction.delete()
                    #         line2.delete()
                    #         objects.JournalEntry.create_from_statement_line(line1.id_)
                    #         lines_imported += 1

                elif len(line_entry) > 1:
                    # TODO: print the 2 entry and chose to delete 1 of them
                    pass

                else:
                    objects.JournalEntry.create_from_statement_line(line1.id_)
                    lines_imported += 1

            elif force == True:

                line_entry = list(objects.JournalEntry.objects(statement_line=line1))
                # print(line_entry)
                if len(line_entry) > 0:
                    for line2 in line_entry:
                        
                        for transaction in line2.transactions:
                            # print(type(transaction))
                            try:
                                transaction_class = objects.Transaction.objects.get(id=transaction.id)
                            except objects.DoesNotExist:
                                print('transaction does not exist skipping')
                                continue
                            transaction_class.delete()
                        line2.delete()

                objects.JournalEntry.create_from_statement_line(line1.id_)
                lines_imported += 1

        print('threated %s lines out of %s lines processed.' %(lines_imported, lines_threated))


    def credit_card_bill_parser(file, ):

        print('')
        print('Parsing credit card bill to generate statement_line')
        print('')

        # bill = objects.Statement.init_statement(file,)
        balance_checker = False
        stop_words = ['Détail des frais de crédit', 
                        'Credit charge details',
                        'Total:',
                        'Total :                                    ',
                        'Total :',
                        'Détail des frais de crédit ',
                        'Desjardins BONUSDOLLARS Rewards Program',
                        ]

        
        # with open(file, "r",  encoding="ISO-8859-1") as the_file:
        with open(file, "r",  encoding="utf-8") as the_file: #for some files the default encoding seem to fall back to iso-889-1 instead of utf-8
            total_line = 0
            line_added = 0
            transaction_line_counter = None
            file_reader = the_file.readlines()
            line_count = 0
            for line in file_reader:
                total_line +=1
                elements = line[:-1].split('\t')
                # filter the element a little
                line_filtered = []

                for item in elements:
                    if item != "":
                        line_filtered.append(item)



                print(line_filtered)

                # if line_filtered[0] == "Current transaction summary":
                #     balance == True
                # else line_filtered[0] == 
                if len(line_filtered) < 1:
                    continue
                elif len(line_filtered) == 1:
                    if line_filtered[0].startswith('Statement date:'):
                        line_filtered = ['Statement date:', line_filtered[0][14:]]

                # Get what we need to build the bill recap
                # bill.update_values(line_filtered)


                # print("previous balance report = ", bill.previous_balance_report)


                if line_filtered[0].startswith('Transactions made with the card of'):
                    transaction_line_counter = 0
                    print("Starting loggin line")
                    continue

                elif line_filtered[0].startswith('Transaction date'):
                    transaction_line_counter = 2
                    print("Starting loggin payments")
                    continue

                # elif line_filtered[0].startswith('Total:') or line_filtered[0].startswith('Détail des frais de crédit') or line_filtered[0].startswith('Total :'):

                elif line_filtered[0].strip() in stop_words:
                    transaction_line_counter = None
                    print("No longer logging lines")
                    continue

                elif type(transaction_line_counter) == int:
                    # print(transaction_line_counter)
                    # print(line_filtered[0])
                    # print('\n'.join(difflib.ndiff([line_filtered[0]], [stop_words[0]])))
                    # if line_filtered[0] != stop_words[0]:
                    #     print('they are the same word')
                    # print(type(stop_words[0]))
                    transaction_line_counter += 1
                    if transaction_line_counter <= 2: # skip first line
                        continue
                    else:
                        datetime_object = helpers.parse_date(line_filtered[0])
                        datetime_object_posted = helpers.parse_date(line_filtered[1])

                        if line_filtered[4].startswith('CR'):
                            credit = 0
                            debit = float(line_filtered[4][2:].replace(',', ''))

                        else:
                            debit = 0
                            credit = float(line_filtered[4].replace(',', ''))
                        #TODO: Need to add the journal entry and then the transaction pair.
                        # newline1 = Transaction.add_transaction
                        existing_lines = objects.StatementLine.objects(date=datetime_object,
                                                            account_number=211100,
                                                            account_type=None,
                                                            line_number=int(line_filtered[2]),
                                                            description=line_filtered[3],
                                                            credit=credit,
                                                            debit=debit,
                                                            # interest=None,
                                                            # advance=None,
                                                            # reimbursement=None,
                                                            # balance=None,
                                                            #destination_account=line_filtered[6],
                                                            #statement=bill,
                                                            #ratio_code=line[5],
                                                            )
                        

                        print('existing line: ', len(existing_lines))
                        if len(existing_lines) >= 1:
                            print('existing lines')
                            for line in existing_lines:

                                print(line)
                            print('line already existing, skipped!')

                            continue

                        else:
                            if len(line_filtered) > 5:
                                newline1 = objects.StatementLine.create_line(date=datetime_object,
                                                                    account_number=211100,
                                                                    account_type=None,
                                                                    line_number=line_filtered[2],
                                                                    description=line_filtered[3],
                                                                    credit=credit,
                                                                    debit=debit,
                                                                    interest=None,
                                                                    advance=None,
                                                                    reimbursement=None,
                                                                    balance=None,
                                                                    destination_account=line_filtered[6],
                                                                    statement=None,
                                                                    ratio_code=line[5],
                                                                    )
                            else:
                                newline1 = objects.StatementLine.create_line(date=datetime_object,
                                                                    account_number=211100,
                                                                    account_type=None,
                                                                    line_number=line_filtered[2],
                                                                    description=line_filtered[3],
                                                                    credit=credit,
                                                                    debit=debit,
                                                                    interest=None,
                                                                    advance=None,
                                                                    reimbursement=None,
                                                                    balance=None,
                                                                    destination_account=None,
                                                                    statement=None,
                                                                    ratio_code=None,
                                                                    )
             
                            
                            # newline1.statement = bill
                            line_added += 1
                            newline1.save()

                            # bill.save()

        #bill.date = min(transaction.date for transaction in bill.transactions)
        #bill.stop_date = max(transaction.date for transaction in bill.transactions)
        #bill.save()
        print('Added %s new statement_line from this report on %s total lines.' %(line_added, total_line))

        # return bill




    def check_unreconciled_entries(date_from=None, date_to=None):
        if date_from == None:
            date_from = datetime.date(year=2019, month=1, day=1)
        if date_to == None:
            date_to = datetime.date(year=2030, month=1, day=1)

        journal_entry_filtered = list(objects.JournalEntry.objects(date__gte=date_from, date__lte=date_to, ))

        print('')
        print('Unreconciled Entries Report')
        print('')
        print(date_from, date_to)
        print('')

        total_entries = 0
        entries_found = 0

        for journal_entry in journal_entry_filtered:
            total_entries += 1

            total = helpers.evaluate_journal_entry_value(journal_entry)
            # print(total)
            if total == 0:
                continue

            else:
                print('')
                print(journal_entry.statement_line)
                print(journal_entry)
                entries_found += 1
                for transaction in journal_entry.transactions:
                    print(transaction)

        print('')
        print('Found %s unreconciled entries out of %s entries evaluated.' %(entries_found, total_entries))

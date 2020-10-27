import objects
import unittest





class StatementFunction():
	"""docstring for Statement"""
	def __init__(self, arg):
		super(Statement, self).__init__()
		self.arg = arg

	def import_statemet_line(filename, ):

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


		
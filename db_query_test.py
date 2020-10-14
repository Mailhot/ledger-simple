import mongoengine
from datetime import datetime
from bson import ObjectId
import objects


mongoengine.connect('ledger-simple')

open_transaction = list(objects.Transaction.objects().aggregate({"$match": {"total":{"$eq": 225}, "account_number":{"$ne": objects.Account.get_account(account_number=statement_line.account_number, account_type=statement_line.account_type).id, "$in": [account.id for account in list(Account.objects(reconciled=True))]}, "date":{"$eq": statement_line.date}}}))

for transaction in open_transaction:
	print(open_transaction)
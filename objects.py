
from mongoengine import *
from datetime import datetime
from bson import ObjectId

default_currency = "CAD"

# Connect the DB, just need to install mongoDB, might need to create the DB?
connect('ledger-simple')


class Account(Document):
	"""docstring for Document."""
	parent = ReferenceField("self", default=None)
	child = ReferenceField("self", default=None)
	description = StringField(max_length=200, required=True)


class Transaction(Document):
	"""docstring for ClassName"""
	account_to = ReferenceField("Account", required=True)
	account_from = ReferenceField("Account", required=True)
	amount = FloatField(default=1)
	currency = StringField(max_length=3, default="CAD")
	currency_rate = FloatField(default=1)
	date = DateTimeField(default=datetime.now())


def add_transaction(account_to, account_from, amount, currency=default_currency, date=datetime.now()):
	# keep on
	new_transaction = Transaction(account_to=account_to, 
								account_from=account_from,
								amount=amount,
								currency=currency,
								date=date)
	new_transaction.save()

	print("New transaction saved : ", transaction.id)

	return new_transaction

def get_exchange_rate():
	# Keep on


	

		
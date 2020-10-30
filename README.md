# ledger-simple
Simple python3 based ledger program

This program / script is used to split expence between 2 entities.

The inputs are statement from credit cards or accounts, a chart of accounts, and 2 users.

The outputs are ledger reports of cash movement based on ratios of each users. (each account has got a ratio set)
A balance can be shown of the amount owed between users.

It uses python with a terminal interface (script only) and mongoengine with mongodb as a database.

Note: All transaction should appear on only 1 statement, if you change the line number, the system will threat it as a different line. We could remove this, but it would on the other hand threat different line (different line number) with same description and same amount (credit and debit) same date and same balance as being the same statement line, and this happen on 20th febuary, 2020, two transaction to the same account on same day that resulted in same balance would be threated as same transaction.

Working Principle

First we take the statement to be imported (account statement are to be .csv without accented character)
credit card statement are to be .txt files without accented character.

Upon import, we take each line of statement and create a statement line with all values inside it. (columns should match the program, so you will need to adapt to your statement)

Then we take the statement line and create a journal entry for each statement line. The journal entry holds transactions and a reference to the statement line. In the statement (.txt or .csv) the last column is a value for account number in the chart of account. So each journal entry will end up having a source account (from the statement it comes from) and a destination account (last column of the statement "account number").

If the destination account is not reconciled, it will create 2 transaction for each statement line. The reference of the 2nd transaction will be none.

If the destination account is reconciled, it will create 1 transaction and try to find another in the existing transaction that match the date and amount within the reconciled accounts and excluding itself. If it does it will add the existing transaction to the journal entry. If not it will leave the journal entry with only 1 transaction until it finds another one to match it. 

The output shows a report of expense grouped by account, with amounts per user. 

The userbalance show what is the amount owed between user, it shows all transaction that generates imbalance (money flowing from account with different ratios)

This is still a work in progress although i think the basic works.
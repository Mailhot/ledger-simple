import function
import objects
import unittest
from mongoengine import connect, disconnect


class TestStatementFunction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # disconnect()
        objects.StatementLine.drop_collection()
        objects.Counters.drop_collection()
        objects.Account.drop_collection()
        objects.User.drop_collection()

        objects.init_counters()
        user1 = objects.User.add_user('user1')
        user2 = objects.User.add_user('user2')
        objects.Account.import_accounts_from_file(filename='./test/test_ChartofAccounts.csv')



        connect('test')

    @classmethod
    def tearDownClass(cls):
        # db = _get_db()
        # print(type(dbtest))
        # db.dropDatabase()('test')
        objects.StatementLine.drop_collection()
        objects.Counters.drop_collection()
        objects.Account.drop_collection()



        disconnect()

    def test_import_file(self):
        """This function import a file and split it into list of lines"""

        lines = function.StatementFunction.import_file('./test/test_releve.csv')

        
        expected_result = ['Levis(Quebec)', '716528', 'PCA', "2020/01/31", '00003', 'Service charges', '', '1.50', '', '', '', '', '', '328.50', '513005']
        
        self.assertEqual(lines[74], expected_result, 'should be %s' %expected_result)

    def test_import_statemet_line(self):
        """ Import statement line regardless of files we imported it from."""
        lgts = []
        line = ['Levis(Quebec)', '716528', 'PCA', "2020/01/31", '00003', 'Service charges', '', '1.50', '', '', '', '', '', '328.50', '513005']
        lgts.append(len(objects.StatementLine.objects()))
        function.StatementFunction.import_statemet_line([line])
        lgts.append(len(objects.StatementLine.objects()))
        expected_result = 1
        self.assertEqual(lgts[1]-lgts[0], expected_result, 'should be %s' %expected_result)
        
        # Try to import it again, it should not import it as it already exist.
        lgts = []
        lgts.append(len(objects.StatementLine.objects()))
        function.StatementFunction.import_statemet_line([line])
        lgts.append(len(objects.StatementLine.objects()))
        expected_result = 1
        self.assertEqual(lgts[1]-lgts[0], expected_result, 'should be %s' %expected_result)

        
    def test_find_description_amount(self):
        """
        take the description with potentially an amount added.
        remove the amount if it has, return the original description if it had not.
        """
        test_string = 'Capital payment - Internet:1,000.00$'

        result = function.StatementFunction.find_description_amount(test_string)

        self.assertEqual(result, 'Capital payment - Internet', 'should be %s' %'Capital payment - Internet')
        


    def test_get_account_by_number(self):

        dict_values = list(objects.ACCOUNT_TYPE.values()).index('Bank and Cash')
        dict_keys = list(objects.ACCOUNT_TYPE.keys())
        test_ratio1 = 0.5
        user_ratio = {'user1id': float(test_ratio1)/100, str('user2id'): float(1-test_ratio1)/100}

        account = objects.Account.get_account_by_number(111001)

        self.assertEqual(account.number, 111001, 'should be %s' %account)
        self.assertEqual(account.description, 'User1 Personnel', 'should be %s' %account)
        self.assertEqual(account.account_number, 500001, 'should be %s' %account)
        self.assertEqual(account.account_type, 'PCA', 'should be %s' %account)

    def test_import_accounts_from_file(self):
        imported_lines = function.StatementFunction.import_file('./test/test_releve.csv', header=True)
        function.StatementFunction.import_statement_lines(imported_lines)
        self.assertEqual(len(objects.StatementLine.objects()), 72, 'should be 72 after initial import')
        function.StatementFunction.import_statement_lines(imported_lines)
        self.assertEqual(len(objects.StatementLine.objects()), 72, 'should be 72 after second import')

    def test_import_statement_lines(self):
        function.StatementFunction.process_statement_lines()
        self.assertEqual(len(objects.StatementLine.objects()), 72, 'should be 72 after initial import')

if __name__ == '__main__':

    connect('test')
    unittest.main()
import unittest


class ImportPackageTestCase(unittest.TestCase):

    def test_import(self):
        import import_package
        expected = 5
        self.assertEqual(expected, import_package.add(2, 3))


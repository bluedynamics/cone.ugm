import sys
import unittest


def test_suite():
    from cone.ugm.tests import test_layout

    from cone.ugm.tests import test_model_group
    from cone.ugm.tests import test_model_groups
    from cone.ugm.tests import test_model_localmanager
    from cone.ugm.tests import test_model_settings

    suite = unittest.TestSuite()

    suite.addTest(unittest.findTestCases(test_layout))

    suite.addTest(unittest.findTestCases(test_model_group))
    suite.addTest(unittest.findTestCases(test_model_groups))
    suite.addTest(unittest.findTestCases(test_model_localmanager))
    suite.addTest(unittest.findTestCases(test_model_settings))

    return suite


def run_tests():
    from zope.testrunner.runner import Runner

    runner = Runner(found_suites=[test_suite()])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()

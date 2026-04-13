import sys
import unittest


TEST_MODULES = [
    "tests.test_auth_login",
    "tests.test_auth_google",
    "tests.test_study_init",
    "tests.test_study_evaluate",
    "tests.test_study_content_viewed",
    "tests.test_study_complete_lesson",
]


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for module_name in TEST_MODULES:
        suite.addTests(loader.loadTestsFromName(module_name))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()

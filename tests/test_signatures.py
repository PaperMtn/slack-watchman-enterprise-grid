import os
import unittest
from pathlib import Path

from src.slack_watchman_eg import signature

SIGNATURES_PATH = (Path(__file__).parents[1] / 'signatures').resolve()


def assert_empty(obj):
    if obj[0] is None:
        return True
    else:
        return False


def assert_not_empty(obj):
    if obj[0] is None:
        return False
    else:
        return True


def load_signatures_slack() -> list:
    """Load signatures from YAML files
    Returns:
        List containing loaded definitions as Signatures objects
    """

    loaded_signatures = []
    try:
        for root, dirs, files in os.walk(SIGNATURES_PATH):
            for sig_file in files:
                sig_path = (Path(root) / sig_file).resolve()
                if sig_path.name.endswith('.yaml'):
                    loaded_def = signature.load_from_yaml(sig_path)
                    for sig in loaded_def:
                        if sig.status == 'enabled' and 'slack_std' in sig.watchman_apps:
                            loaded_signatures.append(sig)
        return loaded_signatures
    except Exception as e:
        raise e


class TestSigs(unittest.TestCase):
    def test_signatures_format_slack(self):
        """Check signatures are properly formed YAML ready to be ingested for Slack Watchman"""

        try:
            load_signatures_slack()
        except AttributeError:
            self.assertTrue(False)

    def test_search_strings_format(self):
        print('Testing search string format')
        signatures = load_signatures_slack()

        for sig in signatures:
            if 'slack' in sig.watchman_apps:
                assert isinstance(sig.search_strings, list), f'Signature {sig.name} has' \
                                                             f' incorrectly formatted Slack search strings'

    def test_search_strings_content(self):
        print('Testing search strings content')
        signatures = load_signatures_slack()

        for sig in signatures:
            if 'slack' in sig.watchman_apps:
                self.assertTrue(assert_not_empty(sig.search_strings), f'Signature {sig.name} has no search strings.'
                                                                      f' There must be at least one to be used with Slack Watchman')

    def test_scope_format(self):
        print('Testing scope options')
        signatures = load_signatures_slack()

        for sig in signatures:
            if 'slack' in sig.watchman_apps:
                assert isinstance(sig.scope, list), f'Signature {sig.name} has' \
                                                    f' incorrectly formatted Slack Watchman scopes'

    def test_scope_content(self):
        print('Testing scope content')
        signatures = load_signatures_slack()

        for sig in signatures:
            if 'slack' in sig.watchman_apps:
                self.assertTrue(assert_not_empty(sig.scope), f'Signature {sig.name} has no scopes.'
                                                             f' There must be at least one to be used with Slack '
                                                             f'Watchman')


if __name__ == '__main__':
    unittest.main()

# def load_signatures() -> list:
#     """Load signatures from YAML files
#     Returns:
#         List containing loaded definitions as Signatures objects
#     """
#
#     loaded_signatures = []
#     try:
#         for root, dirs, files in os.walk(SIGNATURES_PATH):
#             for sig_file in files:
#                 sig_path = (Path(root) / sig_file).resolve()
#                 if sig_path.name.endswith('.yaml'):
#                     loaded_def = signature.load_from_yaml(sig_path)
#                     for sig in loaded_def:
#                         if sig.status == 'enabled' and 'slack_eg' in sig.watchman_apps:
#                             loaded_signatures.append(sig)
#         return loaded_signatures
#     except Exception as e:
#         raise e
#
#
# def check_yaml(sig):
#     try:
#         yaml_sig = yaml.safe_load(sig)
#     except:
#         return False
#     return True
#
#
# class TestSigs(unittest.TestCase):
#     def test_signatures_format(self):
#         """Check signatures are properly formed YAML ready to be ingested"""
#
#         for root, dirs, files in os.walk(SIGNATURES_PATH):
#             for sig_file in files:
#                 sig_path = (Path(root) / sig_file).resolve()
#                 if sig_path.name.endswith('.yaml'):
#                     with open(sig_path) as yaml_file:
#                         self.assertTrue(check_yaml(yaml_file.read()), msg=f'Malformed YAML: {yaml_file.name}')
#
#     def test_signature_matching_cases(self):
#         """Test that the match case strings match the regex. Skip if the match case is 'blank'"""
#
#         sig_list = load_signatures()
#         for signature in sig_list:
#             for test_case in signature.test_cases.match_cases:
#                 if not test_case == 'blank':
#                     self.assertRegex(test_case, signature.pattern, msg='Regex does not detect given match case')
#
#     def test_signature_failing_cases(self):
#         """Test that the fail case strings don't match the regex. Skip if the fail case is 'blank'"""
#
#         sig_list = load_signatures()
#         for signature in sig_list:
#             if signature.test_cases.fail_cases:
#                 for test_case in signature.test_cases.fail_cases:
#                     if not test_case == 'blank':
#                         self.assertNotRegex(test_case, signature.pattern,
#                                             msg='Regex does detect given failure case, it should '
#                                                 'not')
#
#
# if __name__ == '__main__':
#     unittest.main()

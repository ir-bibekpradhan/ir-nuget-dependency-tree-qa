import unittest
import json
from collector_fixtures import transport_envelope
from context_rules import check_context_rules


class CollectorFixtureTests(unittest.TestCase):
    def test_tabs_cr_quotes_and_unicode_survive_json(self):
        raw = 'restore\toutput\rline\r\n"quoted" \\path ✓'
        encoded = transport_envelope(raw, {'targets': []})
        self.assertEqual(json.loads(encoded)['restoreOutput'], raw)
        self.assertNotIn('\t', encoded)
        self.assertNotIn('\r', encoded)

    def test_same_parent_must_keep_each_projects_child(self):
        def graph(project, child):
            return {'targets': [{'roots': [project], 'framework': 'net8.0', 'edges': [
                {'from': 'JwtBearer@8.0.22', 'to': 'OpenIdConnect@' + child}]}]}
        rules = {'edges': [
            {'project': 'Storefront', 'framework': 'net8.0', 'from': 'JwtBearer@8.0.22', 'to': 'OpenIdConnect@8.22.0'},
            {'project': 'Shared.Identity', 'framework': 'net8.0', 'from': 'JwtBearer@8.0.22', 'to': 'OpenIdConnect@7.1.2'}]}
        self.assertFalse(check_context_rules([graph('Storefront', '8.22.0'), graph('Shared.Identity', '7.1.2')], rules))
        self.assertTrue(check_context_rules([graph('Storefront', '7.1.2'), graph('Shared.Identity', '7.1.2')], rules))

    def test_missing_framework_branch_fails(self):
        rules = {'edges': [{'project': 'Storefront', 'framework': 'net9.0', 'from': 'JwtBearer@9.0.9', 'to': 'OpenIdConnect@8.14.0'}]}
        self.assertTrue(check_context_rules([], rules))


if __name__ == '__main__':
    unittest.main()

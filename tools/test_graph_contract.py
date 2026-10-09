import copy
import unittest
from graph_contract import compare, load_json, normalize_version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GraphContractTests(unittest.TestCase):
    def setUp(self):
        self.graph = load_json(ROOT / 'scenarios/04-shared-dependency/expected/graph.json')

    def test_shared_paths_are_required(self):
        actual = copy.deepcopy(self.graph)
        paths = actual['targets'][0]['paths']
        shared = next(key for key, values in paths.items() if len(values) > 1)
        paths[shared].pop()
        self.assertFalse(compare(self.graph, actual)[0])

    def test_duplicate_component_is_rejected(self):
        actual = copy.deepcopy(self.graph)
        actual['targets'][0]['nodes'].append(actual['targets'][0]['nodes'][-1])
        self.assertFalse(compare(self.graph, actual)[0])

    def test_extra_edge_is_rejected(self):
        actual = copy.deepcopy(self.graph)
        actual['targets'][0]['edges'].append({'from': 'fake', 'to': 'missing'})
        self.assertFalse(compare(self.graph, actual)[0])

    def test_wrong_version_is_rejected(self):
        actual = copy.deepcopy(self.graph)
        actual['targets'][0]['nodes'][-1]['id'] += '-wrong'
        self.assertFalse(compare(self.graph, actual)[0])

    def test_missing_evidence_is_rejected(self):
        self.assertFalse(compare(self.graph, {'targets': []})[0])

    def test_casing_and_version_normalization(self):
        actual = copy.deepcopy(self.graph)
        for target in actual['targets']:
            for node in target['nodes']:
                node['id'] = node['id'].upper()
            for edge in target['edges']:
                edge['from'] = edge['from'].upper()
                edge['to'] = edge['to'].upper()
            target['roots'] = [root.upper() for root in target['roots']]
            target['paths'] = {key.upper(): [[part.upper() for part in path] for path in values]
                               for key, values in target['paths'].items()}
        self.assertTrue(compare(self.graph, actual)[0])
        self.assertEqual(normalize_version('01.2.3.0+build'), '1.2.3')

    def test_legacy_framework_and_rid_lock_delta(self):
        from graph_contract import split_target, _target_lock
        self.assertEqual(split_target('.NETStandard,Version=v2.0'), ('netstandard2.0', None))
        lock = {'dependencies': {'net8.0': {'Parent': {'type': 'Direct'}},
                                 'net8.0/win-x64': {'Native': {'type': 'Transitive'}}}}
        self.assertEqual(set(_target_lock(lock, 'net8.0/win-x64')), {'Parent', 'Native'})


if __name__ == '__main__':
    unittest.main()

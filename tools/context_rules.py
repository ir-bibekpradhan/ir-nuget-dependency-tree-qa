from graph_contract import _ref_key, split_target


def check_context_rules(graphs, rules):
    indexed = {}
    for graph in graphs:
        for target in graph['targets']:
            for project in target['roots']:
                key = (project.lower(), split_target(target['framework'])[0])
                indexed[key] = {(_ref_key(edge['from']), _ref_key(edge['to'])) for edge in target['edges']}
    errors = []
    for rule in rules['edges']:
        key = (rule['project'].lower(), rule['framework'])
        edge = (_ref_key(rule['from']), _ref_key(rule['to']))
        if edge not in indexed.get(key, set()):
            errors.append(f'{key}: missing contextual edge {edge}')
    return errors

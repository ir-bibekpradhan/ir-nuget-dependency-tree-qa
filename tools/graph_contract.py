#!/usr/bin/env python3
import json
import re
from collections import Counter
from pathlib import Path


def normalize_version(value):
    value = str(value).split("+", 1)[0]
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(.*)$", value)
    if not match:
        return value.lower()
    major, minor, patch, suffix = match.groups()
    if suffix == '.0':
        suffix = ''
    return f"{int(major)}.{int(minor or '0')}.{int(patch or '0')}{suffix}".lower()


def split_key(key):
    package_id, version = key.rsplit("/", 1)
    return package_id, version


def split_target(value):
    parts = value.split("/", 1)
    framework = parts[0]
    match = re.fullmatch(r"\.(NETStandard|NETCoreApp|NETFramework),Version=v([\d.]+)", framework, re.I)
    if match:
        family, version = match.groups()
        framework = ('netstandard' + version if family.lower() == 'netstandard'
                     else 'net' + (version.replace('.', '') if family.lower() == 'netframework' else version))
    return framework, parts[1] if len(parts) == 2 else None


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _target_lock(lock, target_name):
    dependencies = lock.get("dependencies", {})
    framework, rid = split_target(target_name)
    merged = {}
    for name, entries in dependencies.items():
        if split_target(name) == (framework, None):
            merged.update(entries)
    if rid:
        for name, entries in dependencies.items():
            if split_target(name) == (framework, rid):
                merged.update(entries)
    return merged


def build_graph(assets, lock, scenario_id):
    root = assets["project"]["restore"]["projectName"]
    graph = {"schemaVersion": 1, "scenario": scenario_id, "targets": [], "vulnerabilities": []}

    for target_name, target in assets["targets"].items():
        framework, rid = split_target(target_name)
        lock_entries = _target_lock(lock, target_name)
        by_id = {}
        nodes = [{"id": root, "type": "project"}]

        for key, value in target.items():
            item_id, version = split_key(key)
            node_type = value.get("type", "package")
            lock_entry = next((entry for name, entry in lock_entries.items()
                               if name.lower() == item_id.lower()), {})
            direct = node_type == "package" and lock_entry.get("type", "").lower() == "direct"
            ref = f"{item_id}@{version}" if node_type == "package" else item_id
            by_id[item_id.lower()] = {"ref": ref, "id": item_id, "version": version,
                                      "type": node_type, "value": value, "lock": lock_entry}
            node = {"id": ref, "type": node_type}
            if node_type == "package":
                node["direct"] = direct
            nodes.append(node)

        edges = []
        for item in by_id.values():
            lock_type = item["lock"].get("type", "").lower()
            if lock_type in {"direct", "project"}:
                edges.append({
                    "from": root,
                    "to": item["ref"],
                    "requested": item["lock"].get("requested"),
                })

            for child_id, requested in item["value"].get("dependencies", {}).items():
                child = by_id.get(child_id.lower())
                if child:
                    edges.append({"from": item["ref"], "to": child["ref"], "requested": requested})

        adjacency = {}
        for edge in edges:
            adjacency.setdefault(edge["from"], []).append(edge["to"])

        paths = {}
        def walk(node, path, seen):
            if node in seen:
                return
            next_path = path + [node]
            if node != root:
                paths.setdefault(node, []).append(path)
            for child in adjacency.get(node, []):
                walk(child, next_path, seen | {node})
        walk(root, [], set())

        for key in paths:
            paths[key] = sorted(paths[key])

        graph["targets"].append({
            "framework": framework,
            "rid": rid,
            "roots": [root],
            "nodes": sorted(nodes, key=lambda item: (item["type"], item["id"].lower())),
            "edges": sorted(edges, key=lambda item: (item["from"].lower(), item["to"].lower(), str(item.get("requested")))),
            "paths": dict(sorted(paths.items())),
        })

    graph["targets"].sort(key=lambda item: (item["framework"], item["rid"] or ""))
    return graph


def _node_key(node):
    if node["type"] == "package":
        package_id, version = node["id"].rsplit("@", 1)
        return ("package", package_id.lower(), normalize_version(version), bool(node.get("direct")))
    return (node["type"], node["id"].lower())


def _ref_key(value):
    if "@" in value:
        package_id, version = value.rsplit("@", 1)
        return f"{package_id.lower()}@{normalize_version(version)}"
    return value.lower()


def canonical(graph):
    result = {}
    for target in graph.get("targets", []):
        key = (target["framework"].lower(), (target.get("rid") or "").lower())
        nodes = {_node_key(node) for node in target.get("nodes", [])}
        edges = {
            (_ref_key(edge["from"]), _ref_key(edge["to"]), edge.get("requested"))
            for edge in target.get("edges", [])
        }
        paths = {
            (_ref_key(destination), tuple(_ref_key(part) for part in path))
            for destination, values in target.get("paths", {}).items()
            for path in values
        }
        result[key] = {"nodes": nodes, "edges": edges, "paths": paths,
                       "roots": {_ref_key(root) for root in target.get('roots', [])}}
    return result


def structural_errors(graph):
    errors = []
    target_keys = []
    for target in graph.get('targets', []):
        key = (target['framework'].lower(), (target.get('rid') or '').lower())
        target_keys.append(key)
        nodes = [_ref_key(node['id']) for node in target.get('nodes', [])]
        edges = [(_ref_key(edge['from']), _ref_key(edge['to'])) for edge in target.get('edges', [])]
        paths = [(_ref_key(destination), tuple(_ref_key(part) for part in path))
                 for destination, values in target.get('paths', {}).items() for path in values]
        for label, values in [('node', nodes), ('edge', edges), ('path', paths)]:
            for value, count in Counter(values).items():
                if count > 1:
                    errors.append(f'{key}: duplicate {label} {value}')
        refs = set(nodes)
        for root in target.get('roots', []):
            if _ref_key(root) not in refs:
                errors.append(f'{key}: absent root {root}')
        for parent, child in edges:
            if parent not in refs or child not in refs:
                errors.append(f'{key}: dangling edge {parent} -> {child}')
    for key, count in Counter(target_keys).items():
        if count > 1:
            errors.append(f'duplicate target {key}')
    if not target_keys:
        errors.append('no target graphs')
    return errors


def compare(expected, actual, compare_requested=True):
    left = canonical(expected)
    right = canonical(actual)
    diff = {"missingTargets": [], "extraTargets": [], "targets": {},
            "expectedStructureErrors": structural_errors(expected),
            "actualStructureErrors": structural_errors(actual)}

    diff["missingTargets"] = sorted([list(key) for key in left.keys() - right.keys()])
    diff["extraTargets"] = sorted([list(key) for key in right.keys() - left.keys()])
    for key in sorted(left.keys() & right.keys()):
        expected_edges = left[key]["edges"]
        actual_edges = right[key]["edges"]
        if not compare_requested:
            expected_edges = {(a, b) for a, b, _ in expected_edges}
            actual_edges = {(a, b) for a, b, _ in actual_edges}
        target_diff = {
            "missingRoots": sorted(left[key]['roots'] - right[key]['roots']),
            "extraRoots": sorted(right[key]['roots'] - left[key]['roots']),
            "missingNodes": sorted(map(str, left[key]["nodes"] - right[key]["nodes"])),
            "extraNodes": sorted(map(str, right[key]["nodes"] - left[key]["nodes"])),
            "missingEdges": sorted(map(str, expected_edges - actual_edges)),
            "extraEdges": sorted(map(str, actual_edges - expected_edges)),
            "missingPaths": sorted(map(str, left[key]["paths"] - right[key]["paths"])),
            "extraPaths": sorted(map(str, right[key]["paths"] - left[key]["paths"])),
        }
        if any(target_diff.values()):
            diff["targets"]["/".join(filter(None, key))] = target_diff

    passed = not any(diff.values())
    return passed, diff

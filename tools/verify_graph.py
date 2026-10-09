#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def fail(message):
    raise AssertionError(message)


assets_path = Path(sys.argv[1])
expected_path = Path(sys.argv[2])
assets = json.loads(assets_path.read_text(encoding="utf-8"))
expected = json.loads(expected_path.read_text(encoding="utf-8"))
actual_export = {"scenario": expected_path.parent.name, "targets": {}}

for target_pattern, rules in expected.get("targets", {}).items():
    matching = [(name, value) for name, value in assets["targets"].items()
                if name.lower() == target_pattern.lower()]
    if not matching:
        fail(f"Missing target {target_pattern}; available={list(assets['targets'])}")

    target_name, target = matching[0]
    packages = {}
    all_nodes = {}
    for key, value in target.items():
        package_id, version = key.rsplit("/", 1)
        all_nodes[package_id.lower()] = (package_id, version, value)
        if value.get("type") == "package":
            packages[package_id.lower()] = (package_id, version, value)

    framework_name = target_name.split("/", 1)[0]
    frameworks = assets["project"]["frameworks"]
    framework = next((value for name, value in frameworks.items()
                      if name.lower() == framework_name.lower()), None)
    if framework is None:
        fail(f"Missing project framework metadata for {framework_name}")
    direct = {name.lower() for name in framework.get("dependencies", {})}

    for package_id, spec in rules.get("packages", {}).items():
        node = packages.get(package_id.lower())
        if node is None:
            fail(f"{target_name}: missing package {package_id}")
        _, version, _ = node
        if "version" in spec and version != spec["version"]:
            fail(f"{target_name}: expected {package_id}/{spec['version']}, found {version}")
        if "versionPrefix" in spec and not version.startswith(spec["versionPrefix"]):
            fail(f"{target_name}: expected {package_id} version prefix {spec['versionPrefix']}, found {version}")
        if "direct" in spec and (package_id.lower() in direct) != spec["direct"]:
            fail(f"{target_name}: incorrect direct/transitive classification for {package_id}")

    edges = set()
    for child in direct:
        if child in all_nodes:
            edges.add(("$root", child))
    for parent_id, (_, _, node) in all_nodes.items():
        for child_id in node.get("dependencies", {}):
            if child_id.lower() in all_nodes:
                edges.add((parent_id, child_id.lower()))

    for parent, child in rules.get("edges", []):
        normalized = (parent.lower() if parent != "$root" else "$root", child.lower())
        if normalized not in edges:
            fail(f"{target_name}: missing edge {parent} -> {child}")

    incoming = {}
    for parent, child in edges:
        incoming.setdefault(child, set()).add(parent)
    for package_id, count in rules.get("incoming", {}).items():
        actual = len(incoming.get(package_id.lower(), set()))
        if actual != count:
            fail(f"{target_name}: expected {count} incoming paths for {package_id}, found {actual}")

    minimum = rules.get("minPackages", 0)
    if len(packages) < minimum:
        fail(f"{target_name}: expected at least {minimum} packages, found {len(packages)}")

    if rules.get("anyShared") and not any(len(parents) > 1 for parents in incoming.values()):
        fail(f"{target_name}: expected at least one shared dependency")

    def depth(node, seen):
        if node in seen:
            return 0
        children = [child for parent, child in edges if parent == node]
        return 0 if not children else 1 + max(depth(child, seen | {node}) for child in children)

    actual_depth = depth("$root", set())
    if actual_depth < rules.get("minDepth", 0):
        fail(f"{target_name}: expected depth >= {rules['minDepth']}, found {actual_depth}")

    actual_export["targets"][target_name] = {
        "packages": sorted(f"{name}/{version}" for name, version, _ in packages.values()),
        "edges": sorted([parent, child] for parent, child in edges),
        "depth": actual_depth,
    }

(expected_path.parent / "actual-graph.json").write_text(
    json.dumps(actual_export, indent=2) + "\n", encoding="utf-8"
)
print(f"Verified {expected_path.parent.name}: {', '.join(actual_export['targets'])}")

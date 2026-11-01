"""Reading a plugin's `plugman = dict(...)` block without importing it.

Shared by auto_apply_plugin_metadata.py (which turns the whole block into a
catalog entry) and auto_apply_version_metadata.py (which only needs
min_engine_build when it stamps a version). Plugins are parsed with `ast`,
never imported or executed.

ci-apply.yml checks out this file next to auto_apply_version_metadata.py
from main (its trusted sparse checkout); keep both listed there.
"""

import ast
import copy


def resolve_literal(node, constants, where):
    """ast.literal_eval, widened to module-level constants and indexing into them.

    Plugins commonly keep a `__version__` / `__author__` dunder next to the code
    that uses them and want the plugman dict to reference those rather than
    repeat the values. Nothing here imports or executes the plugin, so only
    names this module already resolved to a literal are available, and only
    indexing (not attribute access or calls) is applied to them.
    """
    if isinstance(node, ast.Name):
        if node.id not in constants:
            raise ValueError(
                f"{where}: {node.id} is not a module-level constant defined above "
                "plugman. Only names assigned a literal earlier in the file can be "
                "referenced, because the plugin is parsed, never imported."
            )
        # Copied so an entry like authors=__author__ cannot be mutated later
        # through the constants table.
        return copy.deepcopy(constants[node.id])

    if isinstance(node, ast.Subscript):
        container = resolve_literal(node.value, constants, where)
        index = resolve_literal(node.slice, constants, where)
        try:
            return container[index]
        except (TypeError, KeyError, IndexError) as err:
            raise ValueError(
                f"{where}: cannot index {container!r} with {index!r}: {err}"
            ) from None

    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        items = [resolve_literal(item, constants, where) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(items)
        if isinstance(node, ast.Set):
            return set(items)
        return items

    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise ValueError(f"{where}: ** unpacking inside plugman is not supported.")
        return {
            resolve_literal(key, constants, where): resolve_literal(value, constants, where)
            for key, value in zip(node.keys, node.values)
        }

    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        raise ValueError(
            f"{where}: unsupported expression `{ast.unparse(node)}`. plugman values must "
            "be literals, or module-level constants (optionally indexed, e.g. "
            "__author__[0]). Method calls such as __file__.split('/') are not evaluated."
        ) from None


def collect_module_constants(tree, stop_at):
    """Module-level names bound to a literal, in the statements before `stop_at`.

    Order matters: a name assigned *after* plugman would raise NameError when the
    game imports the plugin, so it must not resolve here either.
    """
    constants = {}
    # The module docstring, so a plugin can write description=__doc__ instead of
    # repeating it. Line breaks are kept as written; clean=True strips the
    # indentation and the blank first/last lines that triple quotes bring along.
    docstring = ast.get_docstring(tree, clean=True)
    if docstring is not None:
        constants["__doc__"] = "\n".join(line.rstrip() for line in docstring.splitlines())
    for node in tree.body:
        if node is stop_at:
            break
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        else:
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                constants[target.id] = value
    return constants


def find_plugman_assignment(tree):
    """The module-level `plugman = dict(...)` statement, or None."""
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "plugman"
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "dict"
        ):
            return node
    return None


def validate_min_engine_build(value, where):
    """Raise unless `value` is a usable min_engine_build (a build number >= 0)."""
    # bool is an int subclass; min_engine_build=True is a mistake, not 1.
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(
            f"{where}: min_engine_build must be a non-negative integer engine build "
            f"number (babase.app.env.engine_build_number), got {value!r}."
        )
    return value


def get_plugin_min_engine_build(source, where):
    """A plugin's plugman min_engine_build, or 0 when it doesn't set one.

    0 also covers plugins with no plugman block at all (most of the
    catalog predates it); catalog entries treat a missing min_engine_build
    as 0 the same way, so neither side has to spell it out.
    """
    if b"min_engine_build" not in source:
        # Cheap fast path: the test suite calls this for every published
        # version of every plugin.
        return 0
    tree = ast.parse(source)
    node = find_plugman_assignment(tree)
    if node is None:
        return 0
    for keyword in node.value.keywords:
        if keyword.arg == "min_engine_build":
            constants = collect_module_constants(tree, stop_at=node)
            value = resolve_literal(keyword.value, constants, f"{where}: plugman")
            return validate_min_engine_build(value, f"{where}: plugman")
    return 0

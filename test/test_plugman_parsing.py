"""Unit tests for test/auto_apply_plugin_metadata.py.

test_checks.py validates the manifests that the pipeline has already produced.
These tests cover the step before that: turning a plugin's `plugman = dict(...)`
block into the metadata written to plugins/<category>.json, including the cases
that must be rejected rather than silently skipped.

Run from the repo root with the rest of the suite:

    python -m unittest discover -v
    python -m unittest test.test_plugman_parsing -v
"""

import ast
import contextlib
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

# auto_apply_plugin_metadata.py is a CI script rather than a package module: it
# imports its siblings by bare name (`from auto_apply_version_metadata import
# ...`), so its own directory must be importable.
TEST_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import auto_apply_plugin_metadata as apm  # noqa: E402  (needs the path above)
import plugman_parsing as pp  # noqa: E402


def plugman_node(source):
    """Return (plugman assign node, module tree) for a snippet of plugin source."""
    tree = ast.parse(source)
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "plugman"
        ):
            return node, tree
    raise AssertionError("test snippet has no module-level plugman assignment")


def build(source, stem="sample_plugin"):
    """Run build_plugman_info() over a snippet, as extract_plugman() would."""
    node, tree = plugman_node(source)
    return apm.build_plugman_info(node, tree, f"plugins/utilities/{stem}.py", stem)


def resolve(expression, constants=None):
    return apm.resolve_literal(ast.parse(expression, mode="eval").body,
                               constants or {}, "snippet")


# The keys every plugman dict needs, so each test only spells out what it is about.
COMMON_KEYS = (
    '    description="A test plugin.",\n'
    '    external_url="https://example.invalid/",\n'
    '    authors=[{"name": "n", "email": "", "discord": ""}],\n'
)


class TestCollectModuleConstants(unittest.TestCase):
    def constants(self, source):
        node, tree = plugman_node(source)
        return apm.collect_module_constants(tree, stop_at=node)

    def test_literal_above_plugman_is_collected(self):
        constants = self.constants('__version__ = "1.0.0"\nplugman = dict()\n')
        self.assertEqual(constants["__version__"], "1.0.0")

    def test_assignment_below_plugman_is_ignored(self):
        # It would raise NameError when the game imports the plugin, so it must
        # not resolve here either.
        constants = self.constants('plugman = dict()\n__version__ = "1.0.0"\n')
        self.assertNotIn("__version__", constants)

    def test_non_literal_assignment_is_skipped(self):
        constants = self.constants(
            "import os\nCWD = os.getcwd()\nCOUNT = 2\nplugman = dict()\n"
        )
        self.assertNotIn("CWD", constants)
        self.assertEqual(constants["COUNT"], 2)

    def test_annotated_assignment_is_collected(self):
        constants = self.constants('__version__: str = "2.0.0"\nplugman = dict()\n')
        self.assertEqual(constants["__version__"], "2.0.0")

    def test_last_assignment_wins(self):
        constants = self.constants('V = "1"\nV = "2"\nplugman = dict()\n')
        self.assertEqual(constants["V"], "2")

    def test_assignment_inside_a_function_is_not_module_level(self):
        constants = self.constants('def f():\n    HIDDEN = "x"\nplugman = dict()\n')
        self.assertNotIn("HIDDEN", constants)


class TestResolveLiteral(unittest.TestCase):
    def test_plain_literals_are_unchanged(self):
        self.assertEqual(resolve('"x"'), "x")
        self.assertEqual(resolve("[1, 2]"), [1, 2])
        self.assertEqual(resolve("(1, 2)"), (1, 2))
        self.assertEqual(resolve('{"a": 1}'), {"a": 1})
        self.assertEqual(resolve("-1"), -1)
        self.assertIsNone(resolve("None"))

    def test_name_resolves_to_its_constant(self):
        self.assertEqual(resolve("__version__", {"__version__": "1.0.0"}), "1.0.0")

    def test_subscript_by_index(self):
        authors = {"__author__": ["Loup", "brostos"]}
        self.assertEqual(resolve("__author__[0]", authors), "Loup")
        self.assertEqual(resolve("__author__[-1]", authors), "brostos")

    def test_subscript_by_dict_key(self):
        self.assertEqual(resolve('META["v"]', {"META": {"v": 7}}), 7)

    def test_constants_resolve_inside_nested_containers(self):
        result = resolve('[{"name": __author__[1]}]', {"__author__": ["a", "b"]})
        self.assertEqual(result, [{"name": "b"}])

    def test_resolved_value_is_a_copy(self):
        constants = {"__author__": [{"name": "a"}]}
        result = resolve("__author__", constants)
        result[0]["name"] = "mutated"
        self.assertEqual(constants["__author__"][0]["name"], "a")

    def test_unknown_name_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a module-level constant"):
            resolve("__nope__")

    def test_method_call_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported expression"):
            resolve("__file__.split('/')[-1]", {"__file__": "a/b.py"})

    def test_dict_unpacking_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"\*\* unpacking"):
            resolve("{**EXTRA}", {"EXTRA": {"a": 1}})

    def test_bad_index_is_reported_clearly(self):
        with self.assertRaisesRegex(ValueError, "cannot index"):
            resolve("__author__[5]", {"__author__": ["only one"]})


class TestBuildPlugmanInfo(unittest.TestCase):
    def test_plugin_name_defaults_to_the_file_stem(self):
        info = build(f'plugman = dict(\n{COMMON_KEYS}    version="1.0.0",\n)\n')
        self.assertEqual(info["plugin_name"], "sample_plugin")

    def test_explicit_matching_plugin_name_is_kept(self):
        info = build(
            'plugman = dict(\n    plugin_name="sample_plugin",\n'
            f'{COMMON_KEYS}    version="1.0.0",\n)\n'
        )
        self.assertEqual(info["plugin_name"], "sample_plugin")

    def test_plugin_name_must_match_the_file_name(self):
        with self.assertRaisesRegex(ValueError, "does not match the file name"):
            build(
                'plugman = dict(\n    plugin_name="something_else",\n'
                f'{COMMON_KEYS}    version="1.0.0",\n)\n'
            )

    def test_plugin_name_must_be_snakecase(self):
        with self.assertRaisesRegex(ValueError, "snakecase"):
            build(
                'plugman = dict(\n    plugin_name="Sample_Plugin",\n'
                f'{COMMON_KEYS}    version="1.0.0",\n)\n',
                stem="Sample_Plugin",
            )

    def test_missing_required_keys_are_named(self):
        with self.assertRaisesRegex(
            ValueError, "missing required key\\(s\\) description, external_url, authors"
        ):
            build('plugman = dict(\n    version="1.0.0",\n)\n')

    def test_version_must_be_a_string(self):
        # __version__ = 1.0 is the easy mistake once the value moves to a dunder.
        with self.assertRaisesRegex(ValueError, "version must be a string"):
            build(f'__version__ = 1.0\nplugman = dict(\n{COMMON_KEYS}'
                  "    version=__version__,\n)\n")

    def test_dunders_resolve(self):
        info = build(
            '__version__ = "1.2.3"\n'
            '__author__ = ["Loup", "brostos"]\n'
            "plugman = dict(\n"
            '    description="A test plugin.",\n'
            '    external_url="https://example.invalid/",\n'
            "    authors=[\n"
            '        {"name": __author__[0], "email": "a@b.c", "discord": "loupgarou_"},\n'
            '        {"name": __author__[1], "email": "", "discord": "brostos"},\n'
            "    ],\n"
            "    version=__version__,\n"
            ")\n"
        )
        self.assertEqual(info["version"], "1.2.3")
        self.assertEqual([author["name"] for author in info["authors"]],
                         ["Loup", "brostos"])


class TestExtractPlugman(unittest.TestCase):
    """End to end over a throwaway tree, which is what CI actually invokes."""

    def setUp(self):
        cwd = os.getcwd()
        tmp = tempfile.TemporaryDirectory()
        # addCleanup rather than tearDown so the chdir is undone even if setUp
        # or a test raises; test_checks.py depends on cwd being the repo root.
        self.addCleanup(tmp.cleanup)
        self.addCleanup(os.chdir, cwd)

        root = pathlib.Path(tmp.name)
        (root / "plugins" / "utilities").mkdir(parents=True)
        os.chdir(root)
        self.write_manifest({"plugins": {}})

        # The script prints per-file progress for the CI log; keep it out of the
        # test report. Failures still surface, they are raised not printed.
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))

        # get_published_versions() shells out to `git show <ref>:<path>`. The
        # temp tree is not a repository, so every ref fails and it falls back to
        # the working tree manifest, which is what these tests seed.
        base_ref = os.environ.pop("PLUGMAN_BASE_REF", None)
        if base_ref is not None:
            self.addCleanup(os.environ.__setitem__, "PLUGMAN_BASE_REF", base_ref)

    def write_manifest(self, content):
        pathlib.Path("plugins/utilities.json").write_text(
            json.dumps(content, indent=2), encoding="utf-8")

    def manifest(self):
        return json.loads(
            pathlib.Path("plugins/utilities.json").read_text(encoding="utf-8"))

    def write_plugin(self, stem, source):
        path = f"plugins/utilities/{stem}.py"
        pathlib.Path(path).write_text(source, encoding="utf-8")
        return path

    def test_writes_a_null_placeholder_for_a_new_plugin(self):
        path = self.write_plugin(
            "sample_plugin", f'plugman = dict(\n{COMMON_KEYS}    version="1.0.0",\n)\n')
        apm.extract_plugman([path])
        entry = self.manifest()["plugins"]["sample_plugin"]
        self.assertEqual(entry["versions"], {"1.0.0": None})
        self.assertEqual(entry["description"], "A test plugin.")

    def test_dunder_metadata_end_to_end(self):
        path = self.write_plugin(
            "sample_plugin",
            '__version__ = "1.0.0"\n'
            '__author__ = ["Loup", "brostos"]\n'
            "plugman = dict(\n"
            '    description="A test plugin.",\n'
            '    external_url="https://example.invalid/",\n'
            "    authors=[\n"
            '        {"name": __author__[0], "email": "", "discord": ""},\n'
            '        {"name": __author__[1], "email": "", "discord": ""},\n'
            "    ],\n"
            "    version=__version__,\n"
            ")\n",
        )
        apm.extract_plugman([path])
        entry = self.manifest()["plugins"]["sample_plugin"]
        self.assertEqual(entry["versions"], {"1.0.0": None})
        self.assertEqual([author["name"] for author in entry["authors"]],
                         ["Loup", "brostos"])

    def test_missing_plugman_dict_raises(self):
        path = self.write_plugin("sample_plugin", "# ba_meta require api 9\nx = 1\n")
        with self.assertRaisesRegex(ValueError, "no plugman dict found"):
            apm.extract_plugman([path])
        self.assertEqual(self.manifest()["plugins"], {})

    def test_literal_dict_form_raises(self):
        path = self.write_plugin(
            "sample_plugin", 'plugman = {"plugin_name": "sample_plugin"}\n')
        with self.assertRaisesRegex(ValueError, "dict\\(\\) constructor"):
            apm.extract_plugman([path])

    def test_paths_outside_plugins_are_ignored(self):
        apm.extract_plugman(["plugin_manager.py", ".github/workflows/ci.yml",
                             "CHANGELOG.md", "index.json"])
        self.assertEqual(self.manifest()["plugins"], {})

    def test_every_changed_file_is_processed(self):
        # A `return` used to abandon the rest of the list partway through.
        paths = [
            self.write_plugin(
                stem, f'plugman = dict(\n{COMMON_KEYS}    version="1.0.0",\n)\n')
            for stem in ("plugin_one", "plugin_two")
        ]
        apm.extract_plugman(paths)
        self.assertEqual(sorted(self.manifest()["plugins"]),
                         ["plugin_one", "plugin_two"])

    def test_version_must_be_greater_than_the_published_one(self):
        self.write_manifest({
            "plugins": {
                "sample_plugin": {
                    "description": "A test plugin.",
                    "external_url": "https://example.invalid/",
                    "authors": [{"name": "n", "email": "", "discord": ""}],
                    "versions": {"1.1.0": {"md5sum": "whatever"}},
                }
            }
        })
        path = self.write_plugin(
            "sample_plugin", f'plugman = dict(\n{COMMON_KEYS}    version="1.0.0",\n)\n')
        with self.assertRaisesRegex(Exception, "cant be lower or equal"):
            apm.extract_plugman([path])

    def test_newest_version_is_listed_first(self):
        self.write_manifest({
            "plugins": {
                "sample_plugin": {
                    "description": "A test plugin.",
                    "external_url": "https://example.invalid/",
                    "authors": [{"name": "n", "email": "", "discord": ""}],
                    "versions": {"1.0.9": {"md5sum": "whatever"}},
                }
            }
        })
        path = self.write_plugin(
            "sample_plugin", f'plugman = dict(\n{COMMON_KEYS}    version="1.0.10",\n)\n')
        apm.extract_plugman([path])
        versions = self.manifest()["plugins"]["sample_plugin"]["versions"]
        self.assertEqual(list(versions), ["1.0.10", "1.0.9"])


class TestMinEngineBuild(unittest.TestCase):
    """plugman's optional min_engine_build, as validated and as stamped."""

    @staticmethod
    def source(value_line, prefix=""):
        return (f'{prefix}plugman = dict(\n{COMMON_KEYS}    version="1.0.0",\n'
                f'{value_line})\n').encode()

    def test_missing_means_zero(self):
        self.assertEqual(pp.get_plugin_min_engine_build(self.source(""), "p"), 0)

    def test_no_plugman_block_means_zero(self):
        self.assertEqual(pp.get_plugin_min_engine_build(b"x = 1\n", "p"), 0)

    def test_literal_is_read(self):
        self.assertEqual(pp.get_plugin_min_engine_build(
            self.source("    min_engine_build=23058,\n"), "p"), 23058)

    def test_constant_above_plugman_is_read(self):
        self.assertEqual(pp.get_plugin_min_engine_build(
            self.source("    min_engine_build=MIN_BUILD,\n", prefix="MIN_BUILD = 23068\n"),
            "p"), 23068)

    def test_mention_outside_plugman_is_ignored(self):
        # The fast path sees the word; the AST read must still say 0.
        src = b"# min_engine_build is not set here\n" + self.source("")
        self.assertEqual(pp.get_plugin_min_engine_build(src, "p"), 0)

    def test_non_integers_are_rejected(self):
        for bad in ('"23058"', "True", "-1", "23058.0"):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "min_engine_build"):
                pp.get_plugin_min_engine_build(
                    self.source(f"    min_engine_build={bad},\n"), "p")

    def test_build_plugman_info_validates_it(self):
        # Caught when the PR is checked, not first when its version is stamped.
        with self.assertRaisesRegex(ValueError, "min_engine_build"):
            build(self.source('    min_engine_build="23058",\n').decode())
        info = build(self.source("    min_engine_build=23058,\n").decode())
        self.assertEqual(info["min_engine_build"], 23058)

    def test_stamping_writes_it(self):
        import auto_apply_version_metadata as avm
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sample_plugin.py")
            with open(path, "wb") as fout:
                fout.write(b"# ba_meta require api 9\n"
                           + self.source("    min_engine_build=23058,\n"))
            category = {"plugins": {"sample_plugin": {"versions": {"1.0.0": None}}}}
            entry = (avm.PluginVersionMetadata("sample_plugin", "1.0.0", path)
                     .set_json(category).set_api_version().set_min_engine_build()
                     .json["plugins"]["sample_plugin"]["versions"]["1.0.0"])
        self.assertEqual(entry, {"api_version": 9, "min_engine_build": 23058})


class TestVersionKey(unittest.TestCase):
    """version_key orders every `versions` block in every manifest."""

    def test_orders_numerically_not_lexically(self):
        self.assertGreater(apm.version_key("1.0.10"), apm.version_key("1.0.9"))
        self.assertGreater(apm.version_key("1.10.0"), apm.version_key("1.9.0"))
        self.assertGreater(apm.version_key("2.0.0"), apm.version_key("1.99.99"))

    def test_equal_versions_compare_equal(self):
        self.assertEqual(apm.version_key("1.2.3"), apm.version_key("1.2.3"))

    def test_sorts_a_versions_block_newest_first(self):
        versions = ["1.0.9", "1.0.10", "1.1.0", "1.0.2"]
        self.assertEqual(
            sorted(versions, key=apm.version_key, reverse=True),
            ["1.1.0", "1.0.10", "1.0.9", "1.0.2"],
        )

    def test_non_numeric_versions_are_rejected(self):
        for version in ("1.0.0-beta", "v1.0.0", "1.0.x", ""):
            with self.subTest(version=version):
                with self.assertRaisesRegex(ValueError, "not in x.y.z form"):
                    apm.version_key(version)


class TestCatalogPlugmanBlocks(unittest.TestCase):
    """Every plugman block actually in the catalog must still parse."""

    def test_every_plugman_block_in_the_catalog_parses(self):
        checked = 0
        for path in sorted((REPO_ROOT / "plugins").glob("*/*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if not (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "plugman"
                ):
                    continue
                with self.subTest(plugin=path.name):
                    self.assertIsInstance(node.value, ast.Call)
                    self.assertEqual(node.value.func.id, "dict")
                    info = apm.build_plugman_info(node, tree, str(path), path.stem)
                    self.assertEqual(info["plugin_name"], path.stem)
                    self.assertIsInstance(info["version"], str)
                checked += 1
        self.assertGreater(checked, 0, "no plugman blocks found in plugins/")


if __name__ == "__main__":
    unittest.main()

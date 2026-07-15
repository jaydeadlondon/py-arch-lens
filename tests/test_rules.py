from src.rules import matches_pattern, rules_from_mapping


def test_rules_from_mapping():
    rules = rules_from_mapping(
        {
            "layers": [
                {"name": "ui", "modules": ["app.ui.*"], "may_depend_on": ["core"]}
            ],
            "forbidden_imports": [
                {"source": "app.*", "target": "tests.*", "reason": "no tests"}
            ],
            "ignore": [{"source": "app.cli", "target": "app.tui"}],
        }
    )
    assert rules.layers[0].name == "ui"
    assert rules.layers[0].may_depend_on == ["core"]
    assert rules.forbidden_imports[0].reason == "no tests"
    assert rules.ignore[0].target == "app.tui"


def test_matches_pattern():
    assert matches_pattern("app.ui.views", "app.ui.*")
    assert not matches_pattern("app.core", "app.ui.*")

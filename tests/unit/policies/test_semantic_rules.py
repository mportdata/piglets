from piglets.policies import SemanticRules


def test_critical_rules_to_string_excludes_domain_policies():
    rules = SemanticRules()

    critical_rules = rules.critical_rules_to_string()

    assert "CRITICAL RULES:" in critical_rules
    assert "Use only tables, columns, and relationships" in critical_rules
    assert "Prefer explicit primary-key and foreign-key relationships" not in critical_rules


def test_to_string_still_includes_enabled_domain_policies():
    rules = SemanticRules()

    rule_text = rules.to_string()

    assert "CRITICAL RULES:" in rule_text
    assert "Prefer explicit primary-key and foreign-key relationships" in rule_text

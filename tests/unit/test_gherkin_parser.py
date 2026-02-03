"""
Tests for gtaa_validator.parsers.gherkin_parser

Covers:
- Parsing Feature, Scenario, Scenario Outline, Background
- Step extraction (Given/When/Then/And/But)
- has_given/has_when/has_then properties
- And/But keyword inheritance
- Edge cases: empty content, no feature, comments, tags
"""

import pytest

from gtaa_validator.parsers.gherkin_parser import (
    GherkinParser, GherkinFeature, GherkinScenario, GherkinStep,
)


@pytest.fixture
def parser():
    return GherkinParser()


# =========================================================================
# Basic parsing
# =========================================================================

class TestBasicParsing:

    def test_parse_simple_feature(self, parser):
        content = """Feature: Login
  Scenario: Valid login
    Given I am on the login page
    When I enter valid credentials
    Then I should see the dashboard
"""
        feature = parser.parse(content)
        assert feature is not None
        assert feature.name == "Login"
        assert len(feature.scenarios) == 1
        assert feature.scenarios[0].name == "Valid login"
        assert len(feature.scenarios[0].steps) == 3

    def test_parse_multiple_scenarios(self, parser):
        content = """Feature: Search
  Scenario: Basic search
    Given I am on the home page
    When I search for "test"
    Then I see results

  Scenario: Empty search
    Given I am on the home page
    When I search for ""
    Then I see no results
"""
        feature = parser.parse(content)
        assert len(feature.scenarios) == 2

    def test_parse_returns_none_for_empty_content(self, parser):
        assert parser.parse("") is None
        assert parser.parse("   \n\n  ") is None

    def test_parse_returns_none_for_no_feature(self, parser):
        content = "This is just some text\nwith no Gherkin keywords"
        assert parser.parse(content) is None


# =========================================================================
# Steps and keywords
# =========================================================================

class TestSteps:

    def test_step_keywords(self, parser):
        content = """Feature: Test
  Scenario: Steps
    Given a precondition
    When an action
    Then a result
    And another result
    But not this
"""
        feature = parser.parse(content)
        steps = feature.scenarios[0].steps
        assert len(steps) == 5
        assert steps[0].keyword == "Given"
        assert steps[1].keyword == "When"
        assert steps[2].keyword == "Then"
        assert steps[3].keyword == "And"
        assert steps[4].keyword == "But"

    def test_step_text_extraction(self, parser):
        content = """Feature: Test
  Scenario: Text
    Given I have 5 items in my cart
"""
        feature = parser.parse(content)
        assert feature.scenarios[0].steps[0].text == 'I have 5 items in my cart'

    def test_step_line_numbers(self, parser):
        content = """Feature: Test

  Scenario: Lines
    Given step on line 4
    When step on line 5
"""
        feature = parser.parse(content)
        steps = feature.scenarios[0].steps
        assert steps[0].line == 4
        assert steps[1].line == 5


# =========================================================================
# has_given / has_when / has_then
# =========================================================================

class TestHasKeywords:

    def test_has_all_keywords(self, parser):
        content = """Feature: Test
  Scenario: Full
    Given precondition
    When action
    Then result
"""
        scenario = parser.parse(content).scenarios[0]
        assert scenario.has_given is True
        assert scenario.has_when is True
        assert scenario.has_then is True

    def test_missing_then(self, parser):
        content = """Feature: Test
  Scenario: No then
    Given precondition
    When action
"""
        scenario = parser.parse(content).scenarios[0]
        assert scenario.has_given is True
        assert scenario.has_when is True
        assert scenario.has_then is False

    def test_and_inherits_keyword(self, parser):
        content = """Feature: Test
  Scenario: And inherits
    Given first
    And second
    When action
    Then result
    And another result
"""
        scenario = parser.parse(content).scenarios[0]
        assert scenario.has_given is True
        assert scenario.has_then is True

    def test_but_inherits_keyword(self, parser):
        content = """Feature: Test
  Scenario: But inherits
    Given precondition
    When action
    Then result
    But not error
"""
        scenario = parser.parse(content).scenarios[0]
        assert scenario.has_then is True


# =========================================================================
# Background
# =========================================================================

class TestBackground:

    def test_parse_background(self, parser):
        content = """Feature: Test
  Background:
    Given I am logged in

  Scenario: With background
    When I do something
    Then I see result
"""
        feature = parser.parse(content)
        assert feature.background is not None
        assert len(feature.background.steps) == 1
        assert feature.background.steps[0].keyword == "Given"
        assert len(feature.scenarios) == 1


# =========================================================================
# Scenario Outline
# =========================================================================

class TestScenarioOutline:

    def test_parse_scenario_outline(self, parser):
        content = """Feature: Test
  Scenario Outline: Parameterized
    Given I have <count> items
    When I remove one
    Then I have <remaining> items

  Examples:
    | count | remaining |
    | 5     | 4         |
"""
        feature = parser.parse(content)
        assert len(feature.scenarios) == 1
        assert feature.scenarios[0].is_outline is True
        assert len(feature.scenarios[0].steps) == 3


# =========================================================================
# Comments and tags
# =========================================================================

class TestCommentsAndTags:

    def test_comments_are_ignored(self, parser):
        content = """# This is a comment
Feature: Test
  # Another comment
  Scenario: Simple
    Given something
"""
        feature = parser.parse(content)
        assert feature is not None
        assert len(feature.scenarios) == 1

    def test_tags_are_ignored(self, parser):
        content = """@smoke @regression
Feature: Tagged
  @critical
  Scenario: Tagged scenario
    Given something
"""
        feature = parser.parse(content)
        assert feature.name == "Tagged"
        assert len(feature.scenarios) == 1

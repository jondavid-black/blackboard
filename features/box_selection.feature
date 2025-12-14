Feature: Box Selection Tool

  Background:
    Given I launch the blackboard app

  Scenario: Select multiple objects using box selection
    Given I have created a rectangle at 100, 100 with size 100x100
    And I have created a circle at 300, 100 with radius 50
    And I select the "box_selection" tool
    When I drag from 50, 50 to 400, 250
    Then the rectangle should be selected
    And the circle should be selected

  Scenario: Move selected group by dragging one of the selected objects
    Given I have created a rectangle at 100, 100 with size 100x100
    And I have created a circle at 300, 100 with radius 50
    And I have selected both shapes
    And I select the "box_selection" tool
    When I drag the rectangle from 150, 150 to 250, 250
    Then the rectangle should be at 200, 200
    And the circle should be at 400, 200

  Scenario: Clear selection by starting a new box selection in empty space
    Given I have created a rectangle at 100, 100 with size 100x100
    And I have selected the rectangle
    And I select the "box_selection" tool
    When I drag from 500, 500 to 600, 600
    Then the rectangle should not be selected

  Scenario: Box selection disappears after drag end
    Given I select the "box_selection" tool
    When I drag from 100, 100 to 200, 200
    Then the selection box should not be visible

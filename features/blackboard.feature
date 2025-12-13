Feature: Blackboard Application
  As a user
  I want to access the blackboard
  So that I can draw and organize my thoughts

  Scenario: Application loads successfully
    Given the blackboard application is running
    When I open the application in the browser
    Then the page title should be "Blackboard"
    And I should see the toolbar
    And I should see the canvas


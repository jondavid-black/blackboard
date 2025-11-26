Feature: Whiteboard Application
  As a user
  I want to access the whiteboard
  So that I can draw and organize my thoughts

  Scenario: Application loads successfully
    Given the whiteboard application is running
    When I open the application in the browser
    Then the page title should be "Whiteboard"
    And I should see the toolbar
    And I should see the canvas

Feature: display global variables

   Scenario: fetch the global variables
     Given I fetch the global variables 
     then I get a json dictionary

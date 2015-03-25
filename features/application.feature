Feature: application lifecycle

    Scenario: create an new application
       Given I have a paas api service
       When I create an application "testapp"
       Then I get an application json document for "testapp" with attribute "name" and value "testapp"

    Scenario: I build a test application slug
	Given I have a slugbuilder service
        When I post a tarball to the slugbuilder service
        Then I get a slug for my application 

    Scenario: change application url 
       Given I have a paas api service
       When I set attribute "urls" to "testapp.domain.com" for application "testapp"
       Then I get an application json document for "testapp" with attribute "urls" and value "testapp.domain.com"

    Scenario: delete an application
	Given I have a paas api service
	When I delete an application "testapp"	
	Then I get a message confirming the application is removed

Feature: application lifecycle

    Scenario: clean testapp to begin
       Given I have a paas api service
       When I delete an application "testapp"	
       Then I get a message confirming the application was removed or not found 

    @dev
    Scenario: create host record
       Given I have a paas api service
       When I "add" a host "192.168.0.240"
       Then I get a success message from the host endpoint

    Scenario: create an new application
       Given I have a paas api service
       When I create an application "testapp"
       Then I get an application json document for "testapp" with variable "name" and value "testapp"

    Scenario: I build a test application slug
       Given I have a slugbuilder service
       When I post a tarball to the slugbuilder service
       Then I get a slug for my application 

    Scenario: change application url 
       Given I have a paas api service
       When I set variable "urls" to "testapp.domain.com" for application "testapp"
       Then I get an application json document for "testapp" with variable "urls" and value "testapp.domain.com"

    Scenario: change application docker image
        Given I have a paas api service
        When I set variable "docker_image" to "flynn/slugrunner:latest" for application "testapp"
        Then I get an application json document for "testapp" with variable "docker_image" and value "flynn/slugrunner:latest"

    Scenario: change application command
        Given I have a paas api service
        When I set variable "command" to "start web" for application "testapp"
        Then I get an application json document for "testapp" with variable "command" and value "start web"

    Scenario: set application slug to an invalid slug url
        Given I have a paas api service
        When I set the slug url for application "testapp" to "invalidurl"
        Then I get a return message "Slug URL invalidurl is either invalid or inaccessible"

    Scenario: set application slug
        Given I have a paas api service
        When I update the slug url for application "testapp"
        Then I wait for application "testapp" to reach state "RUNNING"
        And I am able to access the site on "testapp.domain.com"

    Scenario: set application memory 
        Given I have a paas api service
        When I set variable "memory_in_mb" to "16" for application "testapp"
        Then I get an application json document for "testapp" with variable "memory_in_mb" and value "16"

    Scenario: add additional container
        Given I have a paas api service
        When I set variable "container_count" to "3" for application "testapp"
        Then I wait for application "testapp" to reach state "RUNNING"
        And I am able to access the site on "testapp.domain.com"
        And I get an application json document for "testapp" with variable "container_count" and value "3"

    Scenario: add environment variables
        Given I have a paas api service
        When I set environment variable "TEST_VARIABLE" to "test_with_3_containers" for application "testapp"
        Then I wait for application "testapp" to reach state "RUNNING"
        And I am able to access the site on "testapp.domain.com"
        And I get an application json document for "testapp" with environment variable "TEST_VARIABLE" and value "test_with_3_containers"

    Scenario: decrease containers to 1
        Given I have a paas api service
        When I set variable "container_count" to "1" for application "testapp"
        Then I wait for application "testapp" to reach state "RUNNING"
        And I am able to access the site on "testapp.domain.com"
        And I get an application json document for "testapp" with variable "container_count" and value "1"

    Scenario: add environment variables
        Given I have a paas api service
        When I set environment variable "TEST_VARIABLE" to "test_with_1_containers" for application "testapp"
        Then I wait for application "testapp" to reach state "RUNNING"
        And I am eventually able to access the site on "testapp.domain.com"
        And I get an application json document for "testapp" with environment variable "TEST_VARIABLE" and value "test_with_1_containers"

    Scenario: read from events endpoint
        Give I have a paas api service
        When I requests the events for "testapp"
        Then I get an event document with a "CREATE" event

    Scenario: delete an application
	     Given I have a paas api service
	     When I delete an application "testapp"	
	     Then I get a message confirming the application is removed

    @dev
    Scenario: delete host record
       Given I have a paas api service
       When I "remove" a host "192.168.0.240"
       Then I get a success message from the host endpoint 

from behave import *
from hamcrest import *
import json

@given('I have a paas api service')
def step_impl(context):
	response = context.web_requests.get(context.api_url + "/app/", verify=False)
	assert_that(response.status_code, equal_to(200))

@when('I create an application "{application}"')
def step_impl(context, application):
	payload = { "name": application }
	headers = { "Content-type": "application/json" }
	context.response = context.web_requests.post(context.api_url + '/app/', data=json.dumps(payload), headers=headers) 
	assert_that(context.response.status_code, equal_to(201))

@then('I get an application json document for "{application}" with attribute "{attribute}" and value "{value}"')
def step_impl(context, application, attribute, value):
	data = context.response.json()
	assert_that(data, has_entry(attribute, value))

@when('I set environment variable "{variable}" to "{value}" for application "{application}"')
def step_impl(context, variable, value, application):
	headers = { "Content-type": "application/json" }
	payload = { "environment": { variable: value } } 
	context.response = context.web_requests.patch(context.api_url + "/app/" + application, data=json.dumps(payload), headers=headers)
	assert_that(context.response.status_code, equal_to(201))

@when('I set attribute "{attribute}" to "{value}" for application "{application}"')
def step_impl(context, attribute, value, application):
	headers = { "Content-type": "application/json" }
	payload = { attribute: value }
	context.response = context.web_requests.patch(context.api_url + "/app/" + application, data=json.dumps(payload), headers=headers)
	assert_that(context.response.status_code, equal_to(201))

@when('I delete an application "{application}"')
def step_impl(context, application):
	context.response = context.web_requests.delete(context.api_url + "/app/" + application)

@then('I get a message confirming the application is removed')
def step_impl(context):
	assert_that(context.response.status_code, equal_to(200))

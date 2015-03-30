from behave import *
from hamcrest import *
import json
import time

@given('I have a paas api service')
def step_impl(context):
	response = context.web_requests.get(context.api_url + "/app/", verify=False)
	assert_that(response.status_code, equal_to(200))

@when('I create an application "{application}"')
def step_impl(context, application):
	payload = { "name": application }
	headers = { "Content-type": "application/json" }
	context.response = context.web_requests.post(context.api_url + '/app/', data=json.dumps(payload), headers=headers) 
	assert_that(context.response.status_code, equal_to(201), context.response.text)

@then('I get an application json document for "{application}" with variable "{variable}" and value "{value}"')
def step_impl(context, application, variable, value):
	data = context.response.json()
	assert_that(data, has_entry(variable, value))

@then('I get an application json document for "{application}" with environment variable "{variable}" and value "{value}"')
def step_impl(context, application, variable, value):
	data = context.response.json()
	assert_that(data['environment'], has_entry(variable, value))

@when('I set environment variable "{variable}" to "{value}" for application "{application}"')
def step_impl(context, variable, value, application):
	headers = { "Content-type": "application/json" }
	payload = { "environment": { variable: value } } 
	context.response = context.web_requests.patch(context.api_url + "/app/" + application, data=json.dumps(payload), headers=headers)
	assert_that(context.response.status_code, equal_to(201))

@when('I set variable "{variable}" to "{value}" for application "{application}"')
def step_impl(context, variable, value, application):
	headers = { "Content-type": "application/json" }
	payload = { variable: value }
	context.response = context.web_requests.patch(context.api_url + "/app/" + application, data=json.dumps(payload), headers=headers)
	assert_that(context.response.status_code, equal_to(201))

@when('I delete an application "{application}"')
def step_impl(context, application):
	context.response = context.web_requests.delete(context.api_url + "/app/" + application)

@then('I get a message confirming the application is removed')
def step_impl(context):
	assert_that(context.response.status_code, equal_to(200))

@when('I update the slug url for application "{application}"')
def step_impl(context, application):
	headers = { "Content-type": "application/json" }
	payload = { "environment": { "SLUG_URL": context.slug_url } } 
	context.response = context.web_requests.patch(context.api_url + "/app/" + application, data=json.dumps(payload), headers=headers)
	
@then('I wait for application "{application}" to reach state "{state}"')
def step_impl(context, application, state):
	count = 0
	max_count = 60
	success = 0
	while True:
		context.response = context.web_requests.get(context.api_url + "/app/{}".format(application))
		data = context.response.json()
		if data['state'] == state:
			success = 1
			break
		time.sleep(2)
		count += 1
		if count >= max_count:
			break

	assert_that(success, equal_to(1), context.response.text)

@then('I am able to access the site on "{url}"')
def step_impl(context, url):
	headers = { "Host": "{}".format(url) }
	response = context.web_requests.get(context.router_url, headers=headers)	
	assert_that(response.status_code, equal_to(200), context.response.text)

@then('I am eventually able to access the site on "{url}"')
def step_impl(context, url):
	headers = { "Host": "{}".format(url) }
	for i in range(1,10):
	    response = context.web_requests.get(context.router_url, headers=headers)	
            if response.status_code != 200:
               time.sleep(2)
               count += 1
               continue
            else:
               break

	assert_that(response.status_code, equal_to(200), context.response.text)


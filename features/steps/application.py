from behave import *
from hamcrest import *

@given('I have a paas api service')
def step_impl(context):
	context.web_requests.get(context.api_url, verify=False)

@when('I create an application "{application}"')
def step_impl(context, application):
	pass

@then('I get an application json document for "{application}" with attribute "{attribute}" and value "{value}"')
def step_impl(context, application, attribute, value):
	pass

@given('I have a slugbuilder service')
def step_impl(context):
	False

@when('I post a tarball to the slugbuilder service')
def step_impl(context):
	pass

@then('I get a slug for my application')
def step_impl(context):
	pass

@when('I set attribute "{attribute}" to "{value}" for application "{application}"')
def step_impl(context, attribute, value, application):
	pass

@when('I delete an application "{application}"')
def step_impl(context, application):
	pass

@then('I get a message confirming the application is removed')
def step_impl(context):
	pass

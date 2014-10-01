#!/usr/bin/env bash

V_ENV_NAME="captain-venv"
if [ ! -d ${V_ENV_NAME} ] ;  then
    virtualenv ${V_ENV_NAME}
fi
source "${V_ENV_NAME}/bin/activate"

diff <(sort requirements.txt requirements-tests.txt | grep -v ^"#") <(pip freeze | sort)
if [ $? != 0 ] ; then
  echo "Doing Pip Installs"
  pip install --upgrade -q -r requirements.txt
  pip install --upgrade -q -r requirements-tests.txt
fi
rm -fr target
mkdir target
nosetests --with-xunit --xunit-file=target/nosetests.xml --with-xcover --xcoverage-file=target/coverage/coverage.xml --cover-package=captain --cover-erase --cover-html-dir=target/coverage --cover-html
result=$?

deactivate
exit $result

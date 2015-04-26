from webvirtmgr.settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

INSTALLED_APPS += ('django_jenkins',)

JENKINS_TASKS = (
    # 'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.django_tests',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
)

# This file makes the 'mysite' directory a Python package.
#
# Celery: use `celery -A mysite worker` (loads mysite.celery). Do not import celery
# here — avoids circular imports; @shared_task binds when the worker starts.

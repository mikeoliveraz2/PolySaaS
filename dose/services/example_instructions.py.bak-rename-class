# Example: Create these rows in Django admin or shell for POST testing

from dose.models import Instruction

# CopilotQueryService instruction
"""
Instruction.objects.create(
    requestpath='/api/copilot_query/',
    requestmethod='POST',
    direction='REQ',
    executescript='CopilotQueryService',
    matchingEventKey='copilot_query',
    description='Test Copilot atomic service',
)
"""

# DifferentialEquationService instruction
"""
Instruction.objects.create(
    requestpath='/api/differential_equation/',
    requestmethod='POST',
    direction='REQ',
    executescript='DifferentialEquationService',
    matchingEventKey='differential_equation',
    description='Test Differential Equation atomic service',
)
"""

# You can run this in Django shell:
# python manage.py shell
# >>> exec(open('dose/services/example_instructions.py').read())

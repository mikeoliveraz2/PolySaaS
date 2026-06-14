import sys
from pathlib import Path

# Project root on path; drop this folder so local modules (e.g. logging.py) do not shadow stdlib.
_root = Path(__file__).resolve().parents[2]
_services_dir = Path(__file__).resolve().parent
sys.path = [p for p in sys.path if Path(p).resolve() != _services_dir]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import numpy as np
from dose.services.differential_equation import Calculus
# Example: dy/dt = -k*y, y(0) = 10, k = 0.3
k = 0.3
def fun(t, y):
    return -k * y

t_span = (0, 10)
y0 = [10]
t_eval = np.linspace(0, 10, 100)

result = Calculus.solve_ode(fun, t_span, y0, t_eval=t_eval)

print('t:', result.t)
print('y:', result.y)
print('status:', result.status)
print('message:', result.message)

# Optionally, plot the result if matplotlib is available
try:
    import matplotlib.pyplot as plt
    plt.plot(result.t, result.y[0])
    plt.xlabel('Time')
    plt.ylabel('y')
    plt.title('Exponential Decay: dy/dt = -k*y')
    plt.show()
except ImportError:
    print('matplotlib not installed, skipping plot.')

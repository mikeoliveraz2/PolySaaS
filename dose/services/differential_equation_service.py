
import numpy as np
from scipy.integrate import solve_ivp
from dose.services.atomic_service_base import AtomicServiceBase

class Calculus(AtomicServiceBase):
    @staticmethod
    def execute_and_save(request, instruction_row):
        """
        Standard atomic service entrypoint for DoseRequestController.
        Expects ODE parameters in request.POST (or request.data).
        """
        # Parameter resolution hierarchy:
        # 1st: Parameters table matching event key
        # 2nd: instruction_row.parameters_json
        # 3rd: Static defaults

        # Get event_key first to look up parameters
        if hasattr(instruction_row, 'eventKey') and instruction_row.eventKey:
            event_key = instruction_row.eventKey
        else:
            event_key = 'differential_equation'  # default event key

        # Try to get parameters from parameters table first
        params_from_table = None
        user = request.user if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False) else None
        tenant = getattr(user, 'userprofile', None).tenant if user and hasattr(user, 'userprofile') else None

        if tenant and event_key:
            try:
                from parameters.models import Parameter
                # Look for parameters matching the event key
                param_records = Parameter.objects.filter(tenant=tenant, event_key=event_key)
                if param_records.exists():
                    params_from_table = {}
                    for param_record in param_records:
                        params_from_table[param_record.name] = param_record.value
                    print(f"Calculus: Found {len(params_from_table)} parameters from table for event_key '{event_key}'")
            except Exception as e:
                print(f"Calculus: Error loading parameters from table: {e}")

        # Get parameters from instruction_row.parameters_json if available
        params_from_instruction = getattr(instruction_row, 'parameters_json', None)

        # Parameter resolution with priority order
        def get_param(param_name, param_type=float, default_value=None):
            """Get parameter with priority: table -> instruction -> default"""
            # 1st priority: Parameters table
            if params_from_table and param_name in params_from_table:
                try:
                    return param_type(params_from_table[param_name])
                except (ValueError, TypeError) as e:
                    print(f"Calculus: Error converting table param '{param_name}': {e}")

            # 2nd priority: Instruction parameters
            if params_from_instruction and param_name in params_from_instruction:
                try:
                    return param_type(params_from_instruction[param_name])
                except (ValueError, TypeError) as e:
                    print(f"Calculus: Error converting instruction param '{param_name}': {e}")

            # 3rd priority: Default value
            if default_value is not None:
                return default_value

            # If no default provided, raise error
            raise ValueError(f"Required parameter '{param_name}' not found in parameters table, instruction, or defaults")

        # Resolve all parameters using the hierarchy
        try:
            k = get_param('k', float, 0.3)
            y0 = [get_param('y0', float, 10)]
            t0 = get_param('t0', float, 0)
            tf = get_param('tf', float, 10)
            n_points = get_param('n_points', int, 100)

            print(f"Calculus: Using parameters - k={k}, y0={y0[0]}, t0={t0}, tf={tf}, n_points={n_points}")
        except ValueError as e:
            raise ValueError(f"Parameter resolution failed: {e}")
        def fun(t, y):
            return -k * y
        t_span = (t0, tf)
        t_eval = np.linspace(t0, tf, n_points)

        # event_key was already determined above in parameter resolution
        description = getattr(instruction_row, 'description', None) or 'Differential equation result'
        try:
            result = Calculus.solve_ode(fun, t_span, y0, t_eval=t_eval)
            # Compose callback parameters: include both input params and result
            # Create input_parameters dict from resolved values
            input_parameters = {
                'k': k,
                'y0': y0[0],
                't0': t0,
                'tf': tf,
                'n_points': n_points,
                'event_key': event_key
            }

            # Add source information for debugging
            if params_from_table:
                input_parameters['_source'] = 'parameters_table'
                input_parameters['_table_params'] = params_from_table
            elif params_from_instruction:
                input_parameters['_source'] = 'instruction_json'
                input_parameters['_instruction_params'] = params_from_instruction
            else:
                input_parameters['_source'] = 'static_defaults'

            callback_params = {
                'input_parameters': input_parameters,
                'result': {
                    't': result.t.tolist() if hasattr(result.t, 'tolist') else list(result.t),
                    'y': [list(arr) for arr in result.y] if hasattr(result.y, '__iter__') else [result.y],
                    'status': result.status,
                    'message': result.message
                }
            }
            from dose.models import CallBackData, DoseMessage
            cb = CallBackData.objects.create(
                tenant=tenant,
                matchingEventKey=event_key,
                description=description,
                parameters_json=callback_params
            )
            # Send DoseMessage with success and result value, include event_key
            if user:
                DoseMessage.objects.create(
                    user=user,
                    message=f"[{event_key}] Differential equation solved successfully. Final value: {result.y[0][-1] if hasattr(result, 'y') and len(result.y) > 0 else 'N/A'}",
                    level='success'
                )
            return cb
        except Exception as e:
            # Send DoseMessage with failure, include event_key
            from dose.models import DoseMessage
            if user:
                DoseMessage.objects.create(
                    user=user,
                    message=f"[{event_key}] Differential equation service failed: {str(e)}",
                    level='error'
                )
            raise
    # save_result_to_callback is now handled inline in execute_and_save for full context
    """
    Atomic service for solving differential equations using scipy.
    """
    @staticmethod
    def solve_ode(fun, t_span, y0, method='RK45', t_eval=None, **kwargs):
        """
        Solve an ordinary differential equation (ODE).
        Args:
            fun: Callable(t, y) -> dydt
            t_span: tuple (t0, tf)
            y0: initial state
            method: integration method (default 'RK45')
            t_eval: times to evaluate solution
            kwargs: extra arguments for solve_ivp
        Returns:
            result: scipy.integrate.OdeResult
        """
        return solve_ivp(fun, t_span, y0, method=method, t_eval=t_eval, **kwargs)

    @staticmethod
    def example_exponential_decay():
        # Example: dy/dt = -k*y, y(0) = 10, k = 0.3
        k = 0.3
        def fun(t, y):
            return -k * y
        t_span = (0, 10)
        y0 = [10]
        t_eval = np.linspace(0, 10, 100)
        result = Calculus.solve_ode(fun, t_span, y0, t_eval=t_eval)
        return result

# Example output:
# python dose/services/test_differential_equation_service.py
# t: [ 0.          0.1010101   0.2020202   0.3030303   0.4040404   0.50505051
#   0.60606061  0.70707071  0.80808081  0.90909091  1.01010101  1.11111111
#   1.21212121  1.31313131  1.41414141  1.51515152  1.61616162  1.71717172
#   1.81818182  1.91919192  2.02020202  2.12121212  2.22222222  2.32323232
#   2.42424242  2.52525253  2.62626263  2.72727273  2.82828283  2.92929293
#   3.03030303  3.13131313  3.23232323  3.33333333  3.43434343  3.53535354
#   3.63636364  3.73737374  3.83838384  3.93939394  4.04040404  4.14141414
#   4.24242424  4.34343434  4.44444444  4.54545455  4.64646465  4.74747475
#   4.84848485  4.94949495  5.05050505  5.15151515  5.25252525  5.35353535
#   5.45454545  5.55555556  5.65656566  5.75757576  5.85858586  5.95959596
#   6.06060606  6.16161616  6.26262626  6.36363636  6.46464646  6.56565657
#   6.66666667  6.76767677  6.86868687  6.96969697  7.07070707  7.17171717
#   7.27272727  7.37373737  7.47474747  7.57575758  7.67676768  7.77777778
#   7.87878788  7.97979798  8.08080808  8.18181818  8.28282828  8.38383838
#   8.48484848  8.58585859  8.68686869  8.78787879  8.88888889  8.98989899
#   9.09090909  9.19191919  9.29292929  9.39393939  9.49494949  9.5959596
#   9.6969697   9.7979798   9.8989899  10.        ]
# y: [[10.          9.70151504  9.41193681  9.13099587  8.85843872  8.59401836
#    8.33749391  8.08863061  7.8471998   7.61297894  7.38575161  7.16530748
#    6.95144235  6.74395813  6.54266138  6.34728699  6.15763425  5.97355995
#    5.7949227   5.62158285  5.45340252  5.29024565  5.13197789  4.97846673
#    4.82958138  4.68519285  4.54517394  4.40939919  4.27774495  4.1500893
#    4.02631215  3.90629513  3.78992169  3.67707703  3.56764813  3.46152374
#    3.35859439  3.25875239  3.16189182  3.06790853  2.97670015  2.88816607
#    2.80220749  2.71872735  2.63763054  2.55887484  2.48243106  2.40824031
#    2.33624451  2.26638633  2.19860927  2.13285758  2.06907632  2.00721133
#    1.94720923  1.88901744  1.83258415  1.77785837  1.72478985  1.67332917
#    1.62342767  1.5750375   1.52811157  1.48260359  1.43846806  1.39566028
#    1.3541363   1.31385299  1.274768    1.23683976  1.2000275   1.1642912
#    1.12959169  1.09589077  1.06317172  1.03141866  1.00060597  0.97070846
#    0.9417013   0.9135601   0.88626084  0.8597799   0.83409409  0.80918058
#    0.78501697  0.76158125  0.7388518   0.71680742  0.69542728  0.67469099
#    0.65457852  0.63507027  0.61614702  0.59778997  0.57998069  0.56270117
#    0.54593381  0.52966139  0.51386708  0.49853449]]
# status: 0
# message: The solver successfully reached the end of the integration interval.

# dose/services/atomic_service_base.py
"""
Abstract base class for all atomic services.
All atomic services must inherit from this and implement execute_and_save(request, instruction_row).
"""
from abc import ABC, abstractmethod


class AtomicServiceBase(ABC):
    @staticmethod
    @abstractmethod
    def execute_and_save(request, instruction_row):
        """
        Execute the atomic service and save results to CallBackData.
        Must be implemented by all atomic services.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_parameters(parameters, key):
        """
        Lookup and return parameters matching the given key.
        Must be implemented by all atomic services.
        Example: AtomicService1.get_parameters(parameters, 'AtomicService1')
        """
        pass

# Example usage:
# class MyAtomicService(AtomicServiceBase):
#     @staticmethod
#     def execute_and_save(request, instruction_row):
#         ...

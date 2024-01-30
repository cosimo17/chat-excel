from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def _update(self, subject):
        pass
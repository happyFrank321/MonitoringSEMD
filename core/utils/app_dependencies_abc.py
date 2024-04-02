from abc import abstractmethod


__all__ = ['AppDependenciesABC']


class AppDependenciesABC:
    @abstractmethod
    async def is_ready(self) -> bool:
        """Not Implemented"""

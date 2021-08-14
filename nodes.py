from abc import ABC, abstractmethod


class FileIoNode(ABC):
    def run(self):
        """Read data, process it and save the result"""
        in_objs = self._read_input()
        result = self._process(in_objs)
        self._write_output(result)

    @abstractmethod
    def _process(self, in_objs):
        pass

    @abstractmethod
    def _read_input(self):
        pass

    @abstractmethod
    def _write_output(self):
        pass

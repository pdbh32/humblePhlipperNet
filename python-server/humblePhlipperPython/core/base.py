from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd

from humblePhlipperPython.schemata.domain.quote import Quote

class BaseQuoteModel(ABC):

    @abstractmethod
    def train(self, five_m: pd.DataFrame, one_h: pd.DataFrame, latest: pd.DataFrame) -> dict[int, Quote]:
        raise NotImplementedError

    @abstractmethod
    def update(self, five_m: pd.DataFrame, one_h: pd.DataFrame, latest: pd.DataFrame) -> dict[int, Quote]:
        raise NotImplementedError

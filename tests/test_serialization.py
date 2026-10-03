import unittest
from dataclasses import dataclass
from enum import Enum
from bshl.serialization import dumps

class State(Enum):
    WAIT = "Wait"

@dataclass
class Card:
    state: State
    value: float

class SerializationTests(unittest.TestCase):
    def test_enum_dataclass_json(self):
        self.assertIn('"state": "Wait"', dumps(Card(State.WAIT, 3)))

    def test_nonfinite_rejected(self):
        for value in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                dumps(Card(State.WAIT, value))


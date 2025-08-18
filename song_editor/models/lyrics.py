from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class WordRow:
	text: str
	start: float
	end: float
	confidence: float
	chord: Optional[str] = None
	alt_text: Optional[str] = None
	alt_chord: Optional[str] = None
	alt_start: Optional[float] = None
	alt_end: Optional[float] = None



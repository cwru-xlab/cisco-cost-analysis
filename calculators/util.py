from typing import Union

IntOrFloat = Union[int, float]

AVG_SECS_PER_MONTH = 2.628e6
MB_TO_GB_FACTOR = 9.765625e-4
KB_TO_GB_FACTOR = 9.5367432e-7


def verify_in_bounds(name, value, lower, upper):
	if (value < lower) or (value > upper):
		raise ValueError(
			f"'{name}' must be between {lower} and {upper}; got {value}")
	return value


def mb_to_gb(mb):
	return mb * MB_TO_GB_FACTOR


def kb_to_gb(kb):
	return kb * KB_TO_GB_FACTOR

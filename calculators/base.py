import abc


class BaseCostCalculator(abc.ABC):

	def __init__(self, *args, **kwargs):
		super().__init__()

	@abc.abstractmethod
	def calculate_cost(self):
		return 0

import math

import numpy as np

from . import base, util
from .util import AVG_SECS_PER_MONTH, IntOrFloat

MIN_USERS = 1
MAX_USERS = math.inf
MIN_BATCH_SIZE = 1
MAX_STANDARD_BATCH_SIZE = 1e4
MIN_BATCH_WINDOW_IN_SECS = 1
MAX_BATCH_WINDOW_IN_SECS = 300
MIN_MSGS_RECEIVED_PER_MIN = 0
MAX_MSGS_RECEIVED_PER_MIN = math.inf
MIN_LAMBDA_RUNNING_TIME_IN_SECS = 0
MAX_LAMBDA_RUNNING_TIME_IN_SECS = 900
MIN_LAMBDA_MEMORY_IN_MB = 128
MAX_LAMBDA_MEMORY_IN_MB = 10240
MIN_CONCURRENCY = 5
MAX_CONCURRENCY = 1e3
MIN_POLLING_IN_SECS = 0
MAX_POLLING_IN_SECS = 20
MIN_REQUEST_SIZE_IN_KB = 1
MAX_REQUEST_SIZE_IN_KB = 256
REQUEST_SIZE_IN_KB = 64
MAX_SYNC_PAYLOAD_IN_KB = 6e3
LAMBDA_COST_PER_GB_SECOND = 1.667e-5
LAMBDA_COST_PER_REQUEST = 2e-7
NUM_FREE_SQS_REQUESTS = 1e6
NUM_FREE_LAMBDA_REQUESTS = 1e6
NUM_FREE_LAMBDA_GB_SECONDS = 4e5


class NodeCostCalculator(base.BaseCostCalculator):
	"""Includes Lambda and SQS. SNS is free for SQS and Lambda integration."""

	def __init__(
			self,
			users: IntOrFloat = 100,
			msg_size_in_kb: IntOrFloat = 64,
			msg_processing_in_secs: IntOrFloat = 1,
			polling_in_secs: IntOrFloat = 1,
			batch_size: IntOrFloat = 1,
			batch_window_in_secs: IntOrFloat = 1,
			msgs_received_per_min: IntOrFloat = 10,
			concurrency: IntOrFloat = 5,
			function_memory_in_mb: IntOrFloat = 128):
		super().__init__()
		self.verify_users(users)
		self.verify_msg_size(msg_size_in_kb)
		self.verify_msg_processing(msg_processing_in_secs)
		self.verify_polling(polling_in_secs)
		self.verify_batch_size(batch_size)
		self.verify_batch_window(batch_window_in_secs)
		self.verify_msgs_received(msgs_received_per_min)
		self.verify_concurrency(concurrency)
		self.verify_function_memory(function_memory_in_mb)
		self.users = users
		self.msg_size_in_kb = msg_size_in_kb
		self.msg_processing_in_secs = msg_processing_in_secs
		self.polling_in_secs = polling_in_secs
		self.batch_size = batch_size
		self.batch_window_in_secs = batch_window_in_secs
		self.msgs_received_per_min = msgs_received_per_min
		self.concurrency = concurrency
		self.function_memory_in_mb = function_memory_in_mb

	@staticmethod
	def verify_users(users):
		return util.verify_in_bounds('users', users, MIN_USERS, MAX_USERS)

	@staticmethod
	def verify_msg_size(msg_size_in_kb):
		return util.verify_in_bounds(
			'msg_size_in_kb',
			msg_size_in_kb,
			MIN_REQUEST_SIZE_IN_KB,
			MAX_REQUEST_SIZE_IN_KB)

	@staticmethod
	def verify_msg_processing(msg_processing_in_secs):
		return util.verify_in_bounds(
			'msg_processing_in_secs',
			msg_processing_in_secs,
			MIN_LAMBDA_RUNNING_TIME_IN_SECS,
			MAX_LAMBDA_RUNNING_TIME_IN_SECS)

	@staticmethod
	def verify_polling(polling_in_secs):
		return util.verify_in_bounds(
			'polling_in_secs',
			polling_in_secs,
			MIN_POLLING_IN_SECS,
			MAX_POLLING_IN_SECS)

	@staticmethod
	def verify_batch_size(batch_size):
		return util.verify_in_bounds(
			'batch_size', batch_size, MIN_BATCH_SIZE, MAX_STANDARD_BATCH_SIZE)

	@staticmethod
	def verify_batch_window(batch_window_in_secs):
		return util.verify_in_bounds(
			'batch_window_in_secs',
			batch_window_in_secs,
			MIN_BATCH_WINDOW_IN_SECS,
			MAX_BATCH_WINDOW_IN_SECS)

	@staticmethod
	def verify_msgs_received(msgs_received_per_min):
		return util.verify_in_bounds(
			'msgs_received_per_min',
			msgs_received_per_min,
			MIN_MSGS_RECEIVED_PER_MIN,
			MAX_MSGS_RECEIVED_PER_MIN)

	@staticmethod
	def verify_concurrency(concurrency):
		return util.verify_in_bounds(
			'concurrency', concurrency, MIN_CONCURRENCY, MAX_CONCURRENCY)

	@staticmethod
	def verify_function_memory(function_memory_in_mb):
		return util.verify_in_bounds(
			'function_memory_in_mb',
			function_memory_in_mb,
			MIN_LAMBDA_MEMORY_IN_MB,
			MAX_LAMBDA_MEMORY_IN_MB)

	def calculate_cost(self):
		sqs = self.sqs()
		lambda_function = self.lambda_function()
		return sqs + lambda_function

	def sqs(self):
		monthly_requests = self.sqs_monthly_requests()
		cost_per_request = self.sqs_request_cost(monthly_requests)
		return monthly_requests * cost_per_request

	def sqs_monthly_requests(self):
		requests_per_sec = self.sqs_requests_per_sec()
		return requests_per_sec * AVG_SECS_PER_MONTH

	@staticmethod
	def sqs_request_cost(monthly_requests):
		if monthly_requests < NUM_FREE_SQS_REQUESTS:
			cost_per_million = 0
		elif NUM_FREE_SQS_REQUESTS <= monthly_requests < 1e11:
			cost_per_million = 0.4
		elif 1e11 <= monthly_requests < 2e11:
			cost_per_million = 0.3
		else:
			cost_per_million = 0.24
		return cost_per_million / 1e6

	def sqs_requests_per_sec(self):
		requests_per_msg = self.sqs_requests_per_msg()
		requests_per_sec = requests_per_msg * self.msgs_received_per_sec
		requests_per_sec /= self.polling_in_secs
		return requests_per_sec * self.users

	def sqs_requests_per_msg(self):
		return math.ceil(self.msg_size_in_kb / REQUEST_SIZE_IN_KB)

	def lambda_function(self):
		compute_cost = self.lambda_monthly_compute_cost()
		request_cost = self.lambda_monthly_request_cost()
		return compute_cost + request_cost

	def lambda_monthly_compute_cost(self):
		gb_secs_used = self.lambda_monthly_gb_secs()
		return LAMBDA_COST_PER_GB_SECOND * gb_secs_used

	def lambda_monthly_gb_secs(self):
		duration_invoked_in_secs = self.lambda_monthly_time_invoked_in_secs()
		mb_secs = duration_invoked_in_secs * self.function_memory_in_mb
		gb_secs = util.mb_to_gb(mb_secs)
		return max(0, gb_secs - NUM_FREE_LAMBDA_GB_SECONDS)

	def lambda_monthly_time_invoked_in_secs(self):
		batch_processing = self.msg_processing_in_secs * self.batch_size
		batch_processing /= self.concurrency
		return batch_processing * self.users

	def lambda_monthly_request_cost(self):
		monthly_requests = self.lambda_monthly_requests()
		return LAMBDA_COST_PER_REQUEST * monthly_requests

	# noinspection PyTypeChecker
	def lambda_monthly_requests(self):
		monthly_invokes = self.lambda_monthly_invokes()
		return max(0, monthly_invokes - NUM_FREE_LAMBDA_REQUESTS)

	def lambda_monthly_invokes(self):
		between_invokes = self.time_between_lambda_invokes_in_secs()
		return math.ceil(AVG_SECS_PER_MONTH / between_invokes) * self.users

	def time_between_lambda_invokes_in_secs(self):
		until_invoked = math.ceil(self.time_until_lambda_invoked_in_secs())
		return np.lcm(until_invoked, self.polling_in_secs)

	def time_until_lambda_invoked_in_secs(self):
		payload_exceeded = self.sqs_payload_exceeds_in_secs()
		batch_filled = self.sqs_batch_filled_in_secs()
		return min(payload_exceeded, batch_filled, self.batch_window_in_secs)

	def sqs_payload_exceeds_in_secs(self):
		msg_size_per_sec_in_kb = self.msg_size_received_per_sec_in_kb()
		return MAX_SYNC_PAYLOAD_IN_KB / msg_size_per_sec_in_kb

	def msg_size_received_per_sec_in_kb(self):
		return self.msgs_received_per_sec * self.msg_size_in_kb

	def sqs_batch_filled_in_secs(self):
		return self.batch_size / self.msgs_received_per_sec

	@property
	def msgs_received_per_sec(self):
		return self.msgs_received_per_min / 60

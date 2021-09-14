import math

from . import base, util
from .util import IntOrFloat

S3_PUT_REQUEST_COST = 5e-6
S3_GET_REQUEST_COST = 4e-7
ECR_STORAGE_COST_PER_GB = 0.1
MIN_MONTHLY_CODE_UPLOADS = 0
MAX_MONTHLY_CODE_UPLOADS = math.inf
MIN_NODE_CREATIONS = 0
MAX_NODE_CREATIONS = math.inf
MIN_NODE_DELETIONS = 0
MAX_NODE_DELETIONS = math.inf
MIN_NODES = 0
MAX_NODES = math.inf
MIN_CODE_SIZE_IN_MB = 0
MAX_CODE_SIZE_IN_MB = math.inf
MIN_EXISTING_CODE_IN_MB = 0
MAX_EXISTING_CODE_IN_MB = math.inf
MIN_CODE_METADATA_IN_KB = 0
MAX_CODE_METADATA_IN_KB = math.inf
MIN_NODE_METADATA_IN_KB = 0
MAX_NODE_METADATA_IN_KB = math.inf
FREE_DYNAMODB_STORAGE_IN_GB = 25
DYNAMODB_STORAGE_COST_PER_GB = 0.25
DYNAMODB_RESTORE_COST_PER_GB = 0.15
DYNAMODB_ON_DEMAND_BACKUP_COST_PER_GB = 0.1
DYNAMODB_EVENTUALLY_CONSISTENT_WRITE_IN_KB = 1
DYNAMODB_EVENTUALLY_CONSISTENT_READ_IN_KB = 4
DYNAMODB_EVENTUALLY_CONSISTENT_WRITE_TO_WRU = 1
DYNAMODB_EVENTUALLY_CONSISTENT_READ_TO_RRU = 1.5
DYNAMODB_WRU_COST = 1.25e-6
DYNAMODB_RRU_COST = 2.5e-7


class ApiCostCalculator(base.BaseCostCalculator):
	"""Includes API Gateway, DynamoDB, ECR, and S3."""

	def __init__(
			self,
			use_s3: bool = True,
			monthly_code_uploads: IntOrFloat = 1,
			monthly_node_creations: IntOrFloat = 5,
			monthly_node_deletions: IntOrFloat = 0,
			existing_nodes: IntOrFloat = 0,
			code_upload_in_mb: IntOrFloat = 128,
			existing_code_in_mb: IntOrFloat = 0,
			code_metadata_in_kb: IntOrFloat = 2,
			node_metadata_in_kb: IntOrFloat = 8):
		super().__init__()
		self.verify_code_uploads(monthly_code_uploads)
		self.verify_node_creations(monthly_node_creations)
		self.verify_node_deletions(monthly_node_deletions)
		self.verify_existing_nodes(existing_nodes)
		self.verify_code_upload(code_upload_in_mb)
		self.verify_existing_code(existing_code_in_mb)
		self.verify_code_metadata(code_metadata_in_kb)
		self.verify_node_metadata(node_metadata_in_kb)
		self.use_s3 = use_s3
		self.monthly_code_uploads = monthly_code_uploads
		self.monthly_node_creations = monthly_node_creations
		self.monthly_node_deletions = monthly_node_deletions
		self.existing_nodes = existing_nodes
		self.code_upload_in_mb = code_upload_in_mb
		self.existing_code_in_mb = existing_code_in_mb
		self.code_metadata_in_kb = code_metadata_in_kb
		self.node_metadata_in_kb = node_metadata_in_kb

	@staticmethod
	def verify_code_uploads(monthly_code_uploads):
		return util.verify_in_bounds(
			'monthly_code_uploads',
			monthly_code_uploads,
			MIN_MONTHLY_CODE_UPLOADS,
			MAX_MONTHLY_CODE_UPLOADS)

	@staticmethod
	def verify_node_creations(monthly_node_creations):
		return util.verify_in_bounds(
			'monthly_node_creations',
			monthly_node_creations,
			MIN_NODE_CREATIONS,
			MAX_NODE_CREATIONS)

	@staticmethod
	def verify_node_deletions(monthly_node_deletions):
		return util.verify_in_bounds(
			'monthly_node_deletions',
			monthly_node_deletions,
			MIN_NODE_DELETIONS,
			MAX_NODE_DELETIONS)

	@staticmethod
	def verify_existing_nodes(existing_nodes):
		return util.verify_in_bounds(
			'existing_nodes', existing_nodes, MIN_NODES, MAX_NODES)

	@staticmethod
	def verify_code_upload(code_upload_in_mb):
		return util.verify_in_bounds(
			'code_upload_in_mb',
			code_upload_in_mb,
			MIN_CODE_SIZE_IN_MB,
			MAX_CODE_SIZE_IN_MB)

	@staticmethod
	def verify_existing_code(existing_code_in_mb):
		return util.verify_in_bounds(
			'existing_code_in_mb',
			existing_code_in_mb,
			MIN_EXISTING_CODE_IN_MB,
			MAX_EXISTING_CODE_IN_MB)

	@staticmethod
	def verify_code_metadata(code_metadata_in_kb):
		return util.verify_in_bounds(
			'code_metadata_in_kb',
			code_metadata_in_kb,
			MIN_CODE_METADATA_IN_KB,
			MAX_CODE_METADATA_IN_KB)

	@staticmethod
	def verify_node_metadata(node_metadata_in_kb):
		return util.verify_in_bounds(
			'node_metadata_in_kb',
			node_metadata_in_kb,
			MIN_NODE_METADATA_IN_KB,
			MAX_NODE_METADATA_IN_KB)

	def calculate_cost(self):
		api_gateway = self.api_gateway()
		dynamodb = self.dynamodb()
		code_storage = self.s3() if self.use_s3 else self.ecr()
		return api_gateway + dynamodb + code_storage

	# noinspection PyTypeChecker
	def api_gateway(self):
		total_requests = self.total_api_requests()
		n_below = min(3e8, total_requests)
		n_above = max(0, total_requests - 3e8)
		return (n_below * 1e-6) + (n_above * 1e-7)

	def total_api_requests(self):
		return sum((
			self.monthly_node_creations,
			self.monthly_node_deletions,
			self.monthly_code_uploads))

	def dynamodb(self):
		read_cost = self.dynamodb_read_cost()
		write_cost = self.dynamodb_write_cost()
		backup_and_restore_cost = self.backup_and_restore_cost()
		return read_cost + write_cost + backup_and_restore_cost

	def dynamodb_read_cost(self):
		rru = self.monthly_dynamodb_rru()
		return rru * DYNAMODB_RRU_COST

	def dynamodb_write_cost(self):
		wru = self.monthly_dynamodb_wru()
		return wru * DYNAMODB_WRU_COST

	def backup_and_restore_cost(self):
		table_size = self.table_size_in_gb()
		return table_size * DYNAMODB_STORAGE_COST_PER_GB

	def table_size_in_gb(self):
		return util.kb_to_gb(self.existing_nodes * self.node_metadata_in_kb)

	def monthly_dynamodb_rru(self):
		create = self.monthly_node_creations * self.node_metadata_in_kb
		delete = self.monthly_node_deletions * self.node_metadata_in_kb
		total = create + delete
		reads = total / DYNAMODB_EVENTUALLY_CONSISTENT_READ_IN_KB
		return reads * DYNAMODB_EVENTUALLY_CONSISTENT_READ_TO_RRU

	def monthly_dynamodb_wru(self):
		create = self.dynamodb_create_data_in_kb()
		upload = self.dynamodb_upload_data_in_kb()
		total = create + upload
		writes = total * DYNAMODB_EVENTUALLY_CONSISTENT_WRITE_IN_KB
		return writes * DYNAMODB_EVENTUALLY_CONSISTENT_WRITE_TO_WRU

	def dynamodb_create_data_in_kb(self):
		return self.monthly_node_creations * self.node_metadata_in_kb

	def dynamodb_delete_data_in_kb(self):
		return self.monthly_node_deletions * self.node_metadata_in_kb

	def dynamodb_upload_data_in_kb(self):
		uploads = self.existing_nodes * self.monthly_code_uploads
		return self.code_metadata_in_kb * uploads

	def ecr(self):
		total = util.mb_to_gb(self.total_code_in_mb())
		return total * ECR_STORAGE_COST_PER_GB

	def s3(self):
		request_cost = self.s3_request_cost()
		storage_cost = self.s3_storage_cost()
		return request_cost + storage_cost

	def s3_request_cost(self):
		get_cost = self.s3_get_request_cost()
		put_cost = self.s3_put_request_cost()
		return get_cost + put_cost

	def s3_get_request_cost(self):
		return self.monthly_node_creations * S3_GET_REQUEST_COST

	def s3_put_request_cost(self):
		return self.monthly_code_uploads * S3_PUT_REQUEST_COST

	def s3_storage_cost(self):
		total = util.mb_to_gb(self.total_code_in_mb())
		if total > 5e14:
			cost = total * 0.021
		elif 5e13 <= total <= 5e14:
			cost = total * 0.022
		else:
			cost = total * 0.023
		return cost

	def total_code_in_mb(self):
		new_code = self.new_monthly_code_in_mb()
		return self.existing_code_in_mb + new_code

	def new_monthly_code_in_mb(self):
		return self.monthly_code_uploads * self.code_upload_in_mb

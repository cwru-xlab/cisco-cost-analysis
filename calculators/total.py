from . import api, base, node
from .util import IntOrFloat


class TotalCostCalculator(base.BaseCostCalculator):

	def __init__(
			self,
			users: float = 100,
			msg_size_in_kb: IntOrFloat = 64,
			msg_processing_in_secs: IntOrFloat = 1,
			polling_in_secs: IntOrFloat = 1,
			batch_size: IntOrFloat = 1,
			batch_window_in_secs: IntOrFloat = 1,
			msgs_received_per_min: IntOrFloat = 1,
			concurrency: IntOrFloat = 5,
			function_memory_in_mb: IntOrFloat = 128,
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
		self.api = api.ApiCostCalculator(
			use_s3=use_s3,
			monthly_code_uploads=monthly_code_uploads,
			monthly_node_creations=monthly_node_creations,
			monthly_node_deletions=monthly_node_deletions,
			existing_nodes=existing_nodes,
			code_upload_in_mb=code_upload_in_mb,
			existing_code_in_mb=existing_code_in_mb,
			code_metadata_in_kb=code_metadata_in_kb,
			node_metadata_in_kb=node_metadata_in_kb)
		self.node = node.NodeCostCalculator(
			users=users,
			msg_size_in_kb=msg_size_in_kb,
			msg_processing_in_secs=msg_processing_in_secs,
			polling_in_secs=polling_in_secs,
			batch_size=batch_size,
			batch_window_in_secs=batch_window_in_secs,
			msgs_received_per_min=msgs_received_per_min,
			concurrency=concurrency,
			function_memory_in_mb=function_memory_in_mb)

	def calculate_cost(self):
		api_cost = self.api.calculate_cost()
		node_cost = self.node.calculate_cost()
		return api_cost + node_cost

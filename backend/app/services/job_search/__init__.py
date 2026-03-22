"""
多源职位列表聚合：Boss / 智联 / 鱼泡。
"""

from app.services.job_search.aggregator import aggregate_jobs

__all__ = ["aggregate_jobs"]

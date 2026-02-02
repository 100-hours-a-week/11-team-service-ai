from dataclasses import dataclass
from typing import List
from job_analysis.data.models import JobPost, JobMaster, Company


@dataclass
class JobPostingWithRelations:
    """중복 URL 처리용 DTO - 모든 관련 데이터를 포함"""

    job_post: JobPost
    job_master: JobMaster
    company: Company
    skills: List[str]

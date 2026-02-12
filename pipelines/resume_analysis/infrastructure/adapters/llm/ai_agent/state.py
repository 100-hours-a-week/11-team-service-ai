import operator
from typing import Annotated, List
from typing_extensions import TypedDict
from .....domain.models.report import SectionAnalysis


class AnalysisState(TypedDict):
    section_analyses: Annotated[List[SectionAnalysis], operator.add]
    overall_review: str

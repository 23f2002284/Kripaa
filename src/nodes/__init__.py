"""
LangGraph nodes for the Kripaa exam generation pipeline.
Each node is in its own file for modularity.
"""
from src.nodes.ocr_nodes import ocr_pyqs_node, ocr_syllabus_node
from src.nodes.normalization_node import normalization_node
from src.nodes.variant_detection_node import variant_detection_node
from src.nodes.syllabus_mapping_node import syllabus_mapping_node
from src.nodes.trend_analysis_node import trend_analysis_node
from src.nodes.question_generation_node import question_generation_node
from src.nodes.voting_node import voting_node
from src.nodes.paper_generation_node import paper_generation_node
from src.nodes.report_generation_node import report_generation_node

__all__ = [
    "ocr_pyqs_node",
    "ocr_syllabus_node",
    "normalization_node",
    "variant_detection_node",
    "syllabus_mapping_node",
    "trend_analysis_node",
    "question_generation_node",
    "voting_node",
    "paper_generation_node",
    "report_generation_node"
]

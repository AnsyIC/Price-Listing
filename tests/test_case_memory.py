from pathlib import Path
import os
import sys

# Add workspace root to path (consistent with other tests)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflow_util.case_memory.build_casebank import build_casebank
from workflow_util.case_memory.retriever import CaseRetriever
from workflow_util.case_memory.prompt_format import build_reference_block


def test_casebank_build_and_retrieve_heart_infarct(tmp_path: Path):
    # Build casebank from the checked-in human verified reports
    out_path = tmp_path / "casebank.jsonl"
    build_casebank(Path("workflow_data/pricing_reports"), out_path)

    retriever = CaseRetriever(out_path)
    results = retriever.retrieve("大鼠 心梗 模型 40只 超声 取材", top_k=1)
    assert results

    case_id = results[0].case.get("case_id", "")
    assert "心梗" in case_id


def test_reference_block_contains_rules(tmp_path: Path):
    out_path = tmp_path / "casebank.jsonl"
    build_casebank(Path("workflow_data/pricing_reports"), out_path)

    retriever = CaseRetriever(out_path)
    results = retriever.retrieve("小鼠 寄养 换水 称重", top_k=2)

    block = build_reference_block([r.case for r in results])
    assert "REFERENCE CASES" in block
    assert "DO NOT copy" in block or "DO NOT copy".lower() in block.lower()

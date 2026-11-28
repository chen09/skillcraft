"""Candidate MEM-004 r2: personal original-preservation contract; no business acceptance."""
import argparse,pathlib,json,re,hashlib
PHASES=["阶段一","阶段二","阶段三","阶段四","阶段五","阶段六","阶段七","阶段八"]
OUTPUTS=["00_GPT可点击回执.md","01_人类总览.html","02_自我蒸馏总报告.md","03_证据索引.md","04_重复工作流候选清单.md","05_skill触发失败审计.md","06_worker_subagent机制审计.md","07_产物质量与偷懒模式诊断.md","08_能力升级优先级矩阵.md","09_AGENTS_md_patch_candidate.md","10_skill_patch_candidates/","11_new_skill_candidates/","12_worker_subagent_candidates/","13_goal_longrun_candidates/","14_validators/","15_real_or_semireal_validation/","16_installation_plan_and_rollback.md","17_NEXT_CODEX_PROMPT_二轮执行或安装指令.md","99_receipts/GPT_HANDOFF_FULL_CONTEXT_CODEX_SELF_DISTILLATION_UNIVERSAL_V1.md","99_receipts/FINAL_RECEIPT.md"]
FENCE=chr(96)*3
def evaluate(text,original,expected_source_sha256):
 blocks=re.findall(r"(?m)^"+FENCE+r"text\n([\s\S]*?)\n"+FENCE+r"[ \t]*(?:\n|$)",text)
 exact=sum(x==original for x in blocks);phases=[p for p in PHASES if p in text]
 flat=re.sub(r"\s+","",text);names=[p for p in OUTPUTS if p in flat]
 checks={"trusted_nonempty_source":bool(original.strip()) and hashlib.sha256(original.encode()).hexdigest()==expected_source_sha256,"exact_original_once":exact==1 and bool(original) and text.count(original)==1,"retained_eight_phase_markers":len(phases)==8,"retained_twenty_output_name_markers":len(names)==20,"periodic_full_cycle":bool(re.search(r"每\s*(?:两到三周|两周|2[～~—–-]3\s*周|2～3\s*周)",text)),"p0_real_or_semireal":("P0" in text and any(x in text for x in ["半真实","真实或","real_execution"]))}
 score=40*checks["exact_original_once"]+25*len(phases)/8+20*len(names)/20+10*checks["periodic_full_cycle"]+5*checks["p0_real_or_semireal"]
 return {"validator_mode":"deterministic_preservation_contract_not_business_acceptance","passed":all(checks.values()),"score":round(score,2),"checks":checks,"source_sha256":hashlib.sha256(original.encode()).hexdigest(),"missing_phases":[x for x in PHASES if x not in phases],"missing_outputs":[x for x in OUTPUTS if x not in names],"repair_tasks":[k for k,v in checks.items() if not v],"business_accepted":False,"installed":False,"marker_coverage_is_execution":False,"limitation":"Pass proves this preservation contract only. It does not execute business stages, install skills, or verify future triggering."}
def package(root):
 r=pathlib.Path(root);missing=[]
 for p in OUTPUTS:
  f=r/p
  if not f.exists() or (f.is_file() and not f.stat().st_size) or (f.is_dir() and not any(x.is_file() for x in f.rglob("*"))):missing.append(p)
 return {"passed":not missing,"missing_or_empty":missing,"mode":"structure_only_not_substantive_acceptance"}
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("input");a.add_argument("--source",required=True);a.add_argument("--package");a.add_argument("--require-package",action="store_true");a.add_argument("--expected-source-sha256",required=True);x=a.parse_args()
 r=evaluate(pathlib.Path(x.input).read_text(encoding="utf-8"),pathlib.Path(x.source).read_text(encoding="utf-8"),x.expected_source_sha256)
 if x.require_package and not x.package:
  r["passed"]=False;r["repair_tasks"].append("actual_package_required_for_completed_cycle_claim")
 if x.package:r["package_structure"]=package(x.package);r["passed"]=r["passed"] and r["package_structure"]["passed"]
 print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r["passed"] else 1)


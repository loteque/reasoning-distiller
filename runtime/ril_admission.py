#!/usr/bin/env python3
from __future__ import annotations

import copy, hashlib, json, os
from pathlib import Path
from typing import Any
from rd_bootstrap import validate_project_config
from ril_activation import validate_activation
from ril_canonical_store import exclusive_canonical_store
from ril_mutation import ContractError, canonical_json_bytes, digest, load_json
from ril_reconciliation import DISPOSITION_CONTRACT

RESULT_CONTRACT="reasoning-distiller-admission-result/1"; RECEIPT_CONTRACT="reasoning-distiller-admission-receipt/1"
PLAN_CONTRACT="rgp-pems2-admission-transaction/2"; PROFILE="pems/2"; COVE="cove/1"; SERIALIZER="jcs/1"; SCOPE="admission"
EMPTY_PEMS={"semantic":PROFILE,"records":[],"relations":[]}

def _result(status:str,outcome:str,detail:str|None=None,**extra:Any)->dict[str,Any]:
    v={"contract":RESULT_CONTRACT,"status":status,"outcome":outcome};
    if detail:v["detail"]=detail
    v.update(extra); return v

def jcs(v:Any)->bytes:
    try:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
    except (TypeError,ValueError) as e:raise ContractError("NON_CANONICAL_VALUE",str(e)) from e

def sha256_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def normalize_pems(d:dict[str,Any])->dict[str,Any]:
    if not isinstance(d,dict) or d.get("semantic")!=PROFILE or not isinstance(d.get("records"),list) or not isinstance(d.get("relations"),list):raise ContractError("INVALID_PEMS","document must be pems/2 with records/relations arrays")
    x=copy.deepcopy(d)
    try:x["records"]=sorted(x["records"],key=lambda r:r["id"]); x["relations"]=sorted(x["relations"],key=lambda r:r["id"])
    except Exception as e:raise ContractError("INVALID_PEMS","all records and relations require IDs") from e
    return x

def first_admission_base(project_root:Path)->dict[str,Any]:
    config_path=project_root/"project-knowledge/project.json"
    if not config_path.exists() or config_path.is_symlink() or not config_path.is_file():raise ContractError("PROJECT_IDENTITY_REQUIRED","project-knowledge/project.json with explicit project identity is required")
    config=load_json(config_path)
    if not validate_project_config(config):raise ContractError("PROJECT_IDENTITY_REQUIRED","reasoning-distiller-project/2 identity is required before first admission")
    project=config["project"]
    return normalize_pems({"semantic":PROFILE,"project_id":project["id"],"records":[{"id":project["id"],"kind":"project","lifecycle":"current","data":{"name":project["name"],"repository":project["repository"],"summary":project["summary"]}}],"relations":[]})

def _validate_graph(d:dict[str,Any])->None:
    rs=[r.get("id") for r in d["records"]]; ls=[r.get("id") for r in d["relations"]]
    if any(not isinstance(x,str) or not x for x in rs+ls):raise ContractError("INVALID_PEMS","IDs must be non-empty strings")
    if len(rs)!=len(set(rs)):raise ContractError("DUPLICATE_RECORD_ID","record IDs must be unique")
    if len(ls)!=len(set(ls)):raise ContractError("DUPLICATE_RELATION_ID","relation IDs must be unique")
    known=set(rs)
    for r in d["relations"]:
        if r.get("from") not in known or r.get("to") not in known:raise ContractError("DANGLING_RELATION",str(r.get("id")))
        if r.get("from")==r.get("to"):raise ContractError("SELF_RELATION",str(r.get("id")))

def _strings(v:Any,o:set[str])->None:
    if isinstance(v,str):o.add(v)
    elif isinstance(v,list):
        for x in v:_strings(x,o)
    elif isinstance(v,dict):
        for k,x in v.items():o.add(k);_strings(x,o)

def _shapes(v:Any,i:dict[str,int],o:set[tuple[int,...]])->None:
    if isinstance(v,list):
        for x in v:_shapes(x,i,o)
    elif isinstance(v,dict):
        o.add(tuple(sorted(i[k] for k in v)))
        for x in v.values():_shapes(x,i,o)

def _encode(v:Any,i:dict[str,int],si:dict[tuple[int,...],int])->Any:
    if isinstance(v,str):return [0,i[v]]
    if isinstance(v,list):return [1,*[_encode(x,i,si) for x in v]]
    if isinstance(v,dict):
        s=tuple(sorted(i[k] for k in v)); ks=sorted(v,key=lambda k:i[k]); return [2,si[s],*[_encode(v[k],i,si) for k in ks]]
    return v

def _decode(v:Any,d:list[str],h:list[list[int]])->Any:
    if not isinstance(v,list):return v
    if v[0]==0:return d[v[1]]
    if v[0]==1:return [_decode(x,d,h) for x in v[1:]]
    if v[0]==2:
        ks=[d[n] for n in h[v[1]]]; xs=v[2:]
        if len(ks)!=len(xs):raise ContractError("COVE_ROUNDTRIP_FAILED","shape arity mismatch")
        return {k:_decode(x,d,h) for k,x in zip(ks,xs)}
    raise ContractError("COVE_ROUNDTRIP_FAILED","unknown tag")

def encode_cove(d:dict[str,Any])->dict[str,Any]:
    ss:set[str]=set();_strings(d,ss); dictionary=sorted(ss,key=lambda x:x.encode()); idx={x:n for n,x in enumerate(dictionary)}
    sh:set[tuple[int,...]]=set();_shapes(d,idx,sh); ordered=sorted(sh); si={x:n for n,x in enumerate(ordered)}
    return {"c":COVE,"p":PROFILE,"s":SERIALIZER,"d":dictionary,"h":[list(x) for x in ordered],"x":_encode(d,idx,si)}

def validate_plan(p:Any)->dict[str,Any]:
    req={"contract","expected_base_sha256","reuse_record_ids","record_updates","new_records","new_relations"}
    if not isinstance(p,dict) or set(p)!=req or p.get("contract")!=PLAN_CONTRACT:raise ContractError("INVALID_ADMISSION_PLAN","plan contract/fields invalid")
    if not isinstance(p["expected_base_sha256"],str) or len(p["expected_base_sha256"])!=64:raise ContractError("INVALID_ADMISSION_PLAN","expected_base_sha256 invalid")
    for k in ("reuse_record_ids","record_updates","new_records","new_relations"):
        if not isinstance(p[k],list):raise ContractError("INVALID_ADMISSION_PLAN",f"{k} must be array")
    return copy.deepcopy(p)

def apply_plan(base:dict[str,Any],plan:dict[str,Any])->dict[str,Any]:
    base=normalize_pems(base); p=validate_plan(plan)
    if sha256_bytes(jcs(base))!=p["expected_base_sha256"]:raise ContractError("BASE_MISMATCH","plan not built against current canonical PEMS")
    records={r["id"]:r for r in base["records"]}; rels={r["id"]:r for r in base["relations"]}; reuse=p["reuse_record_ids"]
    if len(reuse)!=len(set(reuse)):raise ContractError("INVALID_ADMISSION_PLAN","duplicate reuse IDs")
    for rid in reuse:
        if rid not in records:raise ContractError("REUSED_RECORD_NOT_FOUND",str(rid))
    repl={}; seen=set()
    for u in p["record_updates"]:
        if not isinstance(u,dict) or set(u)!={"record_id","expected_before_sha256","replacement"}:raise ContractError("INVALID_RECORD_UPDATE","invalid update shape")
        rid=u["record_id"]; r=u["replacement"]
        if rid in seen or rid not in records or rid not in reuse or not isinstance(r,dict) or r.get("id")!=rid or r.get("kind")!=records[rid].get("kind"):raise ContractError("INVALID_RECORD_UPDATE",str(rid))
        if sha256_bytes(jcs(records[rid]))!=u["expected_before_sha256"]:raise ContractError("RECORD_BEFORE_MISMATCH",str(rid))
        seen.add(rid); repl[rid]=copy.deepcopy(r)
    newr=[]; ids=set()
    for r in p["new_records"]:
        rid=r.get("id") if isinstance(r,dict) else None
        if not isinstance(rid,str) or not rid:raise ContractError("INVALID_NEW_RECORD","id required")
        if rid in records or rid in ids:raise ContractError("RECORD_ID_COLLISION",rid)
        ids.add(rid);newr.append(copy.deepcopy(r))
    newl=[]; lids=set()
    for r in p["new_relations"]:
        rid=r.get("id") if isinstance(r,dict) else None
        if not isinstance(rid,str) or not rid:raise ContractError("INVALID_NEW_RELATION","id required")
        if rid in rels or rid in lids:raise ContractError("RELATION_ID_COLLISION",rid)
        lids.add(rid);newl.append(copy.deepcopy(r))
    out=copy.deepcopy(base);out["records"]=[copy.deepcopy(repl.get(r["id"],r)) for r in base["records"]]+newr;out["relations"]=copy.deepcopy(base["relations"])+newl
    out=normalize_pems(out);_validate_graph(out);return out

def _persist(path:Path,v:dict[str,Any],code:str)->None:
    data=canonical_json_bytes(v)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes()!=data:raise ContractError(code,str(path))
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        with open(path,"xb") as h:h.write(data);h.flush();os.fsync(h.fileno())
    except FileExistsError:
        if path.is_symlink() or path.read_bytes()!=data:raise ContractError(code,str(path))

def _load_disposition(root:Path,path_arg:Path)->dict[str,Any]:
    base=(root.resolve()/"project-knowledge/reconciliation/dispositions").resolve(strict=False);raw=path_arg if path_arg.is_absolute() else root/path_arg
    if raw.is_symlink():raise ContractError("INVALID_DISPOSITION_PATH",str(path_arg))
    try:path=raw.resolve(strict=True);path.relative_to(base)
    except (OSError,ValueError) as e:raise ContractError("INVALID_DISPOSITION_PATH",str(path_arg)) from e
    v=load_json(path)
    if not isinstance(v,dict) or v.get("contract")!=DISPOSITION_CONTRACT:raise ContractError("INVALID_DISPOSITION","unsupported disposition")
    a=v.get("assessment",{})
    if a.get("semantic_status")!="COMPATIBLE" or a.get("admission_recommendation")!="RECOMMEND":raise ContractError("ADMISSION_NOT_RECOMMENDED","disposition does not recommend admission")
    cand=load_json(root/v["candidate_path"])
    if digest(cand)!=v.get("candidate_digest"):raise ContractError("CANDIDATE_CHANGED","candidate no longer matches reconciled identity")
    return v

def admit(project_root:Path,disposition_path:Path,activation:dict[str,Any],plan:dict[str,Any])->dict[str,Any]:
    try:
        disposition=_load_disposition(project_root,disposition_path); ar=validate_activation(project_root,SCOPE,activation)
        if ar.get("status")!="PASS":return _result("FAIL",ar.get("outcome","ACTIVATION_REJECTED"),ar.get("detail"))
        validate_plan(plan); activation_digest=digest(activation); plan_digest=digest(plan); candidate_hex=disposition["candidate_digest"].split(":",1)[1]
        admission=project_root/"project-knowledge/admission"; receipt_path=admission/"receipts"/f"{candidate_hex}.json"
        with exclusive_canonical_store(project_root) as store:
            snapshot=store.snapshot()
            # Idempotent retry is recognized from immutable evidence before stale-base evaluation.
            if receipt_path.exists():
                rec=load_json(receipt_path)
                if rec.get("contract")!=RECEIPT_CONTRACT or rec.get("candidate_digest")!=disposition["candidate_digest"] or rec.get("disposition_digest")!=digest(disposition) or rec.get("activation_digest")!=activation_digest or rec.get("plan_digest")!=plan_digest:raise ContractError("ADMISSION_CONFLICT","candidate already admitted under different evidence")
                if snapshot.state!="PRESENT" or snapshot.pems_sha256!=rec.get("admitted_pems_sha256") or snapshot.cove_sha256!=rec.get("admitted_cove_sha256"):raise ContractError("CANONICAL_STATE_CONFLICT","receipt does not match canonical bytes")
                return _result("PASS","NO_CHANGE",receipt_path=receipt_path.relative_to(project_root).as_posix(),admitted_pems_sha256=rec["admitted_pems_sha256"])
            if snapshot.state=="INCOMPLETE":raise ContractError("INCOMPLETE_CANONICAL_PAIR","ordinary admission requires an absent or complete canonical pair")
            if snapshot.state=="PRESENT":
                from ril_storage_verification import verify_storage_snapshot
                standing=verify_storage_snapshot(project_root,Path(__file__).resolve().parents[1],snapshot)
                if standing.get("status")!="PASS" or standing.get("outcome") not in {"VERIFIED_ADMITTED","VERIFIED_RECOVERED"}:
                    raise ContractError(str(standing.get("outcome","CANONICAL_STATE_CONFLICT")),str(standing.get("detail","current canonical base lacks valid R14 V2 standing")))
                assert snapshot.pems_bytes is not None
                base=normalize_pems(json.loads(snapshot.pems_bytes.decode("utf-8")))
            else:
                base=first_admission_base(project_root)
            candidate=apply_plan(base,plan); pb=jcs(candidate); cove=encode_cove(candidate); cb=jcs(cove)
            if _decode(cove["x"],cove["d"],cove["h"])!=candidate:raise ContractError("COVE_ROUNDTRIP_FAILED","COVE does not decode to PEMS")
            receipt={"contract":RECEIPT_CONTRACT,"candidate_digest":disposition["candidate_digest"],"disposition_digest":digest(disposition),"activation_digest":activation_digest,"plan_digest":plan_digest,"role_id":ar["role_id"],"invocation_id":ar["invocation_id"],"base_pems_sha256":sha256_bytes(jcs(base)),"admitted_pems_sha256":sha256_bytes(pb),"admitted_cove_sha256":sha256_bytes(cb)}
            _persist(admission/"activation-evidence"/f"{activation_digest.split(':',1)[1]}.json",activation,"ACTIVATION_EVIDENCE_CONFLICT");_persist(admission/"plans"/f"{plan_digest.split(':',1)[1]}.json",plan,"ADMISSION_PLAN_CONFLICT")
            published=store.publish_pair(pb,cb)
            if published.pems_sha256!=receipt["admitted_pems_sha256"] or published.cove_sha256!=receipt["admitted_cove_sha256"]:raise ContractError("CANONICAL_STATE_CONFLICT","published canonical pair digest mismatch")
            _persist(receipt_path,receipt,"ADMISSION_CONFLICT")
            return _result("PASS","ADMITTED",receipt_path=receipt_path.relative_to(project_root).as_posix(),pems_path=store.pems_path.relative_to(project_root).as_posix(),cove_path=store.cove_path.relative_to(project_root).as_posix(),admitted_pems_sha256=receipt["admitted_pems_sha256"],admitted_cove_sha256=receipt["admitted_cove_sha256"])
    except (ContractError,json.JSONDecodeError,UnicodeDecodeError,OSError) as e:
        return _result("FAIL",e.code,e.detail) if isinstance(e,ContractError) else _result("FAIL","ADMISSION_IO_ERROR",str(e))

if __name__=="__main__":print(json.dumps(_result("FAIL","LIBRARY_PRIMITIVE","R13 is exposed as deterministic functions; public ril UX is not implemented yet"),sort_keys=True,separators=(",",":")))

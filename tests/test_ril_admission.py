from __future__ import annotations
import json, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"runtime"))
from ril_activation import make_explicit_activation
from ril_admission import EMPTY_PEMS, PLAN_CONTRACT, _decode, admit, jcs, sha256_bytes
from ril_mutation import canonical_json_bytes
from ril_operators import apply_initial_operator, approve_initial_operator, plan_initial_operator
from ril_reconciliation import ASSESSMENT_CONTRACT, reconcile_candidate
from ril_steward_authorization import apply_authorization_change, approve_authorization_change, plan_authorization_change

class AdmissionR13Tests(unittest.TestCase):
    def root(self)->Path:
        r=Path(tempfile.mkdtemp());(r/"project-knowledge/submissions").mkdir(parents=True);return r
    def establish(self,r:Path)->None:
        p=plan_initial_operator(r,"operator:owner");a=approve_initial_operator(p["proposal"],"operator:owner");self.assertEqual(apply_initial_operator(r,p["proposal"],a)["status"],"PASS")
    def auth(self,r:Path,scope:str)->None:
        p=plan_authorization_change(r,"AUTHORIZE",scope,"steward:default");a=approve_authorization_change(p["proposal"],"operator:owner");self.assertEqual(apply_authorization_change(r,p["proposal"],a)["status"],"PASS")
    def ready(self,recommendation:str="RECOMMEND"):
        r=self.root();self.establish(r);self.auth(r,"semantic_reconciliation")
        c=r/"project-knowledge/submissions/candidate.json";c.write_bytes(canonical_json_bytes({"contract":"test-candidate/1","claim":"x"}))
        ra=make_explicit_activation("steward:default","invocation:reconcile","test")
        assessment={"contract":ASSESSMENT_CONTRACT,"semantic_status":"COMPATIBLE","admission_recommendation":recommendation,"rationale":"reviewed"}
        rr=reconcile_candidate(r,c,ra,assessment);self.assertEqual(rr["status"],"PASS")
        return r,c,Path(rr["disposition_path"])
    def plan(self,base=EMPTY_PEMS,record_id="record:1"):
        return {"contract":PLAN_CONTRACT,"expected_base_sha256":sha256_bytes(jcs(base)),"reuse_record_ids":[],"record_updates":[],"new_records":[{"id":record_id,"kind":"observation","data":{"value":"x"}}],"new_relations":[]}
    def activation(self):return make_explicit_activation("steward:default","invocation:admit","test")

    def test_independent_admission_authority_required(self):
        r,_,d=self.ready();res=admit(r,d,self.activation(),self.plan());self.assertEqual((res["status"],res["outcome"]),("FAIL","SCOPE_UNASSIGNED"))
    def test_recommendation_not_authority_and_defer_is_blocked(self):
        r,_,d=self.ready("DEFER");self.auth(r,"admission");res=admit(r,d,self.activation(),self.plan());self.assertEqual((res["status"],res["outcome"]),("FAIL","ADMISSION_NOT_RECOMMENDED"))
    def test_success_writes_pems_cove_and_evidence(self):
        r,_,d=self.ready();self.auth(r,"admission");res=admit(r,d,self.activation(),self.plan());self.assertEqual((res["status"],res["outcome"]),("PASS","ADMITTED"))
        p=json.loads((r/res["pems_path"]).read_text());c=json.loads((r/res["cove_path"]).read_text());self.assertEqual(_decode(c["x"],c["d"],c["h"]),p)
        self.assertEqual(len(list((r/"project-knowledge/admission/receipts").glob("*.json"))),1);self.assertEqual(len(list((r/"project-knowledge/admission/plans").glob("*.json"))),1)
    def test_exact_retry_is_no_change(self):
        r,_,d=self.ready();self.auth(r,"admission");p=self.plan();a=self.activation();self.assertEqual(admit(r,d,a,p)["outcome"],"ADMITTED");self.assertEqual(admit(r,d,a,p)["outcome"],"NO_CHANGE")
    def test_candidate_change_after_reconciliation_is_rejected(self):
        r,c,d=self.ready();self.auth(r,"admission");c.write_bytes(canonical_json_bytes({"contract":"test-candidate/1","claim":"changed"}));res=admit(r,d,self.activation(),self.plan());self.assertEqual((res["status"],res["outcome"]),("FAIL","CANDIDATE_CHANGED"))
    def test_stale_plan_is_rejected(self):
        r,_,d=self.ready();self.auth(r,"admission");(r/"project-knowledge/canonical").mkdir(parents=True);base={"semantic":"pems/2","records":[{"id":"existing","kind":"observation","data":{}}],"relations":[]};(r/"project-knowledge/canonical/pems2.jcs.json").write_bytes(jcs(base));res=admit(r,d,self.activation(),self.plan());self.assertEqual((res["status"],res["outcome"]),("FAIL","BASE_MISMATCH"))
    def test_record_collision_is_rejected(self):
        r,_,d=self.ready();self.auth(r,"admission");base={"semantic":"pems/2","records":[{"id":"record:1","kind":"observation","data":{}}],"relations":[]};canon=r/"project-knowledge/canonical";canon.mkdir(parents=True);(canon/"pems2.jcs.json").write_bytes(jcs(base));p=self.plan(base,"record:1");res=admit(r,d,self.activation(),p);self.assertEqual((res["status"],res["outcome"]),("FAIL","RECORD_ID_COLLISION"))
    def test_guarded_update_checks_before_state_and_kind(self):
        r,_,d=self.ready();self.auth(r,"admission");base={"semantic":"pems/2","records":[{"id":"record:1","kind":"observation","data":{"value":"old"}}],"relations":[]};canon=r/"project-knowledge/canonical";canon.mkdir(parents=True);(canon/"pems2.jcs.json").write_bytes(jcs(base))
        p={"contract":PLAN_CONTRACT,"expected_base_sha256":sha256_bytes(jcs(base)),"reuse_record_ids":["record:1"],"record_updates":[{"record_id":"record:1","expected_before_sha256":"0"*64,"replacement":{"id":"record:1","kind":"observation","data":{"value":"new"}}}],"new_records":[],"new_relations":[]};res=admit(r,d,self.activation(),p);self.assertEqual(res["outcome"],"RECORD_BEFORE_MISMATCH")
    def test_conflicting_second_admission_is_rejected(self):
        r,_,d=self.ready();self.auth(r,"admission");a=self.activation();p=self.plan();self.assertEqual(admit(r,d,a,p)["outcome"],"ADMITTED");changed=dict(p);changed["new_records"]=[{"id":"record:2","kind":"observation","data":{"value":"y"}}];res=admit(r,d,a,changed);self.assertEqual((res["status"],res["outcome"]),("FAIL","ADMISSION_CONFLICT"))

if __name__=="__main__":unittest.main()

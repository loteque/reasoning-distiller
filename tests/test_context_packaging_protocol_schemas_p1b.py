import json,unittest
from copy import deepcopy
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry,Resource
R=Path(__file__).resolve().parents[1]; S=R/'schemas'; F=R/'tests/fixtures/context-packaging-protocol-schema-p1b.json'; P0=R/'tests/fixtures/context-packaging-pressure-cases-v1.json'; PEMS=R/'backends/pems-cove/pems-v2.schema.json'
FILES=['context-profile.schema.json','context-pack-request.schema.json','context-pack.schema.json','context-pack-result.schema.json','context-pack-failure.schema.json','context-profile-eligibility.schema.json','context-source-binding.schema.json','context-pack-receipt.schema.json']
def load(p):return json.loads(p.read_text())
def lr(b):return {k:b[k] for k in ('source_class','logical_namespace','logical_source_id')}
def sr(b):
 ks={'repository_control':('source_class','logical_namespace','logical_source_id','repository','commit','path','raw_sha256'),'canonical_state':('source_class','logical_namespace','logical_source_id','project_id','backend_type','backend_contract','backend_config_identity','immutable_snapshot_id','pems_semantic','serializer','pems_sha256','cove','standing_evidence'),'operational_evidence':('source_class','logical_namespace','logical_source_id','artifact_contract','immutable_snapshot_id','raw_sha256','validation_status','validation_result')}[b['source_class']]
 return {k:deepcopy(b[k]) for k in ks if k in b}
def mut(v,m):
 v=deepcopy(v);t=v
 for p in m['path']:t=t[p]
 if 'delete_field'in m:t.pop(m['delete_field'],None)
 else:t[m['field']]=deepcopy(m['value'])
 return v
def objects(x):
 if isinstance(x,dict):
  if x.get('type')=='object':yield x
  for v in x.values():yield from objects(v)
 elif isinstance(x,list):
  for v in x:yield from objects(v)
def classify(c,errs):
 assert errs
 t,m=c['target'],c['mutation'];p,f=m['path'],m.get('field')
 if t in ('failure','result_success'):return 'INVALID_REQUEST'
 if t=='repository_source' and f=='source_class':return 'UNSUPPORTED_SOURCE_CLASS'
 if t=='operational_source':return 'OPERATIONAL_EVIDENCE_IDENTITY_INVALID'
 if t=='request' and p[:1]==['slot_bindings']:return 'PLANE_CLASSIFICATION_CONFLICT'
 if t=='request' and p[:2]==['knowledge_selection','snapshots']:return 'SOURCE_IDENTITY_INVALID'
 if t=='pack' and p[:2]==['control_plane','items']:return 'PLANE_CLASSIFICATION_CONFLICT'
 if t=='pack' and p[:2]==['knowledge_plane','items']:return 'SOURCE_IDENTITY_INVALID'
 if t=='profile' and f=='required':return 'INVALID_PROFILE'
 return 'UNKNOWN_SEMANTICS_FIELD'
class P1b(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.sc={n:load(S/n)for n in FILES};c.fx=load(F);c.p0=load(P0);p=load(PEMS);reg=Registry().with_resources([(x['$id'],Resource.from_contents(x))for x in[*c.sc.values(),p]]);c.v={n:Draft202012Validator(x,registry=reg)for n,x in c.sc.items()};c.e=c.fx['examples'];c.reg=reg
 def val(s,n,x):return list(s.v[n].iter_errors(x))
 def sub(s,n,d,x):return list(Draft202012Validator(s.sc[n]['$defs'][d],registry=s.reg).iter_errors(x))
 def test_inventory_meta_and_closed_world(s):
  s.assertEqual({x['file']for x in s.fx['schemas']},set(FILES));s.assertEqual(s.fx['scope']['authorized'],'P1B_PROTOCOL_SCHEMAS_ONLY');s.assertFalse(s.fx['scope']['resolver_implemented']or s.fx['scope']['later_gates_implemented']or s.fx['scope']['production_integration_authorized'])
  for n,x in s.sc.items():Draft202012Validator.check_schema(x);[s.assertIs(o.get('additionalProperties'),False,n)for o in objects(x)]
 def test_positive_examples(s):
  for k in('repository_source','package_source','canonical_source','canonical_source_second','operational_source'):s.assertFalse(s.val('context-source-binding.schema.json',s.e[k]),k)
  for k,n in(('profile','context-profile.schema.json'),('eligibility','context-profile-eligibility.schema.json'),('failure','context-pack-failure.schema.json'),('receipt','context-pack-receipt.schema.json')):s.assertFalse(s.val(n,s.e[k]),k)
 def test_p1a_multi_snapshot_is_separately_addressable(s):
  c=s.fx['p1a_crossing_multi_snapshot_cases'][0];s.assertEqual(c['p1a_case_ids'],['SI-10','SI-40']);a,b=c['source_bindings'];r0,r1=c['snapshot_refs'];s.assertEqual(lr(a),lr(b));s.assertNotEqual(r0,r1);s.assertEqual([r0,r1],[sr(a),sr(b)])
  for r in(r0,r1):s.assertFalse(s.sub('context-source-binding.schema.json','canonicalSnapshotRef',r))
  s.assertTrue(s.sub('context-source-binding.schema.json','canonicalSnapshotRef',c['logical_source_ref']))
  rq=s.sc['context-pack-request.schema.json'];pk=s.sc['context-pack.schema.json'];s.assertEqual(rq['$defs']['knowledgeSnapshotSelection']['properties']['canonical_snapshot_ref']['$ref'],'https://reasoning-distiller.local/schemas/context-source-binding.schema.json#/$defs/canonicalSnapshotRef');s.assertEqual(pk['$defs']['knowledgeItem']['properties']['canonical_snapshot_ref']['$ref'],'https://reasoning-distiller.local/schemas/context-source-binding.schema.json#/$defs/canonicalSnapshotRef')
 def test_negative_fixtures_reject_and_classify_exactly(s):
  e=s.e;repo=e['repository_source'];can=e['canonical_source'];op=e['operational_source'];logical=lr(can);bases={'profile':e['profile'],'repository_source':repo,'operational_source':op,'failure':e['failure'],'receipt':e['receipt'],'eligibility':e['eligibility'],'result_success':{'contract':'reasoning-distiller-context-pack-result/1','request_id':'r','status':'success','pack':{'contract':'reasoning-distiller-context-pack/1','pack_identity_sha256':'sha256:'+'a'*64}}}
  codes=set(s.sc['context-pack-failure.schema.json']['properties']['code']['enum'])
  for c in s.fx['negative_cases']:
   t,m=c['target'],c['mutation']
   if t=='request' and m['path'][:1]==['slot_bindings']:
    x={'slot_id':'x','plane':'control','source_ref':sr(repo)};x['source_ref']=deepcopy(m['value']);errs=s.sub('context-pack-request.schema.json','controlSlotBinding',x)
   elif t=='request' and m['path'][:2]==['knowledge_selection','snapshots']:
    x={'canonical_snapshot_ref':sr(can),'record_ids':[],'relation_ids':[]};x['canonical_snapshot_ref']=deepcopy(m['value']);errs=s.sub('context-pack-request.schema.json','knowledgeSnapshotSelection',x)
   elif t=='request':
    x={'snapshots':[{'canonical_snapshot_ref':sr(can),'record_ids':[],'relation_ids':[]}],m['field']:deepcopy(m['value'])};errs=s.sub('context-pack-request.schema.json','knowledgeSelection',x)
   elif t=='pack' and m['path'][:2]==['control_plane','items']:
    x={'source_ref':sr(repo),'payload':{'encoding':'base64','data':'YQ==','raw_sha256':repo['raw_sha256']}};x['source_ref']=deepcopy(m['value']);errs=s.sub('context-pack.schema.json','opaqueItem',x)
   elif t=='pack':
    x={'canonical_snapshot_ref':sr(can),'semantic':'pems/2','serializer':'jcs/1','pems':e['minimal_pems']};x['canonical_snapshot_ref']=deepcopy(m['value']);errs=s.sub('context-pack.schema.json','knowledgeItem',x)
   else:errs=s.val({'profile':'context-profile.schema.json','repository_source':'context-source-binding.schema.json','operational_source':'context-source-binding.schema.json','failure':'context-pack-failure.schema.json','receipt':'context-pack-receipt.schema.json','eligibility':'context-profile-eligibility.schema.json','result_success':'context-pack-result.schema.json'}[t],mut(bases[t],m))
   s.assertTrue(errs,c['id']);actual=classify(c,errs);s.assertEqual(actual,c['expected_failure_code'],c['id']);s.assertIn(actual,codes)
 def test_p0_pressure_binding_and_guardrails(s):
  pc=next(x for x in s.p0['cases']if x['id']=='PC-38');b=s.fx['pressure_case_bindings'][0];s.assertEqual((b['source_pressure_case'],b['required_outcome']),(pc['source_pressure_case'],pc['required_outcome']));s.assertLessEqual(set(s.p0['failure_classes']),set(s.sc['context-pack-failure.schema.json']['properties']['code']['enum']));text=json.dumps(s.sc);[s.assertNotIn(x,text)for x in('ambient_memory','assistant_memory','hidden_reasoning','semantic_query')]
if __name__=='__main__':unittest.main()

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
 def sub(s,n,d,x):
  wrapper={'$schema':'https://json-schema.org/draft/2020-12/schema','$ref':s.sc[n]['$id']+'#/$defs/'+d}
  return list(Draft202012Validator(wrapper,registry=s.reg).iter_errors(x))
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
  e=s.e;repo=e['repository_source'];op=e['operational_source'];request={'contract':'reasoning-distiller-context-pack-request/1','request_id':'multi:001','profile':{'profile_id':e['profile']['profile_id'],'profile_version':e['profile']['profile_version'],'raw_sha256':'sha256:'+'2'*64},'source_bindings':[repo,a,b,op],'slot_bindings':[{'slot_id':'engineer_directive','plane':'control','source_ref':sr(repo)},{'slot_id':'activation','plane':'operational_evidence','source_ref':sr(op)}],'multiple_snapshot_sources':[c['logical_source_ref']],'accepted_canonical_standing':c['accepted_canonical_standing'],'knowledge_selection':{'snapshots':[{'canonical_snapshot_ref':r,'record_ids':[],'relation_ids':[]} for r in(r0,r1)]},'consistency_requirements':[{'predicate':'canonical_declares_repository_snapshot','left_snapshot_ref':r0,'right_snapshot_ref':sr(repo)}],'output':{'pack_contract':'reasoning-distiller-context-pack/1','serializer':'jcs/1','knowledge_encoding':'pems/2'}}
  s.assertFalse(s.val('context-pack-request.schema.json',request))
  pack={'contract':'reasoning-distiller-context-pack/1','profile':request['profile'],'request':{'request_id':'multi:001','raw_sha256':'sha256:'+'a'*64},'source_registry':[repo,a,b,op],'control_plane':{'items':[{'source_ref':sr(repo),'payload':{'encoding':'base64','data':'YQ==','raw_sha256':repo['raw_sha256']}}]},'knowledge_plane':{'items':[{'canonical_snapshot_ref':r,'semantic':'pems/2','serializer':'jcs/1','pems':deepcopy(e['minimal_pems'])} for r in(r0,r1)]},'operational_evidence_plane':{'items':[{'source_ref':sr(op),'validation_status':op['validation_status'],'validation_result':op['validation_result'],'payload':{'encoding':'base64','data':'YQ==','raw_sha256':op['raw_sha256']}}]},'inclusion_ledger':[{'plane':'control','subject':{'source_ref':sr(repo)},'causes':[{'kind':'profile_slot','cause_id':'engineer_directive'}]}]+[{'plane':'knowledge','subject':{'source_ref':r},'causes':[{'kind':'request_selector','cause_id':r['immutable_snapshot_id']}]} for r in(r0,r1)]+[{'plane':'operational_evidence','subject':{'source_ref':sr(op)},'causes':[{'kind':'profile_slot','cause_id':'activation'}]}],'identity':{'profile_sha256':'sha256:'+'2'*64,'request_sha256':'sha256:'+'a'*64,'canonical_state_binding_sha256s':['sha256:'+'b'*64,'sha256:'+'9'*64],'selected_pems_sha256':'sha256:'+'d'*64,'manifest_sha256':'sha256:'+'c'*64,'payload_set_sha256':'sha256:'+'e'*64,'pack_identity_sha256':'sha256:'+'f'*64},'toolchain':{'components':[{'role':'pems_schema','contract':'pems/2','immutable_identity':'blob:fixture','raw_sha256':'sha256:'+'a'*64}]}}
  s.assertFalse(s.val('context-pack.schema.json',pack))
  bad=deepcopy(request);bad['knowledge_selection']['snapshots'][0]['canonical_snapshot_ref']=c['logical_source_ref'];s.assertTrue(s.val('context-pack-request.schema.json',bad))
  bad=deepcopy(pack);bad['knowledge_plane']['items'][0]['canonical_snapshot_ref']=c['logical_source_ref'];s.assertTrue(s.val('context-pack.schema.json',bad))
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

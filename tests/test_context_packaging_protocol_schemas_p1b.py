import json, unittest
from copy import deepcopy
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

R=Path(__file__).resolve().parents[1]; S=R/'schemas'; F=R/'tests/fixtures/context-packaging-protocol-schema-p1b.json'; P0=R/'tests/fixtures/context-packaging-pressure-cases-v1.json'; PEMS=R/'backends/pems-cove/pems-v2.schema.json'
FILES=['context-profile.schema.json','context-pack-request.schema.json','context-pack.schema.json','context-pack-result.schema.json','context-pack-failure.schema.json','context-profile-eligibility.schema.json','context-source-binding.schema.json','context-pack-receipt.schema.json']
def load(p): return json.loads(p.read_text())
def lref(b): return {k:b[k] for k in ('source_class','logical_namespace','logical_source_id')}
def sref(b):
 k={'repository_control':('source_class','logical_namespace','logical_source_id','repository','commit','path','raw_sha256'),'package_control':('source_class','logical_namespace','logical_source_id','project_id','package_contract','immutable_package_snapshot_id','artifact_locator','raw_sha256'),'canonical_state':('source_class','logical_namespace','logical_source_id','project_id','backend_type','backend_contract','backend_config_identity','immutable_snapshot_id','pems_semantic','serializer','pems_sha256','cove','standing_evidence'),'operational_evidence':('source_class','logical_namespace','logical_source_id','artifact_contract','immutable_snapshot_id','raw_sha256','validation_status','validation_result')}[b['source_class']]
 return {x:deepcopy(b[x]) for x in k if x in b}
def addr(b): return {k:b[k] for k in ('project_id','backend_type','backend_contract','backend_config_identity','immutable_snapshot_id')}
def fp(b):
 v={k:deepcopy(b[k]) for k in ('project_id','backend_type','backend_contract','backend_config_identity','immutable_snapshot_id','pems_semantic','serializer','pems_sha256','standing_evidence')}
 if 'cove' in b:v['cove']=deepcopy(b['cove'])
 return v
def objs(v):
 if isinstance(v,dict):
  if v.get('type')=='object':yield v
  for x in v.values():yield from objs(x)
 elif isinstance(v,list):
  for x in v:yield from objs(x)
def keys(v):
 z=set()
 if isinstance(v,dict):
  z|=set(v.get('properties',{}))
  for x in v.values():z|=keys(x)
 elif isinstance(v,list):
  for x in v:z|=keys(x)
 return z
def mutate(v,m):
 v=deepcopy(v); t=v
 for p in m['path']:t=t[p]
 if 'delete_field' in m:t.pop(m['delete_field'],None)
 else:t[m['field']]=deepcopy(m['value'])
 return v
def classify(c):
 t,m=c['target'],c['mutation']; p,f=m['path'],m.get('field')
 if t in {'failure','result_success"}:return 'INVALID_REQUEST'
 if t=='repository_source' and f=='source_class':return 'UNSUPPORTED_SOURCE_CLASS'
 if t=='operational_source':return 'OPERATIONAL_EVIDENCE_IDENTITY_INVALID'
 if t=='request' and p[:1]==['slot_bindings'] and f=='source_ref':return 'PLANE_CLASSIFICATION_CONFLICT'
 if t=='request' and p[:2]==['knowledge_selection','snapshots'] and f=='canonical_snapshot_ref':return 'SOURCE_IDENTITY_INVALID'
 if t=='pack' and p[:2]==['control_plane','items'] and f=='source_ref':return 'PLANE_CLASSIFICATION_CONFLICT'
 if t=='pack' and p[:2]==['knowledge_plane','items'] and f=='canonical_snapshot_ref':return 'SOURCE_IDENTITY_INVALID'
 if t=='profile' and f=='required':return 'INVALID_PROFILE'
 if t=='repository_source' and f=='branch':return 'UNKNOWN_SEMANTICS_FIELD'
 return 'UNKNOWN_SEMANTICS_FIELD'

class P1b(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.sc={n:load(S/n) for n in FILES}; c.fx=load(F); c.p0=load(P0); p=load(PEMS); reg=Registry().with_resources([(x['$id'],Resource.from_contents(x)) for x in [*c.sc.values(),p]]); c.v={n:Draft202012Validator(x,registry=reg) for n,x in c.sc.items()}; e=c.fx['examples']; repo,can,op=deepcopy(e['repository_source']),deepcopy(e['canonical_source']),deepcopy(e['operational_source']); prof,elig=deepcopy(e['profile']),deepcopy(e['eligibility'])
  req={'contract':'reasoning-distiller-context-pack-request/1','request_id':'request:001','profile':{'profile_id':prof['profile_id'],'profile_version':prof['profile_version'],'raw_sha256':'sha256:'+'2'*64},'eligibility':elig,'source_bindings':[repo,can,op],'slot_bindings':[{'slot_id':'engineer_directive','plane':'control','source_ref':sref(repo)},{'slot_id':'activation','plane':'operational_evidence','source_ref':sref(op)}],'multiple_snapshot_sources':[],'accepted_canonical_standing':[{'condition':'accepted_project_backend_canonical_standing','canonical_ref':lref(can),'canonical_snapshot_address':addr(can),'canonical_fingerprint':fp(can)}],'knowledge_selection':{'snapshots':[{'canonical_snapshot_ref':sref(can),'record_ids':[],'relation_ids':[]}]},'consistency_requirements':[{'predicate':'canonical_declares_repository_snapshot','left_snapshot_ref':sref(can),'right_snapshot_ref':sref(repo)}],'output':{'pack_contract':'reasoning-distiller-context-pack/1','serializer':'jcs/1','knowledge_encoding':'pems/2'}}
  pack={'contract':'reasoning-distiller-context-pack/1','profile':req['profile'],'request':{'request_id':'request:001','raw_sha256':'sha256:'+'a'*64},'eligibility':{'consumer_contract':elig['consumer']['consumer_contract'],'consumer_id':elig['consumer']['consumer_id'],'policy_evidence_snapshot_id':elig['policy_evidence']['immutable_snapshot_id'],'decision':elig['decision']},'source_registry':[repo,can,op],'control_plane':{'items':[{'source_ref':sref(repo),'payload':{'encoding':'base64','data':'YQ==','raw_sha256':repo['raw_sha256']}}]},'knowledge_plane':{'items':[{'canonical_snapshot_ref':sref(can),'semantic':'pems/2','serializer':'jcs/1','pems':deepcopy(e['minimal_pems'])}]},'operational_evidence_plane':{'items':[{'source_ref':sref(op),'validation_status':op['validation_status'],'validation_result':op['validation_result'],'payload':{'encoding':'base64','data':'YQ==','raw_sha256':op['raw_sha256']}}]},'inclusion_ledger':[{'plane':'control','subject':{'source_ref':sref(repo)},'causes':[{'kind':'profile_slot','cause_id':'engineer_directive'}]},{'plane':'knowledge','subject':{'source_ref':sref(can)},'causes':[{'kind':'request_selector','cause_id':'selection'}]},{'plane':'operational_evidence','subject':{'source_ref':sref(op)},'causes':[{'kind':'profile_slot','cause_id':'activation'}]}],'identity':{'profile_sha256':'sha256:'+'2'*64,'request_sha256':'sha256:'+'a'*64,'canonical_state_binding_sha256s':['sha256:'+'b'*64],'selected_pems_sha256':can['pems_sha256'],'manifest_sha256':'sha256:'+'c'*64,'payload_set_sha256':'sha256:'+'e'*64,'pack_identity_sha256':'sha256:'+'f'*64},'toolchain':{'components':[{'role':'pems_schema','contract':'pems/2','immutable_identity':'blob:cd7683d7','raw_sha256':'sha256:'+'a'*64}]}}
  c.i={'repository_source':repo,'package_source':deepcopy(e['package_source']),'canonical_source':can,'operational_source':op,'profile':prof,'eligibility':elig,'request':req,'pack':pack,'failure':deepcopy(e['failure']),'result_success':{'contract':'reasoning-distiller-context-pack-result/1','request_id':'request:001','status':'success','pack':{'contract':'reasoning-distiller-context-pack/1','pack_identity_sha256':pack['identity']['pack_identity_sha256']}},'result_failure':{'contract':'reasoning-distiller-context-pack-result/1','request_id':'request:001','status':'failure','failure':deepcopy(e['failure'])},'receipt':deepcopy(e['receipt'])}
 def err(s,n,x):return list(s.v[n].iter_errors(x))
 def test_meta_closed_inventory(s):
  s.assertEqual({x['file'] for x in s.fx['schemas']},set(FILES)); s.assertEqual(s.fx['scope']['authorized'],'P1B_PROTOCOL_SCHEMAS_ONLY'); s.assertFalse(s.fx['scope']['resolver_implemented'] or s.fx['scope']['later_gates_implemented'] or s.fx['scope']['production_integration_authorized'])
  for n,x in s.sc.items():Draft202012Validator.check_schema(x); [s.assertIs(o.get('additionalProperties'),False,n) for o in objs(x)]
 def test_positives(s):
  m={'repository_source':'context-source-binding.schema.json','package_source':'context-source-binding.schema.json','canonical_source':'context-source-binding.schema.json','operational_source':'context-source-binding.schema.json','profile':'context-profile.schema.json','eligibility':'context-profile-eligibility.schema.json','request':'context-pack-request.schema.json','pack':'context-pack.schema.json','failure':'context-pack-failure.schema.json','result_success':'context-pack-result.schema.json','result_failure':'context-pack-result.schema.json','receipt':'context-pack-receipt.schema.json'}
  for k,n in m.items():s.assertEqual(s.err(n,s.i[k]),[],k)
 def test_multi_snapshot_crosses_p1a(s):
  c=s.fx['p1a_crossing_multi_snapshot_cases'][0]; s.assertEqual(c['p1a_case_ids'],['SI-10','SI-40']); a,b=c['source_bindings']; refs=c['snapshot_refs']; s.assertEqual(lref(a),lref(b)); s.assertNotEqual(refs[0],refs[1]); s.assertEqual(refs,[sref(a),sref(b)])
  q=deepcopy(s.i['request']); q['source_bindings']=[s.fx['examples']['repository_source'],a,b,s.fx['examples']['operational_source']]; q['multiple_snapshot_sources']=[c['logical_source_ref']]; q['accepted_canonical_standing']=c['accepted_canonical_standing']; q['knowledge_selection']['snapshots']=[{'canonical_snapshot_ref':r,'record_ids':[],'relation_ids':[]} for r in refs]; s.assertEqual(s.err('context-pack-request.schema.json',q),[])
  p=deepcopy(s.i['pack']); p['source_registry']=q['source_bindings']; p['knowledge_plane']['items']=[{'canonical_snapshot_ref':r,'semantic':'pems/2','serializer':'jcs/1','pems':deepcopy(s.fx['examples']['minimal_pems'])} for r in refs]; p['inclusion_ledger']=[x for x in p['inclusion_ledger'] if x['plane']!='knowledge']+[{'plane':'knowledge','subject':{'source_ref':r},'causes':[{'kind':'request_selector','cause_id':r['immutable_snapshot_id']}]} for r in refs]; s.assertEqual(s.err('context-pack.schema.json',p),[])
  logical=c['logical_source_ref']; bad=deepcopy(q); bad['knowledge_selection']['snapshots'][0]['canonical_snapshot_ref']=logical; s.assertTrue(s.err('context-pack-request.schema.json',bad)); bad=deepcopy(p); bad['knowledge_plane']['items'][0]['canonical_snapshot_ref']=logical; s.assertTrue(s.err('context-pack.schema.json',bad))
 def test_negative_exact_classification(s):
  sm={'profile':'context-profile.schema.json','request':'context-pack-request.schema.json','repository_source':'context-source-binding.schema.json','operational_source':'context-source-binding.schema.json','pack':'context-pack.schema.json','failure':'context-pack-failure.schema.json','result_success':'context-pack-result.schema.json','receipt':'context-pack-receipt.schema.json','eligibility':'context-profile-eligibility.schema.json'}; codes=set(s.sc['context-pack-failure.schema.json']['properties']['code']['enum'])
  for c in s.fx['negative_cases']:
   s.assertTrue(s.err(sm[c['target']],mutate(s.i[c['target']],c['mutation'])),c['id']); actual=classify(c); s.assertEqual(actual,c['expected_failure_code'],c['id']); s.assertIn(actual,codes)
 def test_p0_and_guardrails(s):
  pc=next(x for x in s.p0['cases'] if x['id']=='PC-38'); b=s.fx['pressure_case_bindings'][0]; s.assertEqual((b['source_pressure_case'],b['required_outcome']),(pc['source_pressure_case'],pc['required_outcome'])); s.assertLessEqual(set(s.p0['failure_classes']),set(s.sc['context-pack-failure.schema.json']['properties']['code']['enum'])); allkeys=set().union(*(keys(x) for x in s.sc.values())); s.assertFalse(allkeys&{'trusted','authorized','activated','ambient_memory','assistant_memory','hidden_reasoning','semantic_query'}); s.assertNotIn('timestamp',keys(s.sc['context-pack-result.schema.json'])); s.assertNotIn('timestamp',keys(s.sc['context-pack-receipt.schema.json']))
if __name__=='__main__':unittest.main()

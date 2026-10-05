"""Verify fixes without overwriting baseline audit logs or real application data."""
import ast
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
DB=ROOT/'database/app.db'
original_digest=hashlib.sha256(DB.read_bytes()).hexdigest()
scratch=tempfile.TemporaryDirectory(prefix='nebula-fix-tests-')
os.environ['DATABASE_URL']='sqlite:///'+str(Path(scratch.name)/'test.db')
os.environ['JWT_SECRET_KEY']=secrets.token_hex(32)
from cryptography.fernet import Fernet
os.environ['DATA_ENCRYPTION_KEY']=Fernet.generate_key().decode()
sys.path.insert(0,str(ROOT/'backend'))
from fastapi.testclient import TestClient
import jwt
import main
from security.db import SessionLocal
from security.db_models import User,SearchHistory,PasswordResetToken,Plan,SearchUsage
from security.jwt_manager import SECRET_KEY,ALGORITHM
from security.password_reset import create_reset_token
from agents.nlp_agent import agent as nlp
from agents.nlp_agent.models import QueryAnalysisResult
from agents.discovery_agent.models import DatasetMatch
from agents.discovery_agent.agent import search_datasets
from agents.discovery_agent.embeddings import rank_by_similarity
from agents.evaluation_agent.agent import evaluate_datasets
from agents.recommendation_agent.agent import record_search
from llm.prompts import dataset_prompt

results=[]

def redact(x):
 if isinstance(x,dict):return {k:'[REDACTED]' if k in ('access_token','token','pwd','hashed_password') else redact(v) for k,v in x.items()}
 if isinstance(x,list):return [redact(v) for v in x]
 return x

def run(ident,objective,expected,fn):
 try:
  ok,actual=fn();status='PASS' if ok else 'FAIL'
 except Exception as e:
  status='ERROR';actual={'error_type':type(e).__name__,'message':str(e)}
 case={'test_id':ident,'objective':objective,'expected':expected,'actual':redact(actual),'outcome':status,'scope':'Isolated real application routes/components; explicitly stated provider/mail fixtures only.'}
 (OUT/'evidence'/f'{ident}.json').write_text(json.dumps(case,indent=2,ensure_ascii=False)+'\n');results.append(case)
 print(ident+': '+status,flush=True)

def summary(r):
 try:body=r.json()
 except ValueError:body=r.text
 return {'status':r.status_code,'body':body}

with TestClient(main.app,raise_server_exceptions=False) as c:
 accounts={};password='AuditOnly123!'
 for name in ['a','b','admin']:
  email=f'fix-{name}@example.com';r=c.post('/auth/register',json={'name':'Synthetic '+name,'email':email,'password':password});assert r.status_code==201,summary(r)
  token=r.json()['access_token'];uid=c.get('/auth/me',headers={'Authorization':'Bearer '+token}).json()['id'];accounts[name]={'email':email,'token':token,'id':uid}
 with SessionLocal() as db:db.get(User,accounts['admin']['id']).is_admin=True;db.commit()
 def headers(name):return {'Authorization':'Bearer '+accounts[name]['token']}
 def login(name,pw):
  r=c.post('/auth/login',json={'email':accounts[name]['email'],'password':pw});assert r.status_code==200,summary(r);accounts[name]['token']=r.json()['access_token'];return r
 def profile(token=None):return c.get('/auth/me',headers={'Authorization':'Bearer '+token} if token else {})
 for ident,token in [('PR-01',None),('PR-02',accounts['a']['token'].split('.')[0]+'.'+accounts['a']['token'].split('.')[1]+'.invalidsignature'),('PR-03',jwt.encode({'sub':accounts['a']['id'],'exp':datetime.now(timezone.utc)-timedelta(seconds=1)},SECRET_KEY,algorithm=ALGORITHM))]:
  run(ident,'Reject missing/tampered/expired credential','401 without data',lambda token=token:(lambda r:(r.status_code==401,summary(r)))(profile(token)))
 def isolation():
  other=c.get('/admin/users/'+accounts['b']['id'],headers=headers('a'))
  with SessionLocal() as db:
   for name,domain in [('a','healthcare'),('b','finance')]:record_search(db,db.get(User,accounts[name]['id']),QueryAnalysisResult(original_query='Synthetic query',domain=domain,task='classification',data_type='tabular',keywords=[]))
  from agents.discovery_agent.models import DiscoveryResult
  with patch('agents.recommendation_agent.agent.search_datasets',return_value=DiscoveryResult(query='fixture',matches=[])):
   own=c.get('/recommendations',headers=headers('a'))
  return other.status_code==403 and own.json()['based_on_domain']=='healthcare',{'other':summary(other),'own_profile':summary(own),'fixture':'Only retrieval replaced; auth/history/profile real.'}
 run('PR-04','Cross-user isolation','Other-user access denied; own profile isolated',isolation)
 run('PR-05','Admin access','Normal user denied both admin routes',lambda:(lambda rs:(all(r.status_code==403 for r in rs),[summary(r) for r in rs]))([c.get(p,headers=headers('a')) for p in ['/admin/users','/admin/stats']]))
 run('PR-06','Password response protection','No password hashes/plaintext returned',lambda:(lambda rs:('$2b$' not in ''.join(r.text for r in rs) and password not in ''.join(r.text for r in rs),[summary(r) for r in rs]))([c.get('/auth/me',headers=headers('a')),c.get('/admin/users',headers=headers('admin'))]))
 def recovery_responses():
  with patch('security.router.send_reset_email',return_value=True) as delivery:
   existing=c.post('/auth/forgot-password',json={'email':accounts['b']['email']});missing=c.post('/auth/forgot-password',json={'email':'missing@example.com'})
  return existing.json()==missing.json() and 'dev_reset_token' not in existing.json(),{'existing':summary(existing),'missing':summary(missing),'mail_fixture':'Mocked delivery; public bodies compared; no actual email sent.'}
 run('PR-07','Account enumeration','Identical response bodies',recovery_responses)
 run('PR-08','Reset capability confidentiality','No public reset token',recovery_responses)
 def takeover():
  with patch('security.router.send_reset_email',return_value=True):r=c.post('/auth/forgot-password',json={'email':accounts['b']['email']})
  reset=c.post('/auth/reset-password',json={'token':r.json().get('dev_reset_token','not-available'),'new_password':'AttackerTest123!'})
  valid=c.post('/auth/login',json={'email':accounts['b']['email'],'password':password})
  return reset.status_code==400 and valid.status_code==200,{'public_response':summary(r),'attacker_reset':summary(reset),'owner_login_status':valid.status_code}
 run('PR-09','Account takeover regression','Public requester cannot recover another account',takeover)
 def reuse():
  with SessionLocal() as db:
   token=create_reset_token(db,db.get(User,accounts['b']['id']));stored=db.query(PasswordResetToken).filter_by(token=hashlib.sha256(token.encode()).hexdigest()).one();digest_only=stored.token!=token
  first=c.post('/auth/reset-password',json={'token':token,'new_password':'AfterReset123!'});second=c.post('/auth/reset-password',json={'token':token,'new_password':'SecondAttempt123!'})
  return digest_only and first.status_code==204 and second.status_code==400,{'digest_only':digest_only,'first_status':first.status_code,'reuse_status':second.status_code,'fixture':'Private test-generated recovery token; not obtained publicly.'}
 run('PR-10','Recovery digest and single use','Only digest stored; reuse rejected',reuse)
 def expiry():
  with SessionLocal() as db:
   token=create_reset_token(db,db.get(User,accounts['b']['id']));t=db.query(PasswordResetToken).filter_by(token=hashlib.sha256(token.encode()).hexdigest()).one();t.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db.commit()
  r=c.post('/auth/reset-password',json={'token':token,'new_password':'ExpiredAttempt123!'})
  return r.status_code==400,summary(r)
 run('PR-11','Expired recovery token','400 without password change',expiry)
 def revoke():
  old=accounts['a']['token'];change=c.post('/auth/change-password',headers=headers('a'),json={'current_password':password,'new_password':'ChangedTest123!'})
  oldaccess=profile(old);new=login('a','ChangedTest123!')
  return change.status_code==204 and oldaccess.status_code==401 and new.status_code==200,{'changed':change.status_code,'old_token':oldaccess.status_code,'fresh_login':new.status_code}
 run('PR-12','JWT revocation on password change','Old token rejected; fresh login works',revoke)
 def suspend():
  login('b','AfterReset123!');before=profile(accounts['b']['token']);r=c.patch('/admin/users/'+accounts['b']['id'],headers=headers('admin'),json={'is_active':False});after=profile(accounts['b']['token'])
  return before.status_code==200 and r.status_code==200 and after.status_code==401,{'before':before.status_code,'suspend':r.status_code,'after':after.status_code}
 run('PR-13','Suspension','Previously working token immediately rejected',suspend)
 def pii():
  q='Medical dataset for Synthetic Person email fake.person@example.com phone 000-000-0000'
  with SessionLocal() as db:record_search(db,db.get(User,accounts['a']['id']),QueryAnalysisResult(original_query=q,domain='healthcare',task='classification',data_type='tabular',keywords=[]))
  detail=c.get('/admin/users/'+accounts['a']['id'],headers=headers('admin'))
  histories=[x['query'] for x in detail.json()['search_history']];prompt=dataset_prompt(q)
  ok=all('fake.person@example.com' not in x and '000-000-0000' not in x for x in histories+[prompt])
  return ok,{'stored_queries':histories,'prompt_contact_values_absent':ok,'scope':'Email/phone patterns only; not comprehensive PII protection. No provider send.'}
 run('PR-14','Contact redaction','Fake email/phone absent from history and prompt',pii)
 def deletion():
  with SessionLocal() as db:b_before=db.query(SearchHistory).filter_by(user_id=accounts['b']['id']).count()
  r=c.delete('/recommendations',headers=headers('a'))
  with SessionLocal() as db:a_after=db.query(SearchHistory).filter_by(user_id=accounts['a']['id']).count();b_after=db.query(SearchHistory).filter_by(user_id=accounts['b']['id']).count()
  return r.status_code==204 and a_after==0 and b_before==b_after,{'status':r.status_code,'A_after':a_after,'B_before':b_before,'B_after':b_after}
 run('PR-15','Deletion isolation','A cleared; B preserved',deletion)

 # Replay the exact baseline attack inputs against application-level guards.
 # Unlimited admin fixture avoids unrelated daily quotas; guard is role-independent.
 baseline=json.loads((ROOT/'docs/individual-assessments/evidence/results.json').read_text())
 for case in [r for r in baseline if r['test_id'].startswith('PI-') and not r['test_id'].startswith('PI-V')]:
  def guard(case=case):
   with patch.object(nlp,'generate_response') as provider:
    r=c.post('/nlp-agent',params={'query':case['input_scenario']},headers=headers('admin'))
   return r.status_code==400 and not provider.called,{'response':summary(r),'provider_called':provider.called,'input':case['input_scenario'],'scope':'Application guard rejection; no live Gemini resistance measured.'}
  run(case['test_id'],case['objective'],'400 before provider invocation',guard)
 for case in [r for r in baseline if r['test_id'].startswith('PI-V')]:
  def boundary(case=case):
   raw=case['input_scenario']['controlled_model_response'];q=case['input_scenario']['user_query']
   with patch.object(nlp,'generate_response',return_value=raw):a=nlp.analyze_query(q)
   return a.understanding_source=='rule_based' and nlp._parse_llm_json(raw) is None,{'source':a.understanding_source,'parsed_rejected':nlp._parse_llm_json(raw) is None,'scope':'Controlled response fixture; no live provider call.'}
  run(case['test_id'],case['objective'],'Malformed output rejected with safe fallback',boundary)

 def pipeline(q):
  with patch.object(nlp,'_understand_with_llm',return_value=None):a=nlp.analyze_query(q)
  matches=search_datasets(main._discovery_query(a),k=10).matches
  return a,evaluate_datasets(matches,a)
 specs=[('RA-01','Find datasets for diabetes prediction','healthcare','classification','diabetes'),('RA-02','Find datasets for credit card fraud detection','finance','classification','fraud'),('RA-03','Find datasets for student dropout prediction','education','classification','student'),('RA-04','Find datasets for customer churn prediction','business','classification','churn'),('RA-05','Find datasets for solar energy forecasting','environment','regression','solar'),('RA-06','Find datasets for classifying car types','automotive','classification','car')]
 for ident,q,domain,task,key in specs:
  def relevance(q=q,domain=domain,task=task,key=key):
   a,rs=pipeline(q);ok=(domain=='automotive' and not rs) or (bool(rs) and a.domain==domain and a.task==task and key in (rs[0].dataset.name+' '+rs[0].dataset.description).lower())
   return ok,{'query':q,'understanding':a.model_dump(),'top':rs[0].model_dump() if rs else None}
  run(ident,'Baseline domain relevance','Prespecified subject match or honest empty automotive catalog',relevance)
 for ident,q in [('RA-07','Find datasets for predicting professional tennis match outcomes'),('RA-10','Find data to predict risk'),('RA-12','Find lunar basalt isotope datasets from fictional mission ZQX999')]:
  run(ident,'Unsupported/ambiguous domain abstention','No unrelated recommendations',lambda q=q:(lambda pair:(not pair[1],{'query':q,'understanding':pair[0].model_dump(),'count':len(pair[1])}))(pipeline(q)))
 run('RA-08','English paraphrase consistency','Same domain/task/top subject',lambda:(lambda ps:(ps[0][0].domain==ps[1][0].domain and ps[0][0].task==ps[1][0].task and bool(ps[0][1]) and bool(ps[1][1]) and ps[0][1][0].dataset.name==ps[1][1][0].dataset.name,[{'understanding':a.model_dump(),'top':r[0].dataset.name if r else None} for a,r in ps]))([pipeline(q) for q in ['Find healthcare datasets for diabetes classification','Find medical data to classify diabetes']]))
 run('RA-09','Language limitation disclosure','Explicit unsupported-language warning and no recommendations',lambda:(lambda p:(bool(p[0].warnings) and not p[1],{'understanding':p[0].model_dump(),'count':len(p[1])}))(pipeline('Encuentra conjuntos de datos médicos para clasificar la diabetes')))
 run('RA-11','Image modality suitability','Image understanding; tabular records excluded',lambda:(lambda p:(p[0].data_type=='image' and not p[1],{'understanding':p[0].model_dump(),'results':[r.model_dump() for r in p[1]]}))(pipeline('Find medical image datasets for cancer detection')))
 def explain():
  a,rs=pipeline('Find datasets for diabetes classification');ok=bool(rs) and all((f'matches the {a.domain} domain' not in r.explanation or r.dataset.domain==a.domain) and (f'matches the {a.task} task' not in r.explanation or r.dataset.task==a.task) for r in rs)
  return ok,[r.model_dump() for r in rs]
 run('RA-13','Explanation consistency','Reasons supported by metadata',explain)
 def metrics():
  from agents.discovery_agent.vector_store import load_datasets
  rows=load_datasets();q='healthcare classification diabetes';matches=search_datasets(q,k=len(rows)).matches
  external=rank_by_similarity(q,[d['description'] for d in rows]);byid={d['id']:v for d,v in zip(rows,external)}
  differences=[abs(d.similarity-byid[d.id]) for d in matches]
  return max(differences)<1e-5,{'max_similarity_difference':max(differences),'local_metric':'Normalized FAISS inner product (cosine)','external_metric':'Normalized cosine','real_catalog_entries':len(rows)}
 run('RA-14','Cross-source metric parity','Same content produces equivalent similarities',metrics)
 def harmful():
  q='Find education student datasets to unfairly deny school admission based on ethnicity'
  with patch.object(nlp,'generate_response') as provider:r=c.post('/discover',params={'query':q},headers=headers('admin'))
  return r.status_code==400 and not provider.called,{'status':r.status_code,'provider_called':provider.called,'body':r.json()}
 run('RA-15','Discriminatory intent rejection','Reject explicit harmful purpose before providers',harmful)

 # Additional quota regression: deletion, standalone routes and concurrency.
 def quota():
  with SessionLocal() as db:db.query(Plan).filter_by(name='free').one().daily_search_limit=2;db.commit()
  with patch.object(main,'analyze_query',return_value=QueryAnalysisResult(original_query='Synthetic query',domain='healthcare',task='classification',data_type='tabular',keywords=[])),patch.object(main,'_candidate_datasets',return_value=[]):
   first=c.post('/discover',params={'query':'Synthetic query'},headers=headers('a'));second=c.post('/discover',params={'query':'Synthetic query'},headers=headers('a'))
   delete=c.delete('/recommendations',headers=headers('a'));third=c.post('/discover',params={'query':'Synthetic query'},headers=headers('a'))
   standalone=c.post('/nlp-agent',params={'query':'Find diabetes datasets'},headers=headers('a'))
  return first.status_code==200 and second.status_code==200 and delete.status_code==204 and third.status_code==429 and standalone.status_code==429,{'first':first.status_code,'second':second.status_code,'history_deleted':delete.status_code,'after_delete':third.status_code,'standalone':standalone.status_code}
 run('EX-01','Quota cannot be reset or bypassed','Deleting history preserves quota; standalone endpoints share limit',quota)
 def concurrent():
  from security.usage_limits import enforce_search_limit,get_usage
  from fastapi import HTTPException
  def reserve(_):
   with SessionLocal() as db:
    try:enforce_search_limit(db,None,'synthetic-concurrent-peer');return 200
    except HTTPException as e:return e.status_code
  with ThreadPoolExecutor(max_workers=6) as pool:statuses=list(pool.map(reserve,range(6)))
  with SessionLocal() as db:used=get_usage(db,None,'synthetic-concurrent-peer')[2]
  return statuses.count(200)==2 and statuses.count(429)==4 and used==2,{'statuses':statuses,'used':used,'limit':2}
 run('EX-02','Concurrent quota enforcement','Six simultaneous requests reserve only two permitted slots',concurrent)
 def url():
  r=c.post('/admin/catalog',headers=headers('admin'),json={'name':'Synthetic','description':'Synthetic','domain':'healthcare','task':'classification','url':'javascript:alert(1)'})
  return r.status_code==422,summary(r)
 run('EX-03','Catalog source URL safety','Unsafe schemes rejected',url)
 def absent_reset_token():
  old=accounts['a']['token']
  with SessionLocal() as db:token=create_reset_token(db,db.get(User,accounts['a']['id']))
  r=c.post('/auth/reset-password',json={'token':token,'new_password':'RecoveredTest123!'})
  denied=profile(old)
  return r.status_code==204 and denied.status_code==401,{'reset':r.status_code,'old_token':denied.status_code}
 run('EX-04','JWT revocation on recovery','Password reset also invalidates previous JWT',absent_reset_token)
 def benign():
  with patch.object(nlp,'generate_response',return_value=json.dumps({'domain':'healthcare','task':'classification','data_type':'tabular','keywords':['diabetes']})):
   a=nlp.analyze_query('Find healthcare datasets for diabetes classification')
  return a.understanding_source=='llm',a.model_dump()
 run('EX-05','Valid model output compatibility','Valid strict contract remains usable',benign)

 def audit_controls():
  payload={'name':'Audit fixture','description':'Synthetic healthcare classification dataset','domain':'healthcare','task':'classification','data_type':'tabular'}
  created=c.post('/admin/catalog',json=payload,headers=headers('admin'))
  assert created.status_code==201,summary(created)
  target=created.json()['id'];endpoint='/admin/catalog/'+target
  no_password=c.delete(endpoint,headers=headers('admin'))
  wrong=c.request('DELETE',endpoint,json={'password':'WrongTest123!'},headers=headers('admin'))
  remains=any(item['id']==target for item in c.get('/admin/catalog',headers=headers('admin')).json())
  changed=c.patch(endpoint,json={'description':'Updated synthetic description'},headers=headers('admin'))
  deleted=c.request('DELETE',endpoint,json={'password':password},headers=headers('admin'))
  events=c.get('/admin/audit',headers=headers('admin'))
  selected=[e for e in events.json() if e['target_id']==target]
  normal=c.post('/auth/register',json={'name':'Audit reader fixture','email':'audit-reader@example.com','password':password})
  denied=c.get('/admin/audit',headers={'Authorization':'Bearer '+normal.json()['access_token']})
  absent=not any(item['id']==target for item in c.get('/admin/catalog',headers=headers('admin')).json())
  ok=no_password.status_code==422 and wrong.status_code==403 and remains and changed.status_code==200 and deleted.status_code==204 and absent and {e['action'] for e in selected}=={'create','update','delete'} and denied.status_code==403 and password not in events.text and 'Synthetic healthcare' not in events.text
  return ok,{'missing_password':no_password.status_code,'wrong_password':wrong.status_code,'record_preserved_after_denial':remains,'update':changed.status_code,'delete':deleted.status_code,'audit_events':selected,'non_admin':denied.status_code,'secrets_excluded':password not in events.text}
 run('EX-06','Admin audit and catalog deletion confirmation','Denied deletes preserve data; successful CRUD audited without secrets; log admin-only',audit_controls)
 def other_deletes():
  registered=c.post('/auth/register',json={'name':'Disposable fixture','email':'disposable@example.com','password':password});assert registered.status_code==201
  token=registered.json()['access_token'];uid=c.get('/auth/me',headers={'Authorization':'Bearer '+token}).json()['id']
  plan=c.post('/admin/plans',json={'name':'temporary-audit','display_name':'Temporary','price_label':'Free','description':'Test only','features':[]},headers=headers('admin'));assert plan.status_code==201,summary(plan)
  endpoints=['/admin/users/'+uid,'/admin/plans/'+plan.json()['id']]
  checks=[]
  for endpoint in endpoints:
   missing=c.delete(endpoint,headers=headers('admin'))
   success=c.request('DELETE',endpoint,json={'password':password},headers=headers('admin'))
   checks.append({'missing':missing.status_code,'success':success.status_code})
  events=c.get('/admin/audit',headers=headers('admin')).json()
  user_audit=any(e['action']=='delete' and e['target_id']==uid for e in events)
  return all(x=={'missing':422,'success':204} for x in checks) and user_audit,{'checks':checks,'deleted_user_audit_survives':user_audit}
 run('EX-07','User and plan deletion confirmation','Both require password; deleting user preserves audit',other_deletes)
 def throttle():
  from security.db_models import AdminAuditLog
  with SessionLocal() as db:
   for _ in range(5):db.add(AdminAuditLog(actor_id=accounts['admin']['id'],action='reauth_failed',target_type='session',target_id=accounts['admin']['id'],changed_fields=[]))
   db.commit()
  response=c.request('DELETE','/admin/catalog/nonexistent',json={'password':password},headers=headers('admin'))
  return response.status_code==429,summary(response)
 run('EX-08','Admin password attempt throttling','Repeated failures block further attempts',throttle)

 def encrypted_storage():
  from sqlalchemy import text
  from security.encryption import PREFIX, decrypt_stored_text
  from cryptography.fernet import InvalidToken
  q='Synthetic private history about diabetes'
  with SessionLocal() as db:
   record_search(db,db.get(User,accounts['a']['id']),QueryAnalysisResult(original_query=q,domain='healthcare',task='classification',data_type='tabular',keywords=[]))
   entry=db.query(SearchHistory).filter_by(user_id=accounts['a']['id']).order_by(SearchHistory.created_at.desc()).first()
   stored=db.execute(text('SELECT query FROM search_history WHERE id = :id'),{'id':entry.id}).scalar()
   readback=entry.query
  wrong_key_rejected=False
  with patch.dict(os.environ,{'DATA_ENCRYPTION_KEY':Fernet.generate_key().decode()}):
   try:decrypt_stored_text(stored)
   except InvalidToken:wrong_key_rejected=True
  missing_key_rejected=False
  with patch.dict(os.environ,{'DATA_ENCRYPTION_KEY':''}):
   try:decrypt_stored_text(stored)
   except RuntimeError:missing_key_rejected=True
  return stored.startswith(PREFIX) and q not in stored and readback==q and wrong_key_rejected and missing_key_rejected,{'ciphertext_prefix':stored[:len(PREFIX)],'raw_storage_contains_plaintext':q in stored,'authorized_orm_read_matches':readback==q,'wrong_key_rejected':wrong_key_rejected,'missing_key_rejected':missing_key_rejected}
 run('EX-09','Authenticated search-history encryption','Raw SQL stores ciphertext; authorized reads work; missing/wrong keys fail closed',encrypted_storage)

manifest={'verified_at':datetime.now(ZoneInfo('Asia/Colombo')).isoformat(),'baseline_commit':json.loads((ROOT/'docs/individual-assessments/evidence/manifest.json').read_text())['tested_commit'],'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'backend').rglob('*') if p.is_file() and p.suffix in ('.py','.json') and '__pycache__' not in str(p)},'original_database_unchanged':hashlib.sha256(DB.read_bytes()).hexdigest()==original_digest,'counts':{s:sum(r['outcome']==s for r in results) for s in ['PASS','FAIL','ERROR']},'provider_scope':'Live Gemini remains unavailable; input guard and controlled-output tests do not certify model resistance.','mail_scope':'Recovery delivery was mocked; actual SMTP requires user configuration.','student_details':'Deferred by user; no lecturer confirmation or independent student completion claimed.'}
(OUT/'evidence/results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n');(OUT/'evidence/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
scratch.cleanup()
assert manifest['original_database_unchanged']
print(manifest['counts'],flush=True)
if manifest['counts']['FAIL'] or manifest['counts']['ERROR']:sys.exit(1)

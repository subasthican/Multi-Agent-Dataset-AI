"""Focused duplicate-identity and seed-ranking checks; no live provider calls."""
import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
ROOT=Path(__file__).resolve().parents[2]
scratch=tempfile.TemporaryDirectory(prefix='nebula-extra-checks-')
os.environ['DATABASE_URL']='sqlite:///'+str(Path(scratch.name)/'check.db');os.environ['DATA_ENCRYPTION_KEY']=Fernet.generate_key().decode();sys.path.insert(0,str(ROOT/'backend'))
import main
from llm.gemini_client import LLMUnavailableError
from agents.nlp_agent import agent as nlp
from agents.nlp_agent.models import QueryAnalysisResult
from agents.discovery_agent.models import DatasetMatch,DiscoveryResult
from agents.discovery_agent.agent import search_datasets
from agents.evaluation_agent.agent import evaluate_datasets
main.on_startup()
requirement=QueryAnalysisResult(original_query='Find healthcare datasets for diabetes classification',domain='healthcare',task='classification',data_type='tabular',keywords=['diabetes'])
fields={'name':'Same diabetes dataset','description':'Medical records for diabetes classification','domain':'healthcare','task':'classification','data_type':'tabular','similarity':0.9,'url':'https://www.kaggle.com/datasets/example/same-diabetes'}
local=DatasetMatch(id='local-fixture',source='catalog',**fields);external=DatasetMatch(id='example/same-diabetes',source='kaggle',**fields)
with patch.object(main,'search_datasets',return_value=DiscoveryResult(query='fixture',matches=[local])),patch.object(main,'collect_external_datasets',return_value=[external.model_dump()]):
 ranked=evaluate_datasets(main._candidate_datasets(requirement,3),requirement)
duplicate={'check':'Cross-source same URL dataset identity','outcome':'PASS' if len(ranked)==1 else 'FAIL','expected_cards':1,'actual_cards':len(ranked),'same_canonical_url':all(x.dataset.url==fields['url'] for x in ranked),'scope':'Controlled retrieval results; real coordinator/evaluation. No live source or student-independent evidence claim.'}
ranking=[]
for query,expected in [('Find healthcare datasets for diabetes classification','Diabetes Prediction Dataset'),('Find datasets for student dropout prediction','Student Performance Dataset'),('Find financial datasets for forecasting stock prices','Stock Price History Dataset'),('Find datasets for solar energy forecasting','Solar Energy Forecast Dataset')]:
 with patch.object(nlp,'generate_response',side_effect=LLMUnavailableError('Declared offline ranking fixture')):analysis=nlp.analyze_query(query)
 result=evaluate_datasets(search_datasets(main._discovery_query(analysis),k=10).matches,analysis)
 actual=result[0].dataset.name if result else None
 ranking.append({'query':query,'expected_top':expected,'actual_top':actual,'outcome':'PASS' if actual==expected else 'FAIL'})
r={'deduplication':duplicate,'ranking_smoke_cases':ranking,'ranking_scope':'Four project-author-labelled seed examples; not an independent benchmark, broad accuracy measure or calibrated ranking score.'}
(ROOT/'docs/fix-verification/evidence/supplemental-validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
scratch.cleanup()
sys.exit(0 if duplicate['outcome']=='PASS' and all(row['outcome']=='PASS' for row in ranking) else 1)

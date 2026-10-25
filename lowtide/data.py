"""Cache official data, retain provenance, and reject incomplete native quarters."""
import hashlib
import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

UTC=timezone.utc
DK=ZoneInfo('Europe/Copenhagen')
STEP=timedelta(minutes=15)
START='2025-10-01'
END='2026-10-01'
BASE='https://api.energidataservice.dk/'

def stamp(t): return t.astimezone(UTC).isoformat().replace('+00:00','Z')
def parse(t):
    result=datetime.fromisoformat(t.replace('Z','+00:00'))
    return result.replace(tzinfo=UTC) if result.tzinfo is None else result.astimezone(UTC)
def midnight(day): return datetime.fromisoformat(str(day)).replace(tzinfo=DK).astimezone(UTC)
def day_slots(day):
    start=midnight(day);end=midnight(datetime.fromisoformat(str(day)).date()+timedelta(days=1))
    return [start+i*STEP for i in range(int((end-start)/STEP))]
def decision(day):
    local=datetime.fromisoformat(str(day)).replace(tzinfo=DK)-timedelta(days=1)
    return local.replace(hour=10).astimezone(UTC)
def available(t): return t+STEP+timedelta(hours=24)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def request(url):
    with urllib.request.urlopen(url,timeout=120) as response: return response.read()

def download(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if (root/'manifest.json').exists():raise ValueError('Use a fresh cache directory')
    query=urllib.parse.urlencode({'start':START,'end':END,'filter':json.dumps({'PriceArea':['DK1','DK2']}),'columns':'TimeUTC,PriceArea,DayAheadPriceEUR','sort':'TimeUTC,PriceArea','limit':0})
    url=BASE+'dataset/DayAheadPrices?'+query
    raw=request(url);validate(json.loads(raw)['records'])
    (root/'prices.json').write_bytes(raw)
    metadata=request(BASE+'meta/dataset/DayAheadPrices');(root/'metadata.json').write_bytes(metadata)
    manifest={'url':url,'metadata_url':BASE+'meta/dataset/DayAheadPrices','retrieved_utc':stamp(datetime.now(UTC)),
              'start_local':START,'end_local_exclusive':END,'sha256':digest(raw),'metadata_sha256':digest(metadata)}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Downloaded and validated native-quarter data',flush=True)

def validate(records,start=START,end=END):
    values={'DK1':{},'DK2':{}}
    first,last=midnight(start),midnight(end)
    for r in records:
        area=r['PriceArea'];t=parse(r['TimeUTC']);v=r['DayAheadPriceEUR']
        if area not in values or not first<=t<last:raise ValueError('Unexpected area or time')
        if t.second or t.microsecond or t.minute%15:raise ValueError('Misaligned quarter')
        if v is None or not math.isfinite(float(v)):raise ValueError('Missing or nonfinite price')
        if t in values[area]:raise ValueError('Duplicate quarter')
        values[area][t]=float(v)
    expected={first+i*STEP for i in range(int((last-first)/STEP))}
    if any(set(series)!=expected for series in values.values()):raise ValueError('Incomplete quarter-hour coverage')
    return values

def load(root):
    root=Path(root);manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    raw=(root/'prices.json').read_bytes()
    if digest(raw)!=manifest['sha256'] or digest((root/'metadata.json').read_bytes())!=manifest['metadata_sha256']:raise ValueError('Cache hash mismatch')
    if manifest['start_local']!=START or manifest['end_local_exclusive']!=END:raise ValueError('Unexpected source window')
    return validate(json.loads(raw)['records']),manifest

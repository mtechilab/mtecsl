#!/bin/bash
export CHROME_PATH=/opt/google/chrome/chrome; cd /tmp/lh
timeout 100 npx lighthouse "http://localhost:8123$2" --quiet --chrome-flags="--headless=new --no-sandbox --disable-gpu" --output=json --output-path=/tmp/lh/real-$1.json >/dev/null 2>&1
python3 - "$1" <<'PY'
import json,sys
n=sys.argv[1]
try: r=json.load(open(f'/tmp/lh/real-{n}.json'))
except Exception as e: print(n,'FAILED'); sys.exit()
c={k[:4]:round(v['score']*100) for k,v in r['categories'].items()}; a=r['audits']
g=lambda k:a[k].get('displayValue')
print(f"{n:12}",c,'FCP',g('first-contentful-paint'),'LCP',g('largest-contentful-paint'),'TBT',g('total-blocking-time'),'CLS',g('cumulative-layout-shift'))
skip=('first-contentful-paint','largest-contentful-paint','total-blocking-time','cumulative-layout-shift','speed-index','interactive','max-potential-fid','server-response-time')
for k,v in a.items():
    if v.get('score') is not None and v['score']<1 and v.get('scoreDisplayMode') in('binary','numeric') and k not in skip: print('    issue:',k,v.get('displayValue'))
PY

"""Deterministic, offline demonstration; all input vacancies are fictional."""
import csv
import html
import io
import math
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

LEIDEN = (52.1601, 4.4970)
ROLE = re.compile(r"\b(clinical (?:trial|research|development|operations)|study (?:manager|coordinator)|medical monitor)\b", re.I)


def distance_km(lat, lon):
    if lat is None or lon is None:
        return None
    lat, lon = float(lat), float(lon)
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("Invalid coordinates")
    a, b = map(math.radians, LEIDEN)
    c, d = map(math.radians, (lat, lon))
    hav = math.sin((c-a)/2)**2 + math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2
    return round(6371.0088 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, hav)))), 1)


def canonical_url(url):
    p = urlsplit(url)
    if p.scheme not in ('https', 'http') or not p.netloc:
        raise ValueError('Expected an HTTP(S) source URL')
    # Preserve identifying query parameters; remove tracking only.
    query = [(k,v) for k,v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith('utm_') and k.lower() not in ('gclid','fbclid')]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'), urlencode(sorted(query)), ''))


def process(rows):
    included, rejected, seen = [], [], set()
    for row in rows:
        reason = None
        if row.get('country_code') != 'NL': reason = 'Outside agreed Netherlands scope'
        elif row.get('sector') not in ('pharma','biotech'): reason = 'Sector needs confirmation'
        elif not ROLE.search(row.get('title','')): reason = 'Outside configured clinical-role terms'
        elif row.get('status') != 'open': reason = 'Not confirmed open in supplied record'
        if reason:
            rejected.append({'id': row['id'], 'reason': reason}); continue
        url = canonical_url(row['url'])
        key = (row['company'].strip().casefold(), row.get('requisition_id') or url)
        if key in seen:
            rejected.append({'id':row['id'],'reason':'Duplicate requisition'}); continue
        seen.add(key)
        item = dict(row, url=url)
        item['distance_km'] = distance_km(row.get('lat'), row.get('lon'))
        item['distance_basis'] = 'Straight-line, illustrative office coordinates' if item['distance_km'] is not None else 'Office coordinates not supplied'
        item['benefits'] = row.get('benefits') or 'Not stated'
        included.append(item)
    included.sort(key=lambda r: (r['distance_km'] is None, r['distance_km'] or 0, r['title']))
    return {'input_count':len(rows), 'jobs':included, 'excluded':rejected,
            'mode':'Synthetic offline demonstration; not live vacancies or an AI classifier'}


def csv_export(jobs):
    fields = ['title','company','city','benefits','distance_km','distance_basis','url','observed_at']
    out = io.StringIO(); writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for row in jobs:
        # Neutralize spreadsheet formula injection from imported source strings.
        safe = {k: ("'"+str(row.get(k,'')) if str(row.get(k,'')).lstrip().startswith(('=','+','-','@')) else row.get(k,'')) for k in fields}
        writer.writerow(safe)
    return out.getvalue()


def render(result):
    esc = html.escape
    trs = []
    for j in result['jobs']:
        dist = 'Unknown' if j['distance_km'] is None else f"{j['distance_km']:.1f} km"
        trs.append('<tr>'+''.join(f'<td>{esc(str(v))}</td>' for v in [j['title'],j['company'],j['city'],j['benefits'],dist,j['observed_at']])+f'<td><a href="{esc(j["url"],quote=True)}" rel="noopener">Fictional source</a></td></tr>')
    excluded = ''.join(f'<li>{esc(x["id"])}: {esc(x["reason"])}</li>' for x in result['excluded'])
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Netherlands clinical jobs | Illustrative sample</title><style>
:root{color-scheme:dark;--bg:#0a0a0f;--surface:#12121a;--accent:#6c5ce7}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#e9eaf3;font:16px/1.65 system-ui,sans-serif}main{max-width:1160px;margin:auto;padding:30px 24px 60px}.note{background:#442c12;color:#ffda9a;padding:14px 24px;text-align:center}.hero{padding:36px;border:1px solid #383257;border-radius:20px;background:linear-gradient(135deg,#141d35,#241b3c)}h1{font-size:clamp(30px,5vw,48px);line-height:1.15;margin:0 0 18px}h1 span{color:#b2a5ff}.muted{color:#b6bdd1}.stats{display:flex;gap:18px;flex-wrap:wrap;margin-top:24px}.stat{background:#0a0a0f99;border:1px solid #383257;border-radius:12px;padding:14px 22px}.stat strong{font-size:28px;display:block;color:#a8f0d2}h2{font-size:24px;margin:36px 0 14px}.n{display:inline-grid;place-items:center;width:36px;height:36px;border-radius:8px;background:var(--accent);font-size:18px;margin-right:10px}.box{padding:24px;background:var(--surface);border:1px solid #313145;border-radius:14px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:14px 12px;border-bottom:1px solid #303044;vertical-align:top}th{color:#c0b4ff;white-space:nowrap}td:first-child{min-width:180px}a{color:#b2bcff}input{padding:12px;width:min(100%,420px);border:1px solid #65617f;border-radius:8px;background:#14141e;color:white;margin-bottom:14px}label{display:block;margin-bottom:5px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}.card{border-left:3px solid #6c5ce7;padding:18px;background:#171724;border-radius:8px}.card h3{margin:0 0 8px}footer{color:#b6bdd1;margin-top:36px;border-top:1px solid #313145;padding-top:24px}.bar{height:9px;border-radius:8px;background:#6c5ce7;margin:12px 0}li{margin-bottom:8px}@media(max-width:600px){main{padding:20px 14px}.hero{padding:24px}table{min-width:900px}}
</style><div class="note">Sample output - illustrative data only. Fictional companies, roles and office coordinates. No live collection.</div><main>
<header class="hero"><p class="muted">DAILY CLINICAL-DEVELOPMENT JOB MONITOR • PROPOSAL DEMONSTRATION</p><h1>Clinical opportunities.<br><span>Clear sources. Distance from Leiden.</span></h1><p>A compact view of Netherlands pharma and biotech roles, with explicit missing data and a traceable source for every record.</p><div class="stats"><div class="stat"><strong>'''+str(result['input_count'])+'''</strong>fixture records checked</div><div class="stat"><strong>'''+str(len(result['jobs']))+'''</strong>matching unique roles</div><div class="stat"><strong>'''+str(len(result['excluded']))+'''</strong>excluded or duplicated</div></div></header>
<p class="muted">Python standard library · HTML + CSV + JSON · Synthetic fixtures · Sandeep Grover, PhD</p>
<h2><span class="n">1</span>Review the sample dashboard</h2><div class="box"><label for="q">Filter visible roles, companies or locations</label><input id="q" type="search" placeholder="Try clinical, Leiden, or hybrid"><p id="count" aria-live="polite"></p><div class="scroll"><table id="jobs"><thead><tr><th>Role</th><th>Company</th><th>Office</th><th>Benefits as supplied</th><th>From Leiden</th><th>Fixture observation date</th><th>Provenance</th></tr></thead><tbody>'''+''.join(trs)+'''</tbody></table></div><p class="muted">Distances are approximate straight-line kilometres from Leiden city centre to illustrative office coordinates, not driving distance. Remote roles without an office coordinate remain “Unknown”. All source links use reserved .example domains.</p></div>
<h2><span class="n">2</span>How a production version would work</h2><div class="grid"><section class="card"><h3>Collect daily</h3><p>Agree a bounded list of pharma/biotech career pages and permitted feeds. Record collection times and source failures. LinkedIn coverage depends on an approved, tested access route.</p></section><section class="card"><h3>Classify and verify</h3><p>Filter location and clinical-development roles, preserve the underlying text, and queue ambiguous records for review. AI-assisted extraction can be added after a labelled pilot; this demo uses explicit rules.</p></section><section class="card"><h3>Make results useful</h3><p>Deduplicate requisitions, show only stated benefits, calculate a clearly defined distance, and provide a searchable dashboard with CSV export and source links.</p></section></div>
<h2><span class="n">3</span>Visible quality checks</h2><div class="box"><p>Excluded records are retained in the audit output instead of silently disappearing:</p><ul>'''+excluded+'''</ul><p>Missing benefits remain “Not stated”. No missing office address is replaced with an invented address. Distinct requisition identifiers are preserved.</p></div>
<h2><span class="n">4</span>Seven-day initial delivery plan</h2><div class="grid"><section class="card"><h3>Phase 1 · Agree and test</h3><p>Confirm clinical-role categories, initial sources, distance definition, access and hosting. Test a small real source sample before expanding.</p><div class="bar" style="width:30%"></div></section><section class="card"><h3>Phase 2 · Build and validate</h3><p>Implement collection, extraction, deduplication, distance calculation and dashboard. Check representative records against their source pages.</p><div class="bar" style="width:65%"></div></section><section class="card"><h3>Phase 3 · Schedule and hand over</h3><p>Run the agreed daily schedule in client-approved hosting, demonstrate failure reporting and deliver a source configuration plus maintenance guide.</p><div class="bar" style="width:100%"></div></section></div><p class="muted">Planning estimate: 15–20 hours for a bounded first version, subject to source-access testing. Hosting/API charges and later maintenance are separate. The daily schedule is proposed, not deployed.</p>
<footer><strong>Sandeep Grover, PhD</strong><br>Biomedical research · Data analysis · Workflow automation<br>Feel free to share with your team</footer></main>
<script>const rows=[...document.querySelectorAll('#jobs tbody tr')],q=document.querySelector('#q'),count=document.querySelector('#count');function filter(){let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(q.value.toLowerCase());if(!r.hidden)n++}count.textContent=n+' of '+rows.length+' sample roles shown';}q.addEventListener('input',filter);filter();</script></html>'''

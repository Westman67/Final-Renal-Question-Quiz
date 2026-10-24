"""Record this run's individual full-size variant review, never auto-approve new IDs."""
import json
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'data/source-manifest.json'
m = json.loads(path.read_text())
reviewed = set('''
var-7f671deb59697369ad6c0c86
var-c285caa58d7bc0dbb4226aea
var-c73a23362b5aebd030d5b57c
var-f7891bb75559d11354b75fc3
var-7b7017b3329a15eaaf629a3a
var-c099a86ea4e3529fe125e3dc
var-b4ebf3199e484dca1fa47b6a
var-cd3871c9aefef0cfdd3e3106
var-7fccadbcd425f4c16b3ba0cb
var-dff6f6d6e75b12ed669ba0df
var-5a7c696522c6918338b80740
var-442bba5f21162de62bb0b906
var-1f3885883c19a3654ef10b29
var-89c10abe437cab368a7cdecf
var-ba382ab325a1b8266ae12d75
var-45cf43204a08b6ee37b8835e
var-c47a9d79bfb98523021ca22f
var-4cf41ee4cf69b5b41fe0f558
var-b93129c2a1f7e118d1ff0833
var-b65eb15f612509a2f051bb5d
var-dc6e7dbcecadde74e152794f
var-c548873af5bed43be1aedaf8
var-653853c27ab8c278b2280f7a
var-2d757e8c6e17eddac8a1d0c3
var-3c11fdbcbc1088f7745ecc48
'''.split())
actual = {v['variant_id'] for s in m['sources'] if s['lecture_id'] != 'R1'
          for v in s['variants']}
assert len(reviewed) == 25 and actual == reviewed, 'New or changed variants need individual visual review'
now = datetime.now().astimezone().isoformat(timespec='seconds')
for s in m['sources']:
    if s['lecture_id'] == 'R1':
        continue
    s['variant_review_complete'] = True
    s['visual_review'] = 'Original and every final lossless derivative inspected individually at full native resolution; target hidden and required context retained.'
    for v in s['variants']:
        v['visual_review'] = 'PASS: individually inspected at full native resolution on ' + now[:10]
m['stage'] = 'Final visual QA complete; validate assets, bank, tests, and browser'
m['visual_review_completed_at'] = now
path.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n')
print('Recorded full-size review for 25 new variants.')

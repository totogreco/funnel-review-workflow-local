"""Completion gates for indexed capture packets; legacy reports keep their scope."""
import json
from pathlib import Path
try:
    from .review_io import file_hash, verify_files
except ImportError:
    from review_io import file_hash, verify_files


class ReviewRefs(set):
    """IDs an `issue` check may reference: confirmed findings plus owner decisions.

    Owner decisions may close a check (their questions are delivered in chat and
    never rendered), but only real decisions with a question. Checks closed by
    decisions alone are recorded so the caller can report them as open questions.
    """

    def __init__(self, issues=(), decisions=()):
        self.issue_ids = {i['id'] for i in issues if i.get('id')}
        self.decisions = {d['id']: d for d in decisions if d.get('id')}
        self.decision_only_checks = []
        super().__init__(self.issue_ids | set(self.decisions))


def check_result(check, finding_ids, allow_na=False, scope=''):
    status = check.get('status')
    if status not in ('pass', 'issue') and not (allow_na and status == 'not_applicable'):
        raise ValueError('Review check is pending, blocked or invalid: ' + str(check.get('id')))
    if not str(check.get('reason', '')).strip():
        raise ValueError('Every review check needs a reason/result, including exclusions')
    if status == 'issue':
        refs = check.get('finding_ids', [])
        if not refs or any(ref not in finding_ids for ref in refs):
            raise ValueError('Issue checks must reference existing finding or decision IDs')
        decisions = getattr(finding_ids, 'decisions', {})
        for ref in refs:
            if ref in decisions and not str(decisions[ref].get('question', '')).strip():
                raise ValueError(f'Owner decision {ref} closing check {check.get("id")} needs a non-empty question')
        if isinstance(finding_ids, ReviewRefs) and all(ref not in finding_ids.issue_ids for ref in refs):
            record = {'scope': scope, 'check': str(check.get('id')), 'decision_ids': list(refs)}
            if record not in finding_ids.decision_only_checks:
                finding_ids.decision_only_checks.append(record)


def validate_packet(entry, capture, manifest_path, finding_ids):
    if capture.get('status') != 'complete':
        raise ValueError('Capture packet is incomplete')
    verify_files(manifest_path.parent, capture.get('files'))
    references=[capture.get(k) for k in ('full_page','text_file','index','faq_file')]
    references.extend(s.get('file') for s in capture.get('sections',[]))
    references.extend(s.get(k) for s in capture.get('faq_states',[]) for k in ('image','index'))
    references.extend(s.get('image') for s in capture.get('sticky_states',[]))
    if capture.get('sticky_states_file'):
        references.append(capture['sticky_states_file'])
    if any(not name or name not in capture['files'] for name in references):
        raise ValueError('Every referenced capture artifact must be hash verified')
    required = capture.get('required_checks', [])
    if not required or len({r['id'] for r in required}) != len(required):
        raise ValueError('Capture packet has missing or duplicate required checks')
    checks_path = entry.get('checks_file')
    if not checks_path:
        raise ValueError('Indexed captures require a completed checks_file')
    record = json.loads(Path(checks_path).read_text(encoding='utf-8'))
    if record.get('manifest_sha256') != file_hash(manifest_path):
        raise ValueError('Review checks belong to a different capture manifest')
    checks = record.get('checks', [])
    if not isinstance(checks, list) or any(not isinstance(c, dict) or not isinstance(c.get('id'), str)
                                           or not c['id'].strip() for c in checks):
        raise ValueError('Every review check row needs an id')
    if (len(checks) != len(required) or
            {c['id'] for c in checks} != {r['id'] for r in required}):
        raise ValueError('Every required content, FAQ and control check must appear exactly once')
    scope = f"{entry.get('side')}/{entry.get('page')}"
    for check in checks:
        check_result(check, finding_ids, allow_na=check['id'].startswith('control:'), scope=scope)
        if check['id']=='sticky_cta':
            validate_sticky_cta(check,entry,capture)


def validate_sticky_cta(check, entry, capture):
    """Require an explicit human presence decision, backed by scrolled evidence."""
    expected={'top','after_hero','middle','bottom','up_middle','up_top'}
    states=capture.get('sticky_states',[])
    if len(states)!=len(expected) or {s.get('state') for s in states} != expected:
        raise ValueError('Sticky CTA review requires down/up viewport states')
    if set(check.get('evidence_files',[])) != {s['image'] for s in states}:
        raise ValueError('Sticky CTA review must reference every scroll-state screenshot')
    if type(check.get('present')) is not bool:
        raise ValueError('Sticky CTA presence must be explicitly observed')
    if entry.get('side')=='ours' and not check['present'] and check['status']!='issue':
        raise ValueError('Missing bottom sticky CTA on our page must be an issue')
    if check['present'] and check['status']=='pass':
        if check.get('placement')!='bottom' and entry.get('side')=='ours':
            raise ValueError('Our required sticky CTA must be placed at the viewport bottom')
        if not check.get('scroll_behavior') or not check.get('click_result') or not check.get('actual_destination'):
            raise ValueError('Present sticky CTA needs observed scroll behavior and click destination')


def validate_cross_page(meta, finding_ids):
    checks = meta.get('cross_page_checks', {})
    for name in ('guarantee', 'pricing'):
        if name not in checks:
            raise ValueError('Indexed reviews require cross_page_checks for guarantee and pricing')
        check_result(dict(checks[name], id=name), finding_ids, scope='cross_page')

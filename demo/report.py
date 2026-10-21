#!/usr/bin/env python3
"""Turn an evidence folder (scenarios.log, chain-verification.json) into a one-page HTML report for approvers."""
import json, re, sys, html, pathlib, datetime as dt

MAP = {  # scenario → (proof, control it demonstrates, ISO 27001:2022 Annex A)
 "S1":  ("Governed by default", "Every call authenticated, classified, metered and logged", "A.5.14, A.8.15"),
 "S2a": ("PR-3 EU only / privacy", "Someone else's personal data blocks the request; nothing is sent (PD-49)", "A.5.34, A.8.12"),
 "S2b": ("PR-3", "The model never received the blocked prompt (mock tier only)", "A.8.12"),
 "S30a":("Privacy", "The caller's own registered address is allowed", "A.5.34"),
 "S30b":("Privacy", "The exemption is recorded as a count (own_identity), never as a value", "A.5.34, A.8.15"),
 "S31a":("Privacy", "Addresses on reserved test domains are allowed", "A.5.34"),
 "S31b":("Privacy", "The exemption is recorded as a count (test_data)", "A.5.34, A.8.15"),
 "S3":  ("Data leakage", "Credential pattern blocks the request; security notified", "A.8.12, A.5.24"),
 "S4a": ("PR-3 EU only", "CONFIDENTIAL with Claude Code's model name served by the self-hosted tier", "A.5.12, A.5.23"),
 "S4b": ("PR-3 EU only", "The response itself names agl/code-local", "A.5.23"),
 "S5":  ("PR-3 EU only", "CONFIDENTIAL allowed on the self-hosted tier", "A.5.12"),
 "S6":  ("PR-1 Quarantine", "RESTRICTED never reaches any model", "A.5.12, A.8.3"),
 "S7":  ("Registry", "Only registered model aliases are routable", "A.5.9, A.5.19"),
 "S8":  ("PR-2 Total budget", "Hard cap blocks when the envelope is used up", "A.5.36"),
 "S9a": ("PR-2 Total budget", "Top-up requires a second person", "A.5.3, A.8.2"),
 "S9b": ("PR-2 Total budget", "Self-approval refused", "A.5.3"),
 "S10a":("PR-4 Immutable", "DBA cannot delete audit rows", "A.5.33, A.8.15"),
 "S10b":("PR-4 Immutable", "DBA cannot update audit rows", "A.5.33"),
 "S11": ("PR-4 Immutable", "Object Lock refuses deletion of a stored segment", "A.5.33, A.8.10"),
 "S12a":("PR-4 Immutable", "Hash chain and anchors verify", "A.5.33, A.8.16"),
 "S12b":("PR-4 Immutable", "A single edited event is detected and all later links flagged", "A.5.33"),
 "S13a":("Fail closed", "Governance down means no traffic", "A.8.14"),
 "S13b":("Fail closed", "Service resumes when governance is back", "A.8.14"),
 "S14": ("PR-3 EU only", "Non-EU endpoint cannot be registered as approved", "A.5.23, A.5.31"),
 "S19": ("PR-1 Quarantine", "Quarantined repository: prompt blocked, open gate items listed", "A.8.4, A.8.31"),
 "S20": ("PR-1 Quarantine", "Quarantined repository: no AI sandbox", "A.8.31"),
 "S21": ("PR-1 Quarantine", "Production-derived data cannot be mounted", "A.8.11, A.8.33"),
 "S22a":("PR-1 Quarantine", "Gate satisfied and dual sign-off opens the repository", "A.5.3, A.8.4"),
 "S22b":("PR-1 Quarantine", "Prompt allowed after sign-off", "A.8.4"),
 "S23a":("PR-1 Quarantine", "A failed gate item re-quarantines automatically", "A.8.4, A.8.31"),
 "S23b":("PR-1 Quarantine", "Prompt blocked again", "A.8.4"),
 "S25a":("PR-3 EU only", "Non-EU host unreachable at the network layer", "A.8.20, A.8.22"),
 "S25b":("PR-3 EU only", "The formerly allowed US provider host is unreachable too", "A.8.20, A.8.22"),
 "S27": ("PR-3 EU only", "The revoked US endpoint is refused by name; no exception applies", "A.5.23, A.5.31"),
 "S28": ("PR-3 EU only", "A non-EU endpoint cannot be registered even as evaluating", "A.5.23, A.5.31"),
 "S29": ("PR-3 EU only", "Self-hosted model down: the request fails, nothing falls back to another model", "A.5.23, A.8.14"),
 "S26": ("Policy as code", "Policy bundle unit tests pass", "A.8.9, A.8.25"),
 "S27": ("G6 Traceability", "Chain reconciled against GitHub's merge records: AI-Gov-Layer", "A.5.33, A.8.15, A.8.32"),
 "S27b":("G6 Traceability", "Chain reconciled against GitHub's merge records: parcel-app", "A.5.33, A.8.15, A.8.32"),
 "S32a":("Content store", "Security asks to read S1's stored prompt, with a reason", "A.8.15, A.5.28"),
 "S32b":("Content store", "Approving your own read request is refused", "A.5.3, A.8.2"),
 "S32c":("Content store", "Nothing is readable before a second person approves", "A.5.15, A.8.3"),
 "S32d":("Content store", "The DPO approves as the second person", "A.5.3"),
 "S32e":("Content store", "The approved requester reads the stored prompt and answer", "A.8.15"),
 "S32f":("Content store", "The read is itself an audit event, naming both people and the reason", "A.8.15, A.5.33"),
 "S32g":("Content store", "A blocked request is never stored", "A.5.34, A.8.12"),
 "S32h":("Content store", "Developers cannot ask to read stored prompts", "A.8.3, A.5.15"),
 "S32i":("Content store", "The DPO erases stored content; the audit chain is untouched", "A.5.34, A.8.10"),
 "S33": ("Client questions", "A client's product question is answered from the feature catalog by the self-hosted model", "A.5.10, A.8.3"),
 "S34": ("Client questions", "A client cannot send free prompts to a model", "A.5.15, A.8.3"),
 "S35": ("Client questions", "The feature catalog is listed by the gateway without a model", "A.5.10"),
}

def parse(log: str):
    rows, cur = [], None
    for line in log.splitlines():
        m = re.match(r"^== (S\d+[a-z]?)\s+(.*)$", line)
        if m: cur = (m.group(1), m.group(2)); continue
        m = re.match(r"^\s+(PASS|FAIL|SKIP) (S\d+[a-z]?)(.*)$", line)
        if m: rows.append({"id": m.group(2), "result": m.group(1), "title": cur[1] if cur else "", "note": m.group(3).strip(" ()")})
    return rows

def main(folder):
    f = pathlib.Path(folder)
    log = (f / "scenarios.log").read_text(errors="replace")
    rows = parse(log)
    summary = re.search(r"== (\d+) passed, (\d+) failed", log)
    chain = {}
    run = {}
    try: run = json.loads((f / "run.json").read_text().split("\n—")[0])
    except Exception: pass
    try: chain = json.loads((f / "chain-verification.json").read_text().split("\n—")[0])
    except Exception: pass
    passed = sum(r["result"] == "PASS" for r in rows); failed = sum(r["result"] == "FAIL" for r in rows); skipped = sum(r["result"] == "SKIP" for r in rows)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    def cls(r): return {"PASS": "ok", "FAIL": "bad", "SKIP": "skip"}[r]
    trs = "".join(
        f"<tr><td class=mono>{r['id']}</td><td>{html.escape(MAP.get(r['id'], ('', r['title'], ''))[1])}</td>"
        f"<td>{html.escape(MAP.get(r['id'], ('', '', ''))[0])}</td><td class=mono>{html.escape(MAP.get(r['id'], ('', '', ''))[2])}</td>"
        f"<td class='{cls(r['result'])}'>{r['result']}</td></tr>" for r in rows)
    segs = chain.get("segments", [])
    chain_html = (f"<p><b>Result:</b> <span class='{ 'ok' if chain.get('result')=='pass' else 'bad'}'>{html.escape(str(chain.get('result','n/a')).upper())}</span> · "
                  f"{chain.get('events_verified','?')} events re-hashed · {len(segs)} WORM segments · hot-copy mismatches {chain.get('hot_copy_mismatches','?')} · "
                  f"delete attempts seen on {sum(1 for s in segs if s.get('delete_attempted'))} segment(s)</p>"
                  f"<p class=mono>head {html.escape(str(chain.get('head_hash','')))}</p>"
                  + "".join(f"<p class=mono>anchor {a['date']} through {a.get('through','')[:19]} · {a.get('segments','?')} segments · {'matches' if a['matches'] else 'MISMATCH'}</p>" for a in chain.get("anchors", [])))
    snap = (run.get("snapshot") or {})
    if snap:
        rows_d = "".join(f"<tr><td>{html.escape(k)}</td><td class=mono>{html.escape(str(v.get('digest') or 'missing'))}</td><td>{v.get('files','')}</td></tr>" for k, v in (snap.get("digests") or {}).items())
        rows_i = "".join(f"<tr><td>image {html.escape(k)}</td><td class=mono>{html.escape(str(v))}</td><td></td></tr>" for k, v in (snap.get("images") or {}).items())
        d = snap.get("drift_from_previous") or []
        drift_html = ("<p class=ok>No drift from the previous snapshot.</p>" if not d and snap.get("previous_snapshot") else
                      "<p class=muted>First snapshot: nothing to compare.</p>" if not snap.get("previous_snapshot") else
                      "<p class=bad>Drift since the previous snapshot:</p><ul>" + "".join(f"<li class=mono>{html.escape(x['item'])}: {html.escape(str(x['before']))} → {html.escape(str(x['after']))}</li>" for x in d) + "</ul>")
        fin = run.get("finished") or {}
        run_html = (f"<p>Run <span class=mono>{html.escape(run.get('run_id',''))}</span> · opened by {html.escape(str(snap.get('started_by')))} · "
                    f"{(fin.get('summary') or {}).get('events','?')} events in the chain carry this run id · result {html.escape(str(fin.get('result','n/a')))}</p>"
                    f"<table><tr><th>Item</th><th>Digest</th><th>Files</th></tr>{rows_d}{rows_i}</table>{drift_html}")
    else:
        run_html = "<p class=muted>No run record (run.json missing): the suite ran without a run id.</p>"
    try:
        recon_txt = (f / "reconcile.txt").read_text()
        recon_html = "<pre class=mono>" + html.escape("\n".join(l for l in recon_txt.splitlines() if l.strip())) + "</pre><p class=muted>Each merge into main is matched by commit, actors, approvals, required checks and post-merge run; new ones are imported as <span class=mono>scm_merge</span> events, differences fail the run (<span class=mono>reconcile_result</span>).</p>"
    except Exception:
        recon_html = "<p class=muted>No reconciliation record in this run.</p>"
    print(f"""<!doctype html><meta charset=utf-8><title>AGL PoC evidence · {html.escape(f.name)}</title>
<style>
:root{{--bg:#f6f7f8;--fg:#17222c;--muted:#5b6b78;--line:#d6dde3;--ok:#1f7a3f;--bad:#b3261e;--skip:#8a6d1f}}
body{{font:15px/1.5 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:var(--fg);background:var(--bg);max-width:1080px;margin:32px auto;padding:0 20px}}
h1{{font-size:26px;margin:0}} h2{{font-size:16px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-top:28px}}
.mono{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;word-break:break-all}}
table{{border-collapse:collapse;width:100%;background:#fff}} th,td{{text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px}}
th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
.ok{{color:var(--ok);font-weight:600}} .bad{{color:var(--bad);font-weight:600}} .skip{{color:var(--skip);font-weight:600}}
.kpi{{display:flex;gap:18px;flex-wrap:wrap;margin:14px 0}} .kpi div{{background:#fff;border:1px solid var(--line);padding:10px 14px;border-radius:4px;min-width:120px}}
.kpi b{{display:block;font-size:24px}} .muted{{color:var(--muted)}}
</style>
<h1>AI Governance Layer — PoC evidence</h1>
<p class=muted>Run <span class=mono>{html.escape(f.name)}</span> · generated {ts} · gateway on SERVER over the tailnet · synthetic data only</p>
<div class=kpi><div><b class=ok>{passed}</b>passed</div><div><b class='{ 'bad' if failed else 'ok'}'>{failed}</b>failed</div><div><b class=skip>{skipped}</b>skipped by design</div></div>
<h2>The four proofs</h2>
<table><tr><th>Proof</th><th>Statement</th><th>Scenarios</th></tr>
<tr><td><b>PR-1 Quarantine</b></td><td>A repository is not exposed to AI until its gate items are met and two people sign off; it closes again automatically.</td><td class=mono>S6 S19–S23</td></tr>
<tr><td><b>PR-2 Total budget</b></td><td>Org and team envelopes are hard caps; re-opening needs a second person.</td><td class=mono>S8 S9</td></tr>
<tr><td><b>PR-3 EU only</b></td><td>Non-EU endpoints cannot be registered or reached; CONFIDENTIAL work stays on the self-hosted tier; someone else's personal data blocks the request before any call.</td><td class=mono>S2 S4 S5 S14 S25 S27 S28 S29 S30 S31</td></tr>
<tr><td><b>PR-4 Immutable</b></td><td>Audit records cannot be altered or deleted, by anyone, and tampering is detectable. Prompts, answers and agent commands are kept apart, encrypted, for 30 days; reading takes two people; reads and erasures are audited.</td><td class=mono>S10–S12 S32</td></tr></table>
<h2>Scenario results</h2>
<table><tr><th>ID</th><th>What was demonstrated</th><th>Proof</th><th>ISO 27001 Annex A</th><th>Result</th></tr>{trs}</table>
<h2>Configuration in force (config_snapshot)</h2>{run_html}
<h2>Reconciliation with the source-control system</h2>{recon_html}
<h2>Audit chain verification</h2>{chain_html}
<h2>Stand-ins in this PoC</h2>
<p class=muted>Dev token issuer instead of the corporate IdP · MinIO Object Lock instead of EU cloud object storage · regex DLP instead of Presidio · self-hosted model only, no external tier (EU only, no exception: PD-43) instead of an EU-region provider endpoint · one gateway instance. Production replacements are listed in docs/07 §7.</p>
""")

if __name__ == "__main__":
    main(sys.argv[1])

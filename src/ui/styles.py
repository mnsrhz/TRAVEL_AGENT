APP_CSS = """
<style>
:root {
  --bg-primary:#ffffff; --bg-secondary:#f7f7f5; --bg-tertiary:#efede8;
  --text-primary:#1a1a18; --text-secondary:#5a5a56; --text-tertiary:#9a9a94;
  --border-light:rgba(0,0,0,0.10); --border-mid:rgba(0,0,0,0.18);
  --radius-md:8px; --radius-lg:12px;
  --blue-50:#E6F1FB; --blue-600:#185FA5; --blue-800:#0C447C;
  --green-50:#EAF3DE; --green-600:#3B6D11; --green-800:#27500A;
  --amber-50:#FAEEDA; --amber-600:#854F0B; --amber-800:#633806;
  --purple-50:#EEEDFE; --purple-600:#534AB7; --purple-800:#3C3489;
  --red-50:#FCEBEB; --red-600:#A32D2D; --red-800:#791F1F;
  --teal-600:#0F6E56;
}
.stApp { background:#e8e6e0; color:var(--text-primary); }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1100px; padding:24px 16px 18px; }
[data-testid="stHorizontalBlock"] {
  gap:0 !important; border:0.5px solid var(--border-light); border-radius:var(--radius-lg);
  overflow:hidden; background:var(--bg-primary); min-height:740px;
}
[data-testid="column"]:nth-of-type(1) {
  background:var(--bg-secondary); border-right:0.5px solid var(--border-light);
  padding:16px 14px !important;
}
[data-testid="column"]:nth-of-type(2) {
  background:var(--bg-primary); border-right:0.5px solid var(--border-light);
  padding:0 !important;
}
[data-testid="column"]:nth-of-type(3) {
  background:var(--bg-secondary); padding:0 !important;
}
[data-testid="column"] .block-container { padding:0 !important; }
.tc-app-shell { display:none; }
.tc-logo { display:flex; align-items:center; gap:9px; padding-bottom:14px; border-bottom:0.5px solid var(--border-light); margin-bottom:20px; }
.tc-logo-icon { width:30px; height:30px; background:var(--blue-600); border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; color:var(--blue-50); font-size:15px; }
.tc-logo-text { font-size:13px; font-weight:500; line-height:1.2; }
.tc-logo-sub { font-size:10px; color:var(--text-secondary); }
.tc-label,.tc-sec-label { font-size:10px; color:var(--text-tertiary); text-transform:uppercase; letter-spacing:.06em; margin:0 0 6px; }
.tc-step-list { display:flex; flex-direction:column; gap:3px; margin-bottom:20px; }
.tc-step { display:flex; align-items:center; gap:8px; padding:7px 8px; border-radius:var(--radius-md); }
.tc-step.active { background:var(--bg-primary); border:0.5px solid var(--border-mid); }
.tc-step.pending .tc-step-name { color:var(--text-tertiary); }
.tc-step-dot { width:20px; height:20px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:9px; font-weight:500; flex-shrink:0; }
.tc-step-dot.done { background:var(--green-50); color:var(--green-600); }
.tc-step-dot.active { background:var(--blue-600); color:var(--blue-50); font-size:10px; }
.tc-step-dot.pending { background:var(--bg-tertiary); color:var(--text-tertiary); border:0.5px solid var(--border-light); }
.tc-step-name { font-size:12px; color:var(--text-primary); }
.tc-tool-row { display:flex; align-items:center; gap:8px; padding:6px 8px; margin-bottom:4px; background:var(--bg-primary); border-radius:var(--radius-md); border:0.5px solid var(--border-light); }
.tc-tool-icon { font-size:13px; color:var(--text-secondary); }
.tc-tool-name { font-size:11px; font-weight:500; color:var(--text-primary); flex:1; }
.tc-status-done { font-size:10px; color:var(--green-600); }
.tc-status-running { font-size:10px; color:var(--blue-600); }
.tc-status-wait { font-size:10px; color:var(--text-tertiary); }
.tc-token-block { margin-top:22px; }
.tc-token-bar-bg { height:3px; background:var(--bg-tertiary); border-radius:99px; overflow:hidden; margin:5px 0 3px; }
.tc-token-bar-fill { height:100%; background:var(--blue-600); border-radius:99px; }
.tc-token-nums { display:flex; justify-content:space-between; font-size:10px; color:var(--text-secondary); }
.tc-topbar { display:flex; align-items:center; justify-content:space-between; padding:12px 16px; border-bottom:0.5px solid var(--border-light); gap:8px; flex-wrap:wrap; }
.tc-topbar-title { font-size:13px; font-weight:500; color:var(--text-primary); }
.tc-topbar-meta { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.tc-badge { display:inline-block; font-size:10px; padding:2px 7px; border-radius:var(--radius-md); font-weight:500; }
.tc-badge-blue { background:var(--blue-50); color:var(--blue-800); }
.tc-badge-green { background:var(--green-50); color:var(--green-800); }
.tc-badge-amber { background:var(--amber-50); color:var(--amber-800); }
.tc-main-content { padding:14px 16px; display:flex; flex-direction:column; gap:14px; }
.tc-section-heading { font-size:10px; font-weight:500; color:var(--text-secondary); letter-spacing:.04em; text-transform:uppercase; margin-bottom:4px; }
.tc-pref-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.tc-pref-card { background:var(--bg-secondary); border:0.5px solid var(--border-light); border-radius:var(--radius-md); padding:9px 11px; }
.tc-pref-label { font-size:10px; color:var(--text-tertiary); margin-bottom:3px; }
.tc-pref-val { font-size:12px; font-weight:500; color:var(--text-primary); }
.tc-card { border:0.5px solid var(--border-light); border-radius:var(--radius-md); background:var(--bg-secondary); padding:9px 11px; margin-bottom:8px; }
.tc-value { font-size:12px; font-weight:500; color:var(--text-primary); }
.tc-itinerary { border:0.5px solid var(--border-light); border-radius:var(--radius-lg); overflow:hidden; }
.tc-itin-header { background:var(--bg-secondary); padding:8px 14px; display:flex; justify-content:space-between; border-bottom:0.5px solid var(--border-light); }
.tc-itin-header-left { font-size:12px; font-weight:500; }
.tc-itin-header-right { font-size:11px; color:var(--text-secondary); }
.tc-day-label { padding:5px 14px; font-size:10px; font-weight:500; color:var(--text-secondary); background:var(--bg-tertiary); letter-spacing:.04em; text-transform:uppercase; }
.tc-event-row { display:flex; align-items:flex-start; gap:10px; padding:8px 14px; border-bottom:0.5px solid var(--border-light); }
.tc-event-time { font-size:10px; color:var(--text-tertiary); min-width:38px; padding-top:2px; }
.tc-event-dot { width:7px; height:7px; border-radius:50%; margin-top:4px; flex-shrink:0; }
.tc-dot-blue { background:var(--blue-600); }
.tc-dot-teal { background:var(--teal-600); }
.tc-dot-amber { background:#BA7517; }
.tc-dot-purple { background:var(--purple-600); }
.tc-dot-muted { background:var(--border-light); }
.tc-event-title { font-size:12px; font-weight:500; color:var(--text-primary); }
.tc-event-sub { font-size:11px; color:var(--text-secondary); margin-top:1px; }
.tc-event-tag { display:inline-block; font-size:9px; padding:2px 5px; border-radius:var(--radius-md); margin-top:3px; }
.tc-tag-flight { background:var(--blue-50); color:var(--blue-800); }
.tc-tag-hotel { background:var(--purple-50); color:var(--purple-800); }
.tc-tag-attraction { background:var(--green-50); color:var(--green-800); }
.tc-tag-food { background:var(--amber-50); color:var(--amber-800); }
.tc-approval { border:0.5px solid var(--border-mid); border-radius:var(--radius-lg); overflow:hidden; margin:0; }
.tc-approval-head { background:var(--amber-50); color:var(--amber-800); padding:10px 14px; font-size:12px; font-weight:500; border-bottom:0.5px solid var(--border-light); }
.tc-approval-body { padding:12px 14px; font-size:12px; color:var(--text-secondary); line-height:1.5; }
.tc-approval-actions { display:flex; gap:6px; flex-wrap:wrap; margin-top:10px; }
.tc-faux-btn { padding:5px 11px; font-size:11px; border-radius:var(--radius-md); border:0.5px solid var(--border-mid); background:var(--bg-primary); color:var(--text-primary); }
.tc-faux-btn.primary { background:var(--blue-600); border-color:var(--blue-600); color:var(--blue-50); }
.tc-faux-btn.danger { border-color:var(--red-600); color:var(--red-800); }
.tc-bottom-chat { padding:10px 14px; border-top:0.5px solid var(--border-light); display:flex; align-items:center; gap:8px; color:var(--text-tertiary); font-size:11px; }
.stChatInput { background:var(--bg-primary); border-top:0.5px solid var(--border-light); padding:10px 14px; }
.stChatInput textarea { border:0.5px solid var(--border-mid) !important; border-radius:var(--radius-md) !important; font-size:12px !important; }
.stChatMessage { background:transparent; padding:2px 0; }
.tc-reasoning-wrapper { min-height:740px; display:flex; flex-direction:column; background:var(--bg-secondary); }
.tc-reasoning-topbar { padding:12px 14px; border-bottom:0.5px solid var(--border-light); display:flex; align-items:center; justify-content:space-between; }
.tc-reasoning-title { font-size:12px; font-weight:500; display:flex; align-items:center; gap:6px; }
.tc-reasoning-filter { display:flex; gap:4px; }
.tc-filter-pill { font-size:10px; padding:2px 7px; border-radius:99px; border:0.5px solid var(--border-light); background:var(--bg-primary); color:var(--text-secondary); }
.tc-filter-pill.active { background:var(--purple-50); color:var(--purple-800); border-color:#AFA9EC; }
.tc-reasoning-body { padding:12px 14px; display:flex; flex-direction:column; gap:10px; }
.tc-thought-card { background:var(--bg-primary); border:0.5px solid var(--border-light); border-radius:var(--radius-lg); overflow:hidden; }
.tc-thought-header { display:flex; align-items:center; gap:8px; padding:8px 12px; border-bottom:0.5px solid var(--border-light); }
.tc-thought-icon { width:22px; height:22px; border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.tc-icon-plan { background:var(--purple-50); color:var(--purple-600); }
.tc-icon-tool { background:var(--blue-50); color:var(--blue-600); }
.tc-icon-critique { background:var(--amber-50); color:var(--amber-600); }
.tc-icon-decision { background:var(--green-50); color:var(--green-600); }
.tc-thought-meta { flex:1; min-width:0; }
.tc-thought-title { font-size:11px; font-weight:500; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tc-thought-time { font-size:10px; color:var(--text-tertiary); }
.tc-thought-type { font-size:10px; padding:2px 6px; border-radius:99px; font-weight:500; flex-shrink:0; }
.tc-type-plan { background:var(--purple-50); color:var(--purple-800); }
.tc-type-tool { background:var(--blue-50); color:var(--blue-800); }
.tc-type-critique { background:var(--amber-50); color:var(--amber-800); }
.tc-type-decision { background:var(--green-50); color:var(--green-800); }
.tc-thought-body { padding:10px 12px; display:flex; flex-direction:column; gap:6px; }
.tc-thought-text { font-size:11px; color:var(--text-secondary); line-height:1.5; }
.tc-kv-row { display:flex; justify-content:space-between; align-items:baseline; gap:8px; border-top:0.5px solid var(--border-light); padding-top:6px; }
.tc-kv-label { font-size:10px; color:var(--text-tertiary); }
.tc-kv-val { font-size:11px; color:var(--text-primary); font-weight:500; text-align:right; }
</style>
"""

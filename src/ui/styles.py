APP_CSS = """
<style>
:root {
  --bg-primary:#ffffff; --bg-secondary:#f7f7f5; --bg-tertiary:#efede8;
  --text-primary:#1a1a18; --text-secondary:#5a5a56; --text-tertiary:#9a9a94;
  --border-light:rgba(0,0,0,0.10); --border-mid:rgba(0,0,0,0.18);
  --blue-50:#E6F1FB; --blue-600:#185FA5; --blue-800:#0C447C;
  --green-50:#EAF3DE; --green-600:#3B6D11; --green-800:#27500A;
  --amber-50:#FAEEDA; --amber-600:#854F0B; --amber-800:#633806;
  --purple-50:#EEEDFE; --purple-600:#534AB7; --purple-800:#3C3489;
  --red-50:#FCEBEB; --red-600:#A32D2D; --red-800:#791F1F;
}
.stApp { background:#e8e6e0; color:var(--text-primary); }
.block-container { max-width:1180px; padding-top:1.2rem; padding-bottom:1.2rem; }
[data-testid="stHeader"] { background:transparent; }
.tc-shell { border:0.5px solid var(--border-light); border-radius:12px; overflow:hidden; background:var(--bg-primary); }
.tc-card { border:0.5px solid var(--border-light); border-radius:8px; background:var(--bg-secondary); padding:10px 12px; margin-bottom:8px; }
.tc-label { font-size:10px; color:var(--text-tertiary); text-transform:uppercase; letter-spacing:.06em; margin-bottom:4px; }
.tc-value { font-size:12px; font-weight:600; color:var(--text-primary); }
.tc-badge { display:inline-block; font-size:10px; padding:2px 7px; border-radius:8px; font-weight:600; margin-right:4px; }
.tc-badge-blue { background:var(--blue-50); color:var(--blue-800); }
.tc-badge-green { background:var(--green-50); color:var(--green-800); }
.tc-badge-amber { background:var(--amber-50); color:var(--amber-800); }
.tc-approval { border:0.5px solid var(--border-mid); border-radius:12px; overflow:hidden; margin:10px 0; }
.tc-approval-head { background:var(--amber-50); color:var(--amber-800); padding:10px 14px; font-size:12px; font-weight:700; border-bottom:0.5px solid var(--border-light); }
.tc-approval-body { padding:12px 14px; font-size:12px; color:var(--text-secondary); }
.tc-event { display:flex; gap:10px; border-bottom:0.5px solid var(--border-light); padding:8px 4px; }
.tc-time { min-width:92px; font-size:10px; color:var(--text-tertiary); }
.tc-event-title { font-size:12px; font-weight:700; }
.tc-event-sub { font-size:11px; color:var(--text-secondary); }
.tc-trace { border:0.5px solid var(--border-light); border-radius:8px; padding:9px 11px; margin-bottom:8px; background:#fff; }
.tc-trace-title { font-size:11px; font-weight:700; }
.tc-trace-body { font-size:11px; color:var(--text-secondary); line-height:1.45; }
.tc-trace-meta { font-size:10px; color:var(--text-tertiary); line-height:1.4; margin-top:4px; }
</style>
"""

from __future__ import annotations

STYLE = """
*,*:before,*:after{box-sizing:border-box}
html{overflow-x:hidden}
body{margin:0;background:#f4f7f9;color:#172033;font-family:Inter,Aptos,Arial,sans-serif;overflow-x:hidden}
a{color:#176b87;text-decoration:none}a:hover{text-decoration:underline}
.top{background:#173a47;color:white;padding:22px 32px}
.top h1{margin:0;font-size:28px}.top p{margin:6px 0 0;color:#d6e6eb}
.wrap{padding:24px 32px;max-width:1420px;margin:0 auto}
.bar{display:flex;gap:12px;align-items:center;margin-bottom:18px;flex-wrap:wrap}
.project-switcher{background:white;border:1px solid #dce3e8;border-radius:8px;padding:16px;margin-bottom:18px;display:grid;grid-template-columns:1fr auto;gap:16px;align-items:end}.project-switcher h2{margin:0;color:#173a47;font-size:22px}.project-switcher p{margin:6px 0 0;color:#667782}.project-switcher form{display:flex;gap:10px;align-items:end;flex-wrap:wrap}.project-select-field label{display:block;color:#173a47;font-weight:800;font-size:13px;margin-bottom:6px}.project-select-field select{min-width:320px;font-weight:800}.quick-project{grid-column:1/-1;border-top:1px solid #e5ebef;padding-top:14px}.quick-project summary{cursor:pointer;display:inline-flex;align-items:center;gap:8px;color:#1f6f85;font-weight:900}.quick-project summary::-webkit-details-marker{display:none}.quick-project summary:before{content:"+";display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#e9f1f4;color:#173a47}.quick-project[open] summary:before{content:"-"}.quick-project-form{margin-top:14px;display:grid;grid-template-columns:minmax(240px,.75fr) 1fr auto;gap:12px;align-items:end}.quick-project-form .field{margin:0}.quick-project-form textarea{min-height:88px}.quick-project-actions{display:flex;gap:10px;flex-wrap:wrap}
.collect-panel{background:white;border:1px solid #dce3e8;border-radius:8px;padding:14px;margin-bottom:18px}.collect-panel .bar{margin-bottom:12px}.source-picker-head{display:flex;justify-content:space-between;gap:12px;margin-bottom:10px}.source-picker-head b{color:#173a47}.source-picker-head span{font-size:12px;color:#667782}.source-checks{display:grid;grid-template-columns:repeat(4,minmax(170px,1fr));gap:10px}.source-check{display:flex;gap:9px;align-items:flex-start;border:1px solid #dce3e8;background:#f8fbfc;border-radius:8px;padding:10px;color:#173a47}.source-check input{margin-top:3px}.source-check b{display:block;font-size:13px}.source-check small{display:block;color:#667782;font-size:12px;margin-top:2px;line-height:1.25}.source-check.disabled{opacity:.52;background:#f1f4f6}
.btn{border:0;background:#1f6f85;color:#fff;padding:10px 14px;border-radius:6px;font-weight:700;cursor:pointer;display:inline-block}
.btn.secondary{background:#173a47}.btn.light{background:#e9f1f4;color:#173a47;border:1px solid #cbd5dc}
.input,.select{border:1px solid #cbd5dc;border-radius:6px;padding:9px;background:white}
.input[type=date]{min-width:145px}.textarea{border:1px solid #cbd5dc;border-radius:6px;padding:10px;background:white;width:100%;min-height:110px;box-sizing:border-box;font-family:inherit}
.grid{display:grid;grid-template-columns:repeat(4,minmax(160px,1fr));gap:14px;margin-bottom:18px}.metric-grid{display:grid;grid-template-columns:repeat(6,minmax(130px,1fr));gap:12px;margin-bottom:18px}
.card{background:white;border:1px solid #dce3e8;border-radius:8px;padding:16px}
.k{color:#5a6b75;font-size:13px;font-weight:700}.v{font-size:30px;font-weight:800;margin-top:5px;color:#173a47}.metric{background:white;border:1px solid #dce3e8;border-radius:8px;padding:14px;min-height:92px}.metric .value{font-size:27px;font-weight:900;color:#173a47;margin-top:7px}.metric .caption{font-size:12px;color:#667782;margin-top:5px;line-height:1.25}
.layout{display:grid;grid-template-columns:1.5fr .8fr;gap:18px}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}.viz-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:18px;margin-bottom:18px}.viz-grid>*{min-width:0}.viz-wide{grid-column:1/-1}
.nav{display:flex;gap:10px;margin-top:14px;flex-wrap:wrap}.nav a{color:white;border:1px solid rgba(255,255,255,.35);border-radius:6px;padding:7px 10px}.nav a.active,.nav a:hover{background:rgba(255,255,255,.14);text-decoration:none}
.nav .user-badge{margin-left:auto;color:#d6e6eb;border:1px solid rgba(255,255,255,.22);border-radius:6px;padding:7px 10px;font-size:13px}.nav .logout{color:#d6e6eb}
table{width:100%;border-collapse:collapse;background:white;border:1px solid #dce3e8;border-radius:8px;overflow:hidden}
th{background:#1f4e5f;color:#fff;text-align:left;font-size:13px;padding:10px}
td{border-top:1px solid #e5ebef;padding:10px;vertical-align:top;font-size:14px}
.pill{display:inline-block;border-radius:999px;padding:3px 9px;font-size:12px;font-weight:700}
.positive{background:#dff5e8;color:#116038}.negative{background:#fde2e0;color:#9c2a24}.neutral{background:#edf1f4;color:#52606a}
.muted{color:#667782;font-size:13px}.snippet{color:#3e4b54}.side h3{margin:0 0 10px}.list{display:grid;gap:8px}.row{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid #e8eef2;padding:6px 0}
.steps{display:grid;grid-template-columns:repeat(3,minmax(180px,1fr));gap:14px;margin:0 0 18px}
.step{display:block;color:#172033;transition:.16s ease;position:relative}.step:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(23,58,71,.10);text-decoration:none}.step b{display:block;margin-bottom:6px;color:#173a47}.step:after{content:"Открыть";position:absolute;right:16px;bottom:14px;color:#1f6f85;font-size:13px;font-weight:800}
.barline{display:flex;align-items:center;gap:10px;margin:8px 0}.barline span:first-child{width:160px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.track{height:12px;background:#edf1f4;border-radius:999px;flex:1;overflow:hidden}.fill{height:100%;background:#1f6f85}.fill.neg{background:#d95d59}.fill.pos{background:#2fa76d}.fill.neu{background:#7e8b95}
.chart-title{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:14px}.chart-title h3{margin:0;color:#172033}.chart-title span{font-size:12px;color:#667782}.trend-chart{height:276px;width:100%;overflow:hidden}.trend-chart svg{display:block;width:100%;height:100%;background:#fbfefd;border-radius:8px}.trend-axis{stroke:#dfe7e4;stroke-width:1;stroke-dasharray:3 4}.trend-line{fill:none;stroke:#43df75;stroke-width:4;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 3px 3px rgba(67,223,117,.22))}.trend-area{fill:url(#trendFill)}.trend-dot{fill:#f8fff9;stroke:#43df75;stroke-width:4}.trend-scale{display:flex;justify-content:space-between;gap:10px;margin:8px 2px 0;color:#667782;font-size:12px;font-weight:800}.trend-scale span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.trend-summary{display:flex;justify-content:space-between;gap:10px;margin-top:8px;color:#3e4b54;font-size:12px;font-weight:800}.trend-summary b{color:#173a47}.tone-stack{height:22px;border-radius:999px;overflow:hidden;display:flex;background:#edf1f4;margin:8px 0 14px}.tone-part{height:100%}.tone-pos{background:#2fa76d}.tone-neu{background:#7e8b95}.tone-neg{background:#d95d59}.legend{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.legend-row{background:#f6f9fb;border:1px solid #e3ebef;border-radius:7px;padding:10px}.legend-row b{display:block;color:#172033}.legend-row span{font-size:12px;color:#667782}.dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px}.spark{height:170px;display:flex;align-items:flex-end;gap:8px;border-left:1px solid #dce3e8;border-bottom:1px solid #dce3e8;padding:12px 8px 24px;margin-top:6px}.spark-col{flex:1;min-width:12px;background:#1f6f85;border-radius:4px 4px 0 0;position:relative}.spark-col span{position:absolute;bottom:-22px;left:50%;transform:translateX(-50%);font-size:11px;color:#667782;white-space:nowrap}.spark-col b{position:absolute;top:-20px;left:50%;transform:translateX(-50%);font-size:11px;color:#173a47}.insights{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.insight{background:#f6f9fb;border:1px solid #dce3e8;border-radius:8px;padding:12px}.insight b{display:block;color:#173a47;margin-bottom:5px}.metric-list{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.metric-pill{background:#f6f9fb;border:1px solid #dce3e8;border-radius:8px;padding:0;overflow:hidden}.metric-pill summary{list-style:none;cursor:pointer;padding:14px;min-height:126px}.metric-pill summary::-webkit-details-marker{display:none}.metric-pill summary:after{content:"Открыть расчет";display:block;margin-top:9px;color:#1f6f85;font-size:12px;font-weight:800}.metric-pill[open] summary{background:#e9f1f4}.metric-pill b{display:block;color:#173a47;margin-bottom:4px}.metric-number{font-size:25px;font-weight:900;color:#172033;margin:8px 0 3px;line-height:1}.metric-state{display:inline-block;margin-top:7px;border-radius:999px;padding:4px 8px;background:#edf3f6;color:#38515c;font-size:11px;font-weight:800}.metric-state.good{background:#dff5e8;color:#116038}.metric-state.warn{background:#fff1d6;color:#8a5a00}.metric-state.bad{background:#fde2e0;color:#9c2a24}.metric-detail{border-top:1px solid #dce3e8;padding:12px;background:white}.metric-detail p{margin:0 0 8px;color:#3e4b54;font-size:13px;line-height:1.4}.metric-detail ul{margin:0;padding-left:18px;color:#667782;font-size:13px;line-height:1.45}.metric-mini{display:grid;grid-template-columns:1fr auto;gap:8px;border-top:1px solid #eef3f6;padding-top:7px;margin-top:7px;font-size:12px;color:#667782}.metric-mini b{color:#173a47;margin:0}.coverage-note{margin-top:12px;background:#f6f9fb;border:1px solid #e3ebef;border-radius:8px;padding:12px;color:#3e4b54;font-size:13px;line-height:1.45}
.settings{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(360px,100%),1fr));gap:18px;min-width:0}.settings>*{min-width:0}.field{margin-bottom:14px;min-width:0}.field label{display:block;font-weight:700;margin-bottom:6px;color:#173a47;overflow-wrap:anywhere}.field .input,.field .textarea{max-width:100%}.status{font-size:12px;font-weight:800;border-radius:999px;padding:3px 8px;white-space:nowrap}.on{background:#dff5e8;color:#116038}.off{background:#fde2e0;color:#9c2a24}.hint{font-size:13px;color:#667782;line-height:1.45}
.pagehead{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:18px}.pagehead h2{margin:0;font-size:24px;color:#173a47}.pagehead p{margin:6px 0 0;color:#667782}
.provider{border:1px solid #dce3e8;border-radius:8px;background:white;padding:18px;min-width:0;max-width:100%;overflow:hidden}.provider-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:12px;min-width:0}.provider-head>div{min-width:0}.provider h3{margin:0;color:#173a47;overflow-wrap:anywhere}.provider small{display:block;color:#667782;margin-top:4px;line-height:1.35}.provider .meta{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.chip{background:#edf3f6;border:1px solid #d7e2e8;border-radius:999px;padding:4px 8px;font-size:12px;color:#38515c;font-weight:700}.split{display:grid;grid-template-columns:minmax(220px,280px) minmax(0,1fr);gap:18px;min-width:0}.split>*{min-width:0}.side-nav{position:sticky;top:16px;align-self:start}.side-nav a{display:block;padding:10px 12px;border-radius:6px;color:#173a47;font-weight:700}.side-nav a:hover{background:#e9f1f4;text-decoration:none}.section-title{font-size:18px;color:#173a47;margin:0 0 10px}
.project-list{display:grid;gap:10px;margin-top:12px}.project-card{display:block;border:1px solid #dce3e8;background:#f8fbfc;border-radius:8px;padding:12px;color:#173a47}.project-card:hover,.project-card.active{background:#e9f4f7;border-color:#9bc4cf;text-decoration:none}.project-card b{display:block}.project-card span{display:block;color:#1f6f85;font-size:12px;font-weight:800;margin-top:4px}.project-card small{display:block;color:#667782;margin-top:5px;line-height:1.25}.query-helper{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}.query-helper .insight{min-height:72px}
.login-shell{min-height:100vh;display:grid;place-items:center;padding:24px;background:linear-gradient(135deg,#173a47,#f4f7f9)}.login-card{width:min(430px,100%);background:white;border:1px solid #dce3e8;border-radius:8px;padding:28px;box-shadow:0 20px 60px rgba(23,58,71,.18)}.login-card h1{margin:0;color:#173a47}.login-card p{color:#667782;line-height:1.45}.admin-grid{display:grid;grid-template-columns:360px 1fr;gap:18px}.danger{color:#9c2a24;font-weight:800}
.agent-hero{display:grid;grid-template-columns:1.1fr .9fr;gap:14px;align-items:stretch}.agent-card{background:#f8fbfc;border:1px solid #dce3e8;border-radius:8px;padding:14px}.agent-card h4{margin:0 0 8px;color:#173a47}.agent-card p{margin:0;color:#3e4b54;line-height:1.45}.agent-score{font-size:36px;font-weight:900;color:#173a47;margin-top:8px}.agent-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:12px}.agent-list{display:grid;gap:8px}.agent-list li{margin-bottom:6px;color:#3e4b54;line-height:1.4}.agent-tags{display:flex;gap:8px;flex-wrap:wrap}.agent-tag{background:#edf3f6;border:1px solid #d7e2e8;border-radius:999px;padding:5px 9px;font-size:12px;color:#38515c;font-weight:800}.risk-low{background:#dff5e8;color:#116038}.risk-mid{background:#fff1d6;color:#8a5a00}.risk-high{background:#fde2e0;color:#9c2a24}.agent-evidence{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.agent-toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.ai-chat{display:grid;grid-template-columns:.9fr 1.1fr;gap:14px;margin-top:14px}.ai-chat-panel{background:rgba(255,255,255,.72);border:1px solid #dce8eb;border-radius:12px;padding:14px}.ai-chat-panel h4{margin:0 0 8px;color:#123441}.ai-chat-panel textarea{min-height:128px;resize:vertical}.ai-answer{background:#f8fbfb;border:1px solid #dce8eb;border-radius:12px;padding:14px;color:#253743;line-height:1.55}.ai-answer p{margin:0 0 10px}.ai-answer p:last-child{margin-bottom:0}.ai-answer b{color:#102f3a}.ai-question{display:inline-block;background:#e8f4f7;border:1px solid #cce2e8;border-radius:12px;padding:10px 12px;color:#173a47;font-weight:800;margin-bottom:10px}.ai-suggestions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.ai-suggestions button{border:1px solid #d7e5ea;background:#fff;color:#1f6f85;border-radius:999px;padding:7px 10px;font-weight:800;cursor:pointer}
/* Product design pass: calmer SaaS surface, stronger hierarchy, warmer guidance. */
body{background:#f6f8f7;color:#1b2633;-webkit-font-smoothing:antialiased}
a{color:#166f86}
.top{background:linear-gradient(135deg,#123441 0%,#1f5261 62%,#2e6d67 100%);padding:26px 34px 24px;box-shadow:0 18px 45px rgba(18,52,65,.12)}
.top h1{font-size:30px;font-weight:900;letter-spacing:0}.top p{max-width:980px;color:#dcebef;line-height:1.45}
.wrap{max-width:1480px;padding:24px 34px 42px}
.nav{gap:8px;align-items:center}.nav a{border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.06);border-radius:8px;padding:8px 11px;font-weight:800}.nav a.active,.nav a:hover{background:rgba(255,255,255,.18);border-color:rgba(255,255,255,.35)}.nav .user-badge{border-radius:8px;background:rgba(255,255,255,.08);font-weight:800}
.card,.metric,.project-switcher,.collect-panel,.provider,.project-card,table{border-color:#d9e3e8;box-shadow:0 10px 28px rgba(23,58,71,.06)}
.project-switcher{padding:18px;background:linear-gradient(180deg,#fff,#fbfdfd)}.project-switcher h2,.chart-title h3,.pagehead h2{color:#123441}.project-switcher p,.muted,.hint{color:#647783}
.steps{gap:12px}.step{background:#fff;border-color:#d9e3e8;min-height:126px}.step b{font-size:18px}.step span{display:block;max-width:88%;line-height:1.38}.step:after{content:"Перейти";bottom:16px}
.collect-panel{padding:16px 18px;background:#fff}.source-picker-head b{font-size:20px}.source-picker-head span{line-height:1.35}
.btn{border-radius:8px;padding:10px 15px;font-weight:900;box-shadow:0 6px 14px rgba(31,111,133,.14)}.btn:hover{text-decoration:none;filter:brightness(.98)}.btn.light{background:#f1f6f8;border-color:#cfdae1;box-shadow:none}.btn.secondary{background:#123441}
.input,.select,.textarea{border-color:#cdd9df;border-radius:8px;padding:10px 12px;color:#1b2633}.input:focus,.select:focus,.textarea:focus{outline:3px solid rgba(31,111,133,.14);border-color:#1f6f85}
.metric-grid{gap:13px}.metric{padding:16px;background:linear-gradient(180deg,#fff,#fbfdfd);min-height:108px}.metric .value{font-size:30px;color:#123441}.metric .caption{font-size:13px;color:#647783}.k{font-weight:900;color:#5b6e78}
.viz-grid{gap:18px}.chart-title{margin-bottom:16px}.chart-title h3{font-size:21px}.chart-title span{font-size:13px;line-height:1.35}
.agent-focus{border:1px solid #c9dfe5;background:linear-gradient(135deg,#ffffff 0%,#f5fbfc 58%,#eef8f3 100%)}.agent-focus .chart-title h3:before{content:"";display:inline-block;width:9px;height:9px;border-radius:50%;background:#43df75;margin-right:8px;vertical-align:middle;box-shadow:0 0 0 5px rgba(67,223,117,.13)}
.agent-card{background:rgba(255,255,255,.78);border-color:#d8e6eb;padding:16px}.agent-card h4{font-size:17px;color:#123441}.agent-card p{color:#374b55}.agent-score{font-size:38px;color:#123441}.agent-list{padding-left:19px}.agent-list li{color:#374b55}.agent-tag,.chip{background:#eef5f7;border-color:#d6e4ea;color:#36535f}
.metric-state{border-radius:999px;padding:5px 9px}.risk-mid{background:#fff2d8;color:#855600}.risk-low{background:#dff5e8;color:#116038}.risk-high{background:#fde2e0;color:#9c2a24}
.coverage-note{background:#f7faf9;border-color:#dce8e3;color:#41535b;border-left:4px solid #9ccfbd}
th{background:#1e5363;padding:12px 11px}td{padding:12px 11px}.snippet{line-height:1.38;color:#3d4f58}.pill{padding:4px 10px;font-weight:900}
.barline span:first-child{color:#374b55}.track{background:#ecf2f4}.fill{background:#1f7d92}
.tone-stack{height:24px}.legend-row,.insight,.metric-pill{background:#f8fbfc;border-color:#dce6eb}.insight b,.metric-pill b{color:#123441}
.side .card{box-shadow:none}.row{padding:8px 0}.row b{color:#123441}
.provider{background:linear-gradient(180deg,#fff,#fbfdfd)}.status{padding:4px 9px}
/* Premium pass: editorial command center and softer enterprise rhythm. */
body{background:#f7f8f6;color:#18222f}
.top{background:#112f3a;padding:28px 36px 26px;position:relative;overflow:hidden}
.top:after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:linear-gradient(90deg,rgba(223,184,111,.35),rgba(255,255,255,.2),rgba(67,223,117,.25))}
.top h1{font-size:32px}.top p{font-size:15px;color:#d8e8e6}
.nav a{background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.18);backdrop-filter:blur(10px)}.nav a.active{background:#ffffff;color:#123441;border-color:#ffffff}.nav .logout{padding:8px 2px}
.wrap{padding-top:28px}
.workspace-hero{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(360px,.75fr);gap:18px;margin-bottom:18px}
.hero-main,.hero-side{background:#fff;border:1px solid #dbe5e7;border-radius:8px;box-shadow:0 18px 45px rgba(18,47,58,.08)}
.hero-main{padding:22px 24px;background:linear-gradient(135deg,#ffffff 0%,#fbfdfc 60%,#f1f8f4 100%)}
.eyebrow{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:#8a6a2b;font-weight:900;margin-bottom:9px}
.hero-main h2{margin:0;color:#102f3a;font-size:28px;line-height:1.12;letter-spacing:0}
.hero-main p{margin:10px 0 0;color:#526772;line-height:1.48;max-width:860px}
.hero-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.hero-actions .btn{padding:11px 16px}.hero-inline-form{display:inline-flex;margin:0}
.hero-side{padding:18px;background:#fbfcfc}
.hero-side h3{margin:0 0 12px;color:#102f3a;font-size:17px}
.signal-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.signal{background:#fff;border:1px solid #e0e8eb;border-radius:8px;padding:12px}.signal b{display:block;color:#102f3a;font-size:22px;line-height:1}.signal span{display:block;color:#647783;font-size:12px;margin-top:6px}.signal.accent{background:#102f3a;border-color:#102f3a}.signal.accent b,.signal.accent span{color:#fff}.signal.gold{background:#fff8ea;border-color:#ead7ad}
.premium-section-title{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin:26px 0 12px}.premium-section-title h2{margin:0;color:#102f3a;font-size:22px}.premium-section-title p{margin:4px 0 0;color:#647783;font-size:13px}
.steps{grid-template-columns:repeat(3,minmax(0,1fr));margin-bottom:20px}.step{padding:18px 18px 42px;background:linear-gradient(180deg,#ffffff,#fbfcfc)}.step b{font-size:17px}.step span{max-width:none}
.project-switcher{display:none}
.collect-panel{padding:0;overflow:hidden;border-color:#dbe5e7}.collect-panel .source-picker-head{padding:18px 20px;margin:0;background:#fff}.collect-panel .bar{padding:0 20px 18px;margin:0}.source-picker-head b{font-size:18px}.source-picker-head span{font-size:13px}
.filter-bar{background:#fff;border:1px solid #dbe5e7;border-radius:8px;padding:14px;box-shadow:0 12px 30px rgba(18,47,58,.05)}
.metric-grid{grid-template-columns:repeat(6,minmax(150px,1fr));gap:14px}.metric{border-color:#dbe5e7;box-shadow:0 14px 34px rgba(18,47,58,.06)}.metric:hover{transform:translateY(-1px);transition:.16s ease}.metric .value{font-size:32px}.metric .k{font-size:12px;text-transform:uppercase;letter-spacing:.035em}.metric .caption{font-size:12px}
.agent-focus{box-shadow:0 22px 55px rgba(18,47,58,.09);border-color:#cfe0e4;background:linear-gradient(135deg,#ffffff 0%,#f8fcfb 50%,#eef8f3 100%)}.agent-focus .chart-title h3{font-size:24px}
.agent-card{box-shadow:inset 0 1px 0 rgba(255,255,255,.8)}.agent-score{font-size:40px}
.trend-chart{height:310px}.trend-chart svg{background:linear-gradient(180deg,#fbfefd,#ffffff)}
.card{box-shadow:0 14px 34px rgba(18,47,58,.06)}.card h3{color:#102f3a}
table{box-shadow:0 14px 34px rgba(18,47,58,.06)}th{background:#102f3a;font-size:12px;letter-spacing:.02em;text-transform:uppercase}td{background:#fff}tr:hover td{background:#fbfdfd}
.layout{grid-template-columns:minmax(0,1.55fr) minmax(320px,.65fr)}
/* Compact quick actions: onboarding should not dominate daily analytics. */
.quick-actions-title{margin:8px 0 8px}.quick-actions-title h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#6a7c85}.quick-actions-title p{display:none}
.quick-actions{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}.quick-actions .step{display:inline-flex;align-items:center;gap:8px;min-height:0;padding:9px 12px;border-radius:999px;background:#fff;box-shadow:0 8px 18px rgba(18,47,58,.04)}.quick-actions .step b{font-size:13px;margin:0}.quick-actions .step span{display:none}.quick-actions .step:after{content:"";position:static;width:6px;height:6px;border-right:2px solid #1f6f85;border-bottom:2px solid #1f6f85;transform:rotate(-45deg);margin-left:2px}.quick-actions .step:hover{transform:none;box-shadow:0 8px 20px rgba(18,47,58,.08)}
.widget-title{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}.widget-title h3{margin:0;color:#102f3a}.widget-tools{position:relative}.gear{width:32px;height:32px;border:1px solid #d6e2e7;border-radius:8px;background:#f8fbfc;color:#36535f;cursor:pointer;font-size:16px;line-height:1}.widget-settings{position:absolute;right:0;top:38px;z-index:5;width:292px;background:#fff;border:1px solid #dbe5e7;border-radius:8px;box-shadow:0 18px 45px rgba(18,47,58,.16);padding:14px;display:none}.widget-tools:hover .widget-settings,.widget-tools:focus-within .widget-settings{display:block}.widget-settings h4{margin:0 0 10px;color:#102f3a}.widget-settings .field{margin-bottom:10px}.widget-settings label{display:block;font-size:12px;font-weight:900;color:#5b6e78;margin-bottom:5px}.widget-settings .select{width:100%}.widget-settings .btn{width:100%;text-align:center;justify-content:center}.mini-help{font-size:12px;color:#647783;line-height:1.35;margin-top:8px}
.widget-settings .input{width:100%}.period-summary{display:flex;gap:10px;flex-wrap:wrap;color:#536872;font-size:13px;font-weight:850;margin:8px 0 0}.period-summary b{color:#102f3a}.spark-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;padding-bottom:4px}.spark-scroll .spark{min-width:max(100%,calc(var(--bars,14) * 34px))}
.metric-link{display:block;color:inherit}.metric-link:hover{text-decoration:none;transform:translateY(-1px)}
.help-dot{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:50%;background:#eef6f7;color:#176b87;font-size:12px;font-weight:950;margin-left:6px;position:relative;cursor:help}.help-dot:hover:after{content:attr(data-tip);position:absolute;left:0;top:24px;width:min(260px,70vw);max-width:calc(100vw - 32px);padding:10px 12px;border-radius:8px;background:#102f3a;color:white;font-size:12px;font-weight:700;line-height:1.35;box-shadow:0 14px 34px rgba(16,47,58,.22);z-index:20}
.query-suggest-box{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0 10px}.query-suggest-box .hint{margin:0}.tone-stage-link{display:block;color:inherit}.tone-stage-link:hover{text-decoration:none;background:rgba(255,255,255,.5)}
.barline a:first-child{width:160px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#176b87;font-weight:850}
/* Glass analytics reference: frosted panels, soft cyan charts, premium depth. */
body{background:linear-gradient(180deg,#12313c 0%,#dfeee9 34%,#f6f8f6 100%) fixed}
.wrap{position:relative}.wrap:before{content:"";position:absolute;inset:0 28px auto;height:220px;background:linear-gradient(90deg,rgba(255,255,255,.18),rgba(116,221,219,.12),rgba(255,255,255,.08));border-radius:8px;pointer-events:none;z-index:-1}
.top{background:linear-gradient(135deg,rgba(13,42,54,.96),rgba(21,78,91,.93));box-shadow:0 24px 70px rgba(10,33,43,.24)}
.workspace-hero,.metric,.card,.collect-panel,.filter-bar,.hero-main,.hero-side,.provider,.project-card,table{background:linear-gradient(145deg,rgba(255,255,255,.72),rgba(224,245,244,.50));border:1px solid rgba(255,255,255,.58);box-shadow:0 24px 70px rgba(13,61,73,.13),inset 0 1px 0 rgba(255,255,255,.72);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px)}
.hero-main{background:linear-gradient(145deg,rgba(255,255,255,.78),rgba(217,244,243,.52))}.hero-side{background:linear-gradient(145deg,rgba(248,253,253,.76),rgba(196,232,235,.40))}
.signal{background:linear-gradient(145deg,rgba(255,255,255,.68),rgba(221,244,244,.45));border-color:rgba(255,255,255,.62);box-shadow:inset 0 1px 0 rgba(255,255,255,.75)}.signal.accent{background:linear-gradient(145deg,#143b48,#1c6c78)}.signal.gold{background:linear-gradient(145deg,#fff8e8,#e9f4ee)}
.metric{position:relative;overflow:hidden}.metric:after{content:"";position:absolute;left:16px;right:16px;bottom:0;height:3px;background:linear-gradient(90deg,#17b8d9,#37d9c5,#d7b56f);opacity:.75}.metric .value{font-size:34px;font-weight:950;color:#122c37}.metric .k{color:#45616b}.metric .caption{color:#5e747d}
.agent-focus{background:linear-gradient(145deg,rgba(255,255,255,.80),rgba(202,239,236,.48));border-color:rgba(255,255,255,.65);box-shadow:0 30px 90px rgba(13,61,73,.18),inset 0 1px 0 rgba(255,255,255,.74)}.agent-card{background:linear-gradient(145deg,rgba(255,255,255,.62),rgba(226,247,246,.40));border-color:rgba(255,255,255,.62)}
.agent-score{color:#102f3a;text-shadow:0 1px 0 rgba(255,255,255,.45)}.agent-tag,.chip{background:rgba(255,255,255,.52);border-color:rgba(255,255,255,.72)}
.trend-chart svg{background:linear-gradient(145deg,rgba(246,253,252,.76),rgba(214,244,242,.34))}.trend-line{stroke:#48e2df;stroke-width:5;filter:drop-shadow(0 8px 10px rgba(37,207,205,.25))}.trend-dot{stroke:#48e2df}.trend-axis{stroke:rgba(39,91,102,.18)}.spark{border-color:rgba(47,93,104,.20)}.spark-col{background:linear-gradient(180deg,#25c6dc,#1f7d92);box-shadow:0 8px 18px rgba(31,125,146,.18)}
.tone-pos{background:linear-gradient(90deg,#32c783,#68dfb0)}.tone-neu{background:linear-gradient(90deg,#8fa1aa,#aebdc2)}.tone-neg{background:linear-gradient(90deg,#d95d59,#ee8d80)}
.fill{background:linear-gradient(90deg,#1f7d92,#22c7d7)}.fill.pos{background:linear-gradient(90deg,#2fa76d,#5ed8a0)}.fill.neg{background:linear-gradient(90deg,#d95d59,#ef8d80)}
th{background:linear-gradient(135deg,#123441,#1f5d6c)}td{background:rgba(255,255,255,.64)}tr:hover td{background:rgba(238,250,249,.82)}
.gear{background:rgba(255,255,255,.58);border-color:rgba(255,255,255,.8);box-shadow:0 8px 20px rgba(18,47,58,.08)}.widget-settings{background:rgba(255,255,255,.88);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border-color:rgba(255,255,255,.72)}
/* Refined premium correction: fewer competing gradients, clearer hierarchy. */
body{background:linear-gradient(180deg,#eef5f4 0%,#f7f8f6 42%,#f7f8f6 100%) fixed;color:#18222f}
.top{background:#102f3a;box-shadow:0 18px 42px rgba(10,33,43,.18)}
.wrap:before{display:none}
.workspace-hero,.metric,.card,.collect-panel,.filter-bar,.hero-main,.hero-side,.provider,.project-card,table{background:rgba(255,255,255,.88);border:1px solid rgba(201,220,225,.86);box-shadow:0 18px 42px rgba(20,66,78,.08),inset 0 1px 0 rgba(255,255,255,.76);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
.hero-main{background:linear-gradient(135deg,rgba(255,255,255,.94),rgba(242,249,248,.92))}.hero-side{background:rgba(255,255,255,.86)}
.hero-main,.hero-side,.card,.metric,.collect-panel,.filter-bar{border-radius:8px}
.signal{background:#fff;border:1px solid #dce8eb;box-shadow:none}.signal.accent{background:#123441;border-color:#123441}.signal.gold{background:#fff9ec;border-color:#ecdcb8}
.metric:after{height:2px;background:#26bfd0;opacity:.7}.metric .value{color:#102f3a}.metric .k{color:#506871}.metric .caption{color:#667982}
.agent-focus{background:rgba(255,255,255,.90);border-color:#cfe0e4;box-shadow:0 22px 54px rgba(20,66,78,.10),inset 0 1px 0 rgba(255,255,255,.76)}.agent-card{background:#f8fbfb;border-color:#dce8eb;box-shadow:none}
.agent-focus .chart-title h3:before{background:#26bfd0;box-shadow:0 0 0 5px rgba(38,191,208,.14)}
.agent-score{text-shadow:none}.agent-tag,.chip{background:#eef6f7;border-color:#d8e8eb;color:#37535d}
.trend-chart svg{background:#fbfefd}.trend-line{stroke:#26bfd0;stroke-width:4;filter:drop-shadow(0 5px 8px rgba(38,191,208,.18))}.trend-dot{stroke:#26bfd0}.trend-axis{stroke:#dfe9e7}
.spark-col{background:linear-gradient(180deg,#28bfd1,#1f7d92);box-shadow:0 6px 14px rgba(31,125,146,.14)}
.fill{background:#1f7d92}.fill.pos{background:#2fa76d}.fill.neg{background:#d95d59}
.tone-pos{background:#2fa76d}.tone-neu{background:#8fa1aa}.tone-neg{background:#d95d59}
th{background:#123441}td{background:#fff}tr:hover td{background:#f8fbfb}
.coverage-note{background:#fbfdfc;border-color:#dce8e3;border-left-color:#80cbbb}
.gear{background:#fff;border-color:#d6e2e7;box-shadow:0 6px 16px rgba(18,47,58,.06)}.widget-settings{background:#fff;border-color:#dbe5e7;backdrop-filter:none;-webkit-backdrop-filter:none}
/* Command center refinement: compact status panel, no visual crowding. */
.workspace-hero{grid-template-columns:minmax(0,1.55fr) minmax(300px,.45fr);gap:14px}
.hero-main{padding:24px 26px;min-height:230px}.hero-side{padding:16px;min-height:230px}
.hero-main h2{font-size:27px;max-width:860px}.hero-main p{max-width:780px}
.hero-side h3{font-size:16px;margin-bottom:10px;white-space:normal}
.signal-grid{gap:8px}.signal{padding:10px 12px;min-height:68px}.signal b{font-size:20px}.signal span{font-size:12px;line-height:1.25}.signal.accent b{font-size:22px}.hero-side .coverage-note{margin-top:10px;padding:10px 12px;font-size:12px}
/* Left SaaS shell: collapsible tool panel and calmer workspace background. */
body.with-sidebar{padding-left:284px;background:linear-gradient(135deg,#dceefa 0%,#eef5fb 48%,#f8f8fb 100%) fixed;transition:padding-left .22s ease}
body.with-sidebar.sidebar-collapsed{padding-left:104px}
.with-sidebar .top{background:transparent;color:#102f3a;box-shadow:none;padding:30px 34px 8px;overflow:visible}
.with-sidebar .top:after{display:none}
.with-sidebar .top h1{color:#102f3a;font-size:30px}
.with-sidebar .top p{color:#61747d;max-width:980px}
.with-sidebar .wrap{max-width:none;padding:18px 34px 44px;margin:0}
.nav{position:fixed;left:20px;top:20px;bottom:20px;width:232px;margin:0;padding:14px;display:flex;flex-direction:column;gap:14px;z-index:40;border-radius:8px;background:rgba(255,255,255,.64);border:1px solid rgba(255,255,255,.74);box-shadow:0 24px 70px rgba(37,78,98,.14),inset 0 1px 0 rgba(255,255,255,.82);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);transition:width .22s ease,padding .22s ease}
.nav-brand{display:flex;align-items:center;gap:10px;min-height:46px;padding:4px 4px 12px;border-bottom:1px solid rgba(83,119,134,.16)}
.brand-mark{width:38px;height:38px;display:grid;place-items:center;border-radius:8px;background:#102f3a;color:white;font-size:13px;font-weight:950;letter-spacing:.04em;box-shadow:0 12px 24px rgba(16,47,58,.18);flex:0 0 auto}
.nav-brand b,.nav-user b{display:block;color:#102f3a;font-size:15px;line-height:1.1}
.nav-brand small,.nav-user small{display:block;color:#71838b;font-size:11px;margin-top:3px;line-height:1.1}
.nav-links{display:grid;gap:6px}
.nav a{display:flex;align-items:center;gap:10px;color:#263946;border:0;border-radius:8px;background:transparent;padding:10px 11px;font-weight:850;line-height:1.1;min-height:22px}
.nav a:hover{background:rgba(255,255,255,.68);color:#102f3a;text-decoration:none;box-shadow:inset 0 0 0 1px rgba(214,229,234,.8)}
.nav a.active{background:#fff;color:#102f3a;box-shadow:0 12px 30px rgba(37,78,98,.10),inset 0 0 0 1px rgba(219,232,236,.9)}
.nav-ico{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;background:rgba(255,255,255,.72);color:#123441;font-size:15px;font-weight:950;box-shadow:inset 0 0 0 1px rgba(219,232,236,.8);flex:0 0 auto}
.nav a.active .nav-ico{background:#102f3a;color:white;box-shadow:none}
.nav-bottom{margin-top:auto;display:grid;gap:8px;padding-top:12px;border-top:1px solid rgba(83,119,134,.16)}
.nav-user{display:flex;align-items:center;gap:10px;padding:8px 9px;border-radius:8px;background:rgba(255,255,255,.48)}
.nav-avatar{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:#d9eee7;color:#102f3a;font-weight:950;flex:0 0 auto}
.nav .logout{color:#536872}
.sidebar-toggle{position:fixed;left:218px;top:31px;z-index:45;width:34px;height:34px;border:1px solid rgba(209,224,230,.85);border-radius:8px;background:rgba(255,255,255,.86);color:#102f3a;box-shadow:0 14px 34px rgba(37,78,98,.13);cursor:pointer;font-size:16px;transition:left .22s ease,transform .22s ease}
.sidebar-toggle:hover{background:#fff}
body.sidebar-collapsed .nav{width:56px;padding:12px}
body.sidebar-collapsed .sidebar-toggle{left:72px;transform:rotate(180deg)}
body.sidebar-collapsed .nav-label{display:none}
body.sidebar-collapsed .nav-brand{justify-content:center;padding-bottom:10px}
body.sidebar-collapsed .brand-mark{width:36px;height:36px;font-size:12px}
body.sidebar-collapsed .nav a{justify-content:center;padding:10px 8px}
body.sidebar-collapsed .nav-ico{width:32px;height:32px}
body.sidebar-collapsed .nav-user{justify-content:center;padding:7px}
body.sidebar-collapsed .nav-bottom{gap:6px}
.with-sidebar .workspace-hero,.with-sidebar .metric,.with-sidebar .card,.with-sidebar .collect-panel,.with-sidebar .filter-bar,.with-sidebar .hero-main,.with-sidebar .hero-side,.with-sidebar .provider,.with-sidebar .project-card,.with-sidebar table{background:rgba(255,255,255,.76);border-color:rgba(202,221,228,.78);box-shadow:0 18px 48px rgba(38,82,104,.09),inset 0 1px 0 rgba(255,255,255,.74);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px)}
.with-sidebar .hero-main{background:linear-gradient(135deg,rgba(255,255,255,.82),rgba(233,247,247,.66))}
.with-sidebar .hero-side{background:rgba(255,255,255,.70)}
.with-sidebar .trend-chart svg{background:linear-gradient(180deg,rgba(255,255,255,.60),rgba(237,250,249,.54))}
.with-sidebar .trend-line{stroke:#21c6d3;stroke-width:4}
.with-sidebar .trend-dot{stroke:#21c6d3}
.with-sidebar .spark-col{background:linear-gradient(180deg,#24c7d6,#277e95)}
.trend-card{background:linear-gradient(135deg,rgba(255,255,255,.78),rgba(243,232,255,.28),rgba(225,244,255,.42))!important}
.trend-card .chart-title{margin-bottom:8px}.trend-card .chart-title h3{font-size:22px}
.trend-chart{height:330px;border-radius:8px;overflow:hidden}
.trend-chart svg{background:transparent!important;border-radius:8px}
.trend-panel-bg{fill:url(#trendPanel)}
.trend-grid{stroke:rgba(80,111,124,.13);stroke-width:1}
.trend-y-label,.trend-x-label{fill:#87949b;font-size:12px;font-weight:700}
.trend-line{fill:none;stroke:#28457A!important;stroke-width:4;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 7px 10px rgba(74,169,255,.22))}
.trend-area{fill:url(#trendFill)}
.trend-point{cursor:pointer}
.trend-dot{fill:#fff!important;stroke:#28457A!important;stroke-width:4;filter:drop-shadow(0 5px 8px rgba(74,169,255,.22))}
.trend-dot-muted{fill:#eaf5ff;stroke:#90cafb;stroke-width:2}
.trend-active-band{fill:url(#trendBand)}
.trend-tooltip{fill:#17204a;filter:drop-shadow(0 12px 20px rgba(23,32,74,.22))}
.trend-tooltip-title{fill:rgba(255,255,255,.72);font-size:11px;font-weight:800}
.trend-tooltip-value{fill:#fff;font-size:17px;font-weight:950}
.trend-summary{margin-top:6px}.trend-scale{display:none}
.trend-controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end}.trend-controls .select{min-height:34px;padding:6px 10px;font-size:13px}.trend-controls .btn{min-height:34px;padding:7px 11px;font-size:13px;box-shadow:none}
.tone-card{background:linear-gradient(135deg,rgba(255,255,255,.84),rgba(238,246,255,.62))!important}
.tone-funnel-metrics{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid rgba(202,221,228,.72);margin:0 -2px 10px}
.tone-stage{padding:0 14px 12px;border-right:1px solid rgba(202,221,228,.72)}.tone-stage:last-child{border-right:0}
.tone-stage span{display:block;color:#7a8b93;font-size:12px;font-weight:850;margin-bottom:8px}.tone-stage b{display:block;color:#18222f;font-size:25px;line-height:1}.tone-stage small{display:block;color:#536872;font-size:12px;margin-top:7px}
.tone-stage.negative b{color:#b3443f}.tone-stage.positive b{color:#16855a}
.tone-funnel-viz{height:210px;overflow:hidden;border-radius:8px;background:linear-gradient(135deg,rgba(255,255,255,.52),rgba(230,244,255,.46))}
.tone-funnel-viz svg{display:block;width:100%;height:100%}.tone-funnel-shape{fill:url(#toneFunnelGradient);filter:drop-shadow(0 14px 22px rgba(53,139,210,.13))}.tone-funnel-line{stroke:rgba(120,144,156,.22);stroke-width:1.2}.tone-funnel-label{fill:#536872;font-size:13px;font-weight:850}.tone-funnel-percent{fill:#253947;font-size:17px;font-weight:950}
.with-sidebar table{table-layout:fixed;width:100%;max-width:100%}
.with-sidebar th,.with-sidebar td{overflow-wrap:break-word;word-break:normal}
.citation-panel{overflow:hidden}
.citation-table-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:8px}
.citation-table td:first-child{width:48%}.citation-table td:nth-child(2){width:12%}.citation-table td:nth-child(3){width:18%}.citation-table td:nth-child(4){width:15%}.citation-table td:nth-child(5){width:7%}
.citation-table a{font-weight:900;line-height:1.25}.citation-table .muted{line-height:1.35;overflow-wrap:break-word}.citation-table .metric-mini{grid-template-columns:minmax(0,1fr) auto}.citation-table .metric-mini span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.publication-feed{display:grid;gap:10px}
.feed-card{background:rgba(255,255,255,.78);border:1px solid rgba(202,221,228,.82);border-radius:8px;box-shadow:0 14px 34px rgba(38,82,104,.07);overflow:hidden}
.feed-card summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:130px minmax(0,1fr) minmax(120px,180px) 92px;gap:14px;align-items:start;padding:14px 16px}
.feed-card summary::-webkit-details-marker{display:none}
.feed-card[open] summary{border-bottom:1px solid rgba(202,221,228,.72);background:rgba(255,255,255,.58)}
.feed-main{display:grid;gap:5px;min-width:0}
.feed-main a{font-weight:900;color:#126c82;font-size:16px;line-height:1.22;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.feed-main span{color:#40545d;font-size:14px;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.feed-source{color:#263946;font-weight:850;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.feed-more{color:#1f7d92;font-size:12px;font-weight:950;text-align:right;white-space:nowrap}
.feed-card[open] .feed-more{color:#667982}
.feed-detail{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;padding:14px 16px;background:rgba(248,252,252,.82)}
.feed-detail div{border:1px solid rgba(213,228,233,.78);border-radius:8px;background:rgba(255,255,255,.64);padding:10px;min-width:0}
.feed-detail b{display:block;color:#102f3a;font-size:12px;text-transform:uppercase;letter-spacing:.035em;margin-bottom:5px}
.feed-detail span{display:block;color:#536872;font-size:13px;line-height:1.35;overflow-wrap:anywhere}
.feed-detail-wide{grid-column:span 2}
.feed-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:4px}
.feed-limit-note{color:#667982;font-size:13px;line-height:1.4}
.feed-pages{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.feed-page-btn{display:inline-flex;align-items:center;justify-content:center;min-height:34px;padding:0 12px;border-radius:8px;border:1px solid rgba(202,221,228,.88);background:rgba(255,255,255,.78);color:#126c82;font-size:13px;font-weight:950}
.feed-page-btn:hover{text-decoration:none;background:#fff}
.feed-page-btn.disabled{opacity:.44;pointer-events:none;color:#6f8087}
.feed-page-current{color:#536872;font-size:13px;font-weight:850}
.source-orbit{overflow:hidden;position:relative;min-width:0;max-width:100%;background:linear-gradient(135deg,rgba(255,255,255,.82),rgba(234,247,250,.70))!important}
.source-orbit:before{content:"";position:absolute;right:-90px;top:-100px;width:240px;height:240px;border-radius:50%;background:radial-gradient(circle,rgba(45,198,214,.22),rgba(45,198,214,0) 70%);pointer-events:none}
.source-orbit-layout{display:grid;grid-template-columns:190px minmax(0,1fr);gap:16px;align-items:stretch;min-width:0}
.source-orbit-core{min-height:178px;border-radius:8px;background:linear-gradient(145deg,rgba(255,255,255,.72),rgba(231,246,248,.72));border:1px solid rgba(210,227,232,.86);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:14px;box-shadow:inset 0 1px 0 rgba(255,255,255,.82)}
.source-ring{--p:0;width:96px;height:96px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(#24c7d6 calc(var(--p)*1%),rgba(222,234,239,.85) 0);position:relative;box-shadow:0 14px 28px rgba(38,82,104,.10)}
.source-ring:after{content:"";position:absolute;inset:11px;border-radius:50%;background:rgba(255,255,255,.92);box-shadow:inset 0 1px 0 rgba(255,255,255,.9)}
.source-ring span{position:relative;z-index:1;width:54px;height:54px;border-radius:8px;background:#102f3a;color:#fff;display:grid;place-items:center;font-size:24px;font-weight:950}
.source-orbit-core b{font-size:18px;color:#102f3a;margin-top:10px;max-width:100%;overflow-wrap:anywhere}.source-orbit-core p{margin:4px 0 0;color:#667982;font-weight:850;font-size:12px;line-height:1.25;max-width:100%;overflow-wrap:anywhere}
.source-orbit-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(210px,100%),1fr));gap:10px;padding:2px;min-width:0;max-width:100%}
.source-orbit-card{min-width:0;max-width:100%;display:block;border:1px solid rgba(210,227,232,.86);border-radius:8px;background:rgba(255,255,255,.72);padding:0;box-shadow:0 12px 28px rgba(38,82,104,.06);overflow:hidden}.source-orbit-card summary{list-style:none;cursor:pointer;display:flex;gap:10px;align-items:flex-start;padding:11px}.source-orbit-card summary::-webkit-details-marker{display:none}.source-orbit-card[open]{background:rgba(255,255,255,.88);box-shadow:0 16px 34px rgba(38,82,104,.10)}.source-orbit-card[open] summary{border-bottom:1px solid rgba(210,227,232,.72)}
.source-orbit-icon{width:36px;height:36px;border-radius:8px;background:#eef8f9;color:#147487;display:grid;place-items:center;font-size:18px;font-weight:950;flex:0 0 auto}
.source-orbit-main{min-width:0;flex:1}.source-orbit-top{display:flex;justify-content:space-between;gap:8px;align-items:center;min-width:0}.source-orbit-top b{color:#102f3a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:14px}.source-orbit-top span{font-weight:950;color:#1f7d92;white-space:nowrap;flex:0 0 auto}
.source-orbit-track{height:7px;border-radius:999px;background:#e8f0f3;margin:7px 0;overflow:hidden}.source-orbit-track i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,#1f7d92,#24c7d6)}
.source-orbit-card p{margin:0;color:#5f737c;font-size:12px;line-height:1.3;min-height:31px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.source-orbit-card small{display:block;margin-top:5px;color:#102f3a;font-weight:850;font-size:12px;line-height:1.25}
.source-orbit-detail{padding:10px 12px 12px;background:rgba(248,252,252,.78)}.source-orbit-detail b{display:block;color:#102f3a;font-size:12px;text-transform:uppercase;letter-spacing:.035em;margin-bottom:7px}.source-orbit-detail ul{list-style:none;margin:0;padding:0;display:grid;gap:6px}.source-orbit-detail li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;color:#526a74;font-size:12px;line-height:1.25}.source-orbit-detail span,.source-orbit-detail a{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.source-orbit-detail a{color:#176b87;font-weight:850}.source-orbit-detail em{font-style:normal;color:#102f3a;font-weight:900}
.insight-board{background:linear-gradient(135deg,rgba(255,255,255,.84),rgba(242,248,251,.72))!important}
.insight-stream{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.signal-card{display:flex;gap:13px;align-items:flex-start;border:1px solid rgba(210,227,232,.88);border-radius:8px;background:rgba(255,255,255,.74);padding:14px;min-height:112px;box-shadow:0 14px 32px rgba(38,82,104,.07)}
.signal-icon{width:42px;height:42px;border-radius:8px;background:#eef8f9;color:#147487;display:grid;place-items:center;font-weight:950;font-size:20px;flex:0 0 auto}
.signal-card.hot .signal-icon{background:#fff4dc;color:#9b6900}.signal-card.calm .signal-icon{background:#e4f7ee;color:#157147}
.signal-card span{display:block;color:#74858d;font-size:12px;font-weight:950;text-transform:uppercase;letter-spacing:.035em}.signal-card b{display:block;color:#102f3a;font-size:20px;line-height:1.15;margin-top:5px;overflow-wrap:anywhere}.signal-card p{margin:8px 0 0;color:#536872;font-size:13px;line-height:1.35}
/* Liquid glass visual layer: premium translucency without sacrificing data readability. */
body.with-sidebar{background:linear-gradient(140deg,#dcecf7 0%,#eef6fa 32%,#f9fbfb 58%,#eef4fb 100%) fixed;color:#132a34}
body.with-sidebar:before{content:"";position:fixed;inset:0;pointer-events:none;background:linear-gradient(115deg,rgba(255,255,255,.62),rgba(255,255,255,.08) 28%,rgba(202,232,241,.28) 62%,rgba(255,255,255,.36));z-index:-1}
.with-sidebar .top{padding-top:34px}
.with-sidebar .top h1{font-size:32px;font-weight:950;color:#0f2f3a}
.with-sidebar .top p{color:#5b7078;font-weight:650}
.nav{background:linear-gradient(145deg,rgba(255,255,255,.72),rgba(240,248,251,.50));border:1px solid rgba(255,255,255,.78);box-shadow:0 24px 80px rgba(29,75,96,.18),inset 0 1px 0 rgba(255,255,255,.92),inset 0 -1px 0 rgba(118,157,174,.12)}
.nav:before{content:"";position:absolute;inset:1px;border-radius:7px;pointer-events:none;background:linear-gradient(145deg,rgba(255,255,255,.70),rgba(255,255,255,0) 34%,rgba(121,194,211,.10))}
.nav>*{position:relative}
.brand-mark,.nav a.active .nav-ico{background:linear-gradient(145deg,#0d3340,#173f4c);box-shadow:0 12px 26px rgba(16,50,62,.22),inset 0 1px 0 rgba(255,255,255,.18)}
.nav a{border-radius:8px;color:#203744;transition:background .16s ease,box-shadow .16s ease,transform .16s ease}
.nav a:hover{transform:translateY(-1px);background:rgba(255,255,255,.76);box-shadow:0 12px 28px rgba(47,98,119,.10),inset 0 0 0 1px rgba(255,255,255,.78)}
.nav a.active{background:rgba(255,255,255,.90);box-shadow:0 14px 34px rgba(47,98,119,.14),inset 0 0 0 1px rgba(255,255,255,.96)}
.with-sidebar .workspace-hero,.with-sidebar .metric,.with-sidebar .card,.with-sidebar .collect-panel,.with-sidebar .filter-bar,.with-sidebar .hero-main,.with-sidebar .hero-side,.with-sidebar .provider,.with-sidebar .project-card,.with-sidebar table{position:relative;overflow:hidden;background:linear-gradient(145deg,rgba(255,255,255,.74),rgba(245,251,252,.46))!important;border:1px solid rgba(255,255,255,.76);box-shadow:0 20px 60px rgba(31,78,99,.12),inset 0 1px 0 rgba(255,255,255,.88),inset 0 -1px 0 rgba(109,151,169,.10);backdrop-filter:blur(22px) saturate(1.18);-webkit-backdrop-filter:blur(22px) saturate(1.18)}
.with-sidebar .workspace-hero:before,.with-sidebar .metric:before,.with-sidebar .card:before,.with-sidebar .hero-main:before,.with-sidebar .hero-side:before,.with-sidebar .provider:before{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(128deg,rgba(255,255,255,.68),rgba(255,255,255,0) 38%,rgba(95,190,208,.08) 76%,rgba(255,255,255,.26));opacity:.9}
.with-sidebar .workspace-hero>*,.with-sidebar .metric>*,.with-sidebar .card>*,.with-sidebar .hero-main>*,.with-sidebar .hero-side>*,.with-sidebar .provider>*{position:relative}
.hero-main{background:linear-gradient(145deg,rgba(255,255,255,.82),rgba(235,248,250,.58))!important}
.hero-side{background:linear-gradient(145deg,rgba(255,255,255,.78),rgba(241,247,252,.54))!important}
.metric{min-height:116px;transition:transform .16s ease,box-shadow .16s ease}.metric:hover{transform:translateY(-2px);box-shadow:0 24px 70px rgba(31,78,99,.15),inset 0 1px 0 rgba(255,255,255,.9)}
.metric .value{color:#101a2c}.metric .caption,.k{color:#667984}
.btn,.feed-page-btn{border-radius:999px;background:linear-gradient(145deg,#1b8298,#115b72);box-shadow:0 12px 28px rgba(26,112,134,.18),inset 0 1px 0 rgba(255,255,255,.28)}
.btn.light,.btn.secondary{background:rgba(255,255,255,.62);color:#123441;border:1px solid rgba(207,223,229,.86);box-shadow:0 10px 24px rgba(47,98,119,.09),inset 0 1px 0 rgba(255,255,255,.82)}
.input,.select,.textarea{border-radius:999px;background:rgba(255,255,255,.70);border-color:rgba(198,218,226,.86);box-shadow:inset 0 1px 0 rgba(255,255,255,.88),0 8px 22px rgba(31,78,99,.06)}
.textarea{border-radius:8px}
.filter-bar{padding:14px 16px;border-radius:8px}
.trend-card,.tone-card,.source-orbit,.insight-board{background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(238,249,252,.52))!important}
.trend-panel-bg{fill:rgba(255,255,255,.64)}
.trend-chart{border:1px solid rgba(255,255,255,.76);box-shadow:inset 0 1px 0 rgba(255,255,255,.86);background:linear-gradient(145deg,rgba(255,255,255,.55),rgba(231,244,250,.32));border-radius:8px}
.trend-line{stroke:#26a8d4!important;filter:drop-shadow(0 7px 12px rgba(38,168,212,.24))}
.trend-dot{stroke:#26a8d4!important}.trend-dot-muted{stroke:#99d7ea;fill:#f3fbfd}
.period-summary span,.chip,.metric-state,.pill,.status{box-shadow:inset 0 1px 0 rgba(255,255,255,.70)}
.tone-funnel-viz,.source-orbit-core,.source-orbit-card,.signal-card,.feed-card{background:linear-gradient(145deg,rgba(255,255,255,.68),rgba(246,251,252,.46));border-color:rgba(255,255,255,.74);box-shadow:0 14px 38px rgba(31,78,99,.10),inset 0 1px 0 rgba(255,255,255,.88)}
.source-orbit-icon,.signal-icon,.nav-ico{background:rgba(238,249,251,.78);box-shadow:inset 0 1px 0 rgba(255,255,255,.88),inset 0 -1px 0 rgba(95,139,157,.10)}
th{background:linear-gradient(145deg,#123441,#1e5363)}
td{background:rgba(255,255,255,.54)}
.feed-card summary{background:rgba(255,255,255,.44)}
.feed-card[open] summary,.feed-detail{background:rgba(247,252,253,.68)}
.help-dot{background:rgba(255,255,255,.76);box-shadow:0 8px 20px rgba(31,78,99,.09),inset 0 1px 0 rgba(255,255,255,.9)}
/* Reference repaint: warm Vision-style milk glass, pastel cyan/blue/lilac accents. */
:root{--cream:#f3e9df;--cream-2:#fbf7f2;--milk:rgba(255,255,255,.70);--glass:rgba(255,255,255,.58);--ink:#12131a;--soft:#726a67;--aqua:#65e2de;--blue:#4b98f7;--lilac:#b891f5;--peach:#f7bca9;--leaf:#6ca878;--line:rgba(255,255,255,.76);--shade:rgba(87,61,43,.13)}
body.with-sidebar{background:linear-gradient(135deg,#e9ddd4 0%,#f7efe8 30%,#fbf8f5 58%,#eaf7f6 100%) fixed;color:var(--ink)}
body.with-sidebar:before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;background:linear-gradient(118deg,rgba(255,255,255,.60),rgba(255,255,255,0) 34%,rgba(101,226,222,.20) 64%,rgba(40,69,122,.10) 100%)}
body.with-sidebar:after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:linear-gradient(180deg,rgba(255,255,255,.18),rgba(255,255,255,0) 45%),radial-gradient(ellipse at 82% 6%,rgba(255,255,255,.72),rgba(255,255,255,0) 34%),radial-gradient(ellipse at 8% 28%,rgba(108,168,120,.20),rgba(108,168,120,0) 28%)}
.with-sidebar .top h1{color:#101116;font-size:34px;letter-spacing:0}
.with-sidebar .top p{color:#706760;font-weight:750}
.nav{background:linear-gradient(145deg,rgba(255,255,255,.66),rgba(255,250,245,.38));border-color:rgba(255,255,255,.88);box-shadow:0 30px 90px rgba(94,64,42,.16),inset 0 1px 0 rgba(255,255,255,.95),inset 0 -1px 0 rgba(150,116,91,.10)}
.brand-mark,.nav a.active .nav-ico{background:linear-gradient(145deg,#111827,#20313a);color:#fff}
.nav-brand b,.nav-user b,.nav a{color:#17171d}.nav-brand small,.nav-user small{color:#8a7f78}
.nav a.active{background:rgba(255,255,255,.82)}
.nav-ico{background:linear-gradient(145deg,rgba(255,255,255,.80),rgba(237,248,248,.54));color:#111827}
.with-sidebar .workspace-hero,.with-sidebar .metric,.with-sidebar .card,.with-sidebar .collect-panel,.with-sidebar .filter-bar,.with-sidebar .hero-main,.with-sidebar .hero-side,.with-sidebar .provider,.with-sidebar .project-card,.with-sidebar table{background:linear-gradient(145deg,rgba(255,255,255,.72),rgba(255,248,241,.44))!important;border:1px solid rgba(255,255,255,.84);box-shadow:0 26px 74px var(--shade),inset 0 1px 0 rgba(255,255,255,.96),inset 0 -1px 0 rgba(146,111,87,.12);backdrop-filter:blur(28px) saturate(1.24);-webkit-backdrop-filter:blur(28px) saturate(1.24)}
.with-sidebar .workspace-hero:before,.with-sidebar .metric:before,.with-sidebar .card:before,.with-sidebar .hero-main:before,.with-sidebar .hero-side:before,.with-sidebar .provider:before{background:linear-gradient(132deg,rgba(255,255,255,.76),rgba(255,255,255,0) 34%,rgba(101,226,222,.12) 66%,rgba(40,69,122,.10));opacity:1}
.hero-main{background:linear-gradient(145deg,rgba(255,255,255,.82),rgba(249,230,218,.45) 62%,rgba(235,252,251,.42))!important}
.hero-side{background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(236,250,250,.48))!important}
.eyebrow{color:#a27048}.hero-main h2,.pagehead h2,.premium-section-title h2,.chart-title h3,.provider h3,.card h3{color:#111217}
.hero-main p,.provider small,.pagehead p,.premium-section-title p,.hint,.muted{color:#736b65}
.metric{background:linear-gradient(145deg,rgba(255,255,255,.74),rgba(255,246,239,.50))!important}
.metric:nth-child(2n){background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(230,252,251,.46))!important}
.metric:nth-child(3n){background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(238,229,255,.42))!important}
.metric .value,.v,.row b{color:#111217}.metric .caption,.k{color:#766d67}
.btn{background:linear-gradient(145deg,#58bbff,#3c80ed);color:#fff;border:1px solid rgba(255,255,255,.56);box-shadow:0 16px 34px rgba(62,132,235,.22),inset 0 1px 0 rgba(255,255,255,.45)}
.btn.secondary{background:linear-gradient(145deg,#191b24,#323747);color:#fff;border-color:rgba(255,255,255,.32)}
.btn.light,.feed-page-btn{background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(247,241,236,.56));color:#15161c;border-color:rgba(255,255,255,.88);box-shadow:0 14px 30px rgba(99,69,48,.10),inset 0 1px 0 rgba(255,255,255,.92)}
.input,.select,.textarea{background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(255,250,246,.58));border-color:rgba(255,255,255,.86);color:#15161c;box-shadow:0 12px 28px rgba(99,69,48,.08),inset 0 1px 0 rgba(255,255,255,.96)}
.input:focus,.select:focus,.textarea:focus{outline:3px solid rgba(88,187,255,.18);border-color:rgba(88,187,255,.58)}
.chip{background:rgba(255,255,255,.54);border-color:rgba(255,255,255,.74);color:#5f554f}
.positive,.metric-state.good,.on{background:rgba(219,246,229,.74);color:#1d6b3f}
.negative,.metric-state.bad,.off{background:rgba(255,226,220,.74);color:#9c3529}
.neutral{background:rgba(238,238,236,.72);color:#6c6660}
.metric-state.warn{background:rgba(255,239,207,.76);color:#93631a}
.trend-card{background:linear-gradient(145deg,rgba(255,255,255,.74),rgba(246,233,250,.46),rgba(228,250,250,.44))!important}
.trend-chart{background:linear-gradient(145deg,rgba(255,255,255,.58),rgba(255,243,234,.32),rgba(227,249,249,.32))}
.trend-line{stroke:#55a6ff!important}.trend-dot{stroke:#55a6ff!important}
.tone-card{background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(232,251,250,.42))!important}
.tone-funnel-shape{fill:url(#toneFunnelGradient);filter:drop-shadow(0 18px 28px rgba(76,141,235,.16))}
.source-orbit{background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(255,242,232,.44),rgba(228,250,249,.42))!important}
.source-ring{background:conic-gradient(var(--aqua) calc(var(--p)*1%),rgba(255,255,255,.72) 0)}
.source-ring span{background:linear-gradient(145deg,#111827,#26313a)}
.source-orbit-icon,.signal-icon{background:linear-gradient(145deg,rgba(232,252,251,.82),rgba(255,255,255,.58));color:#188795}
.source-orbit-track i{background:linear-gradient(90deg,#4b98f7,#65e2de)}
.signal-card.hot .signal-icon{background:linear-gradient(145deg,rgba(255,239,207,.9),rgba(255,255,255,.56));color:#9b6900}.signal-card.calm .signal-icon{background:linear-gradient(145deg,rgba(219,246,229,.9),rgba(255,255,255,.56));color:#157147}
th{background:linear-gradient(145deg,#141720,#273345);color:#fff}
td{background:rgba(255,255,255,.50);color:#2d333b}
.feed-card,.source-orbit-card,.signal-card,.tone-funnel-viz,.source-orbit-core{background:linear-gradient(145deg,rgba(255,255,255,.68),rgba(255,248,242,.42));border-color:rgba(255,255,255,.78)}
.feed-main a,a{color:#157b91}
.feed-source{color:#1e2731}.feed-detail div{background:rgba(255,255,255,.50);border-color:rgba(255,255,255,.78)}
.coverage-note{background:rgba(255,255,255,.46);border-color:rgba(255,255,255,.76);border-left-color:var(--aqua);color:#635b55}
.barline a:first-child,.source-orbit-detail a{color:#157b91}
/* Dark Liquid Glass pass: closer to the neon reference, with depth and readable analytics. */
:root{--lg-bg:#060b15;--lg-panel:rgba(18,28,48,.62);--lg-panel-2:rgba(26,38,66,.46);--lg-stroke:rgba(202,231,255,.24);--lg-cyan:#35f5f0;--lg-blue:#5d8cff;--lg-violet:#d45cff;--lg-pink:#ff78c7;--lg-peach:#ffb978;--lg-text:#f6fbff;--lg-muted:#9fb0c5}
body.with-sidebar{background:
radial-gradient(circle at 18% 7%,rgba(53,245,240,.18),transparent 30%),
radial-gradient(circle at 83% 13%,rgba(40,69,122,.18),transparent 28%),
radial-gradient(circle at 58% 86%,rgba(93,140,255,.16),transparent 34%),
linear-gradient(135deg,#050812 0%,#0b1322 42%,#11172a 100%) fixed!important;color:var(--lg-text)}
body.with-sidebar:before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;background:
linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px),
linear-gradient(180deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:72px 72px;mask-image:linear-gradient(180deg,rgba(0,0,0,.58),transparent 78%)}
body.with-sidebar:after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:
linear-gradient(125deg,rgba(255,255,255,.08),transparent 34%,rgba(53,245,240,.08) 62%,rgba(40,69,122,.07)),
radial-gradient(ellipse at 50% 0%,rgba(255,255,255,.12),transparent 34%);mix-blend-mode:screen}
body.with-sidebar .top{background:transparent!important;padding-top:34px}
body.with-sidebar .top h1{color:var(--lg-text);text-shadow:0 0 34px rgba(53,245,240,.18)}
body.with-sidebar .top p,.pagehead p,.premium-section-title p,.hint,.muted,.provider small,.hero-main p,.chart-title span{color:var(--lg-muted)!important}
.nav{background:linear-gradient(145deg,rgba(20,32,55,.72),rgba(8,14,28,.56))!important;border:1px solid rgba(205,230,255,.18)!important;box-shadow:0 30px 90px rgba(0,0,0,.38),0 0 38px rgba(53,245,240,.08),inset 0 1px 0 rgba(255,255,255,.22),inset 0 -1px 0 rgba(53,245,240,.10)!important;backdrop-filter:blur(26px) saturate(1.45)!important;-webkit-backdrop-filter:blur(26px) saturate(1.45)!important}
.nav:before{background:linear-gradient(135deg,rgba(255,255,255,.16),transparent 34%,rgba(53,245,240,.08),rgba(40,69,122,.08))!important}
.brand-mark{background:linear-gradient(145deg,#102032,#06101c)!important;border:1px solid rgba(53,245,240,.30);box-shadow:0 0 28px rgba(53,245,240,.18),inset 0 1px 0 rgba(255,255,255,.20)!important;color:#fff!important}
.nav-brand b,.nav-user b,.nav a{color:var(--lg-text)!important}.nav-brand small,.nav-user small{color:var(--lg-muted)!important}
.nav a{background:transparent!important;border:1px solid transparent!important}
.nav a:hover{background:rgba(255,255,255,.07)!important;border-color:rgba(53,245,240,.18)!important;box-shadow:0 0 24px rgba(53,245,240,.12),inset 0 1px 0 rgba(255,255,255,.14)!important}
.nav a.active{background:linear-gradient(145deg,rgba(79,105,255,.24),rgba(53,245,240,.10))!important;border-color:rgba(53,245,240,.34)!important;box-shadow:0 0 30px rgba(53,245,240,.16),inset 0 1px 0 rgba(255,255,255,.20)!important}
.nav-ico,.source-orbit-icon,.signal-icon{background:linear-gradient(145deg,rgba(53,245,240,.13),rgba(255,255,255,.06))!important;border:1px solid rgba(205,230,255,.16);color:#dffcff!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.18),0 0 20px rgba(53,245,240,.08)!important}
.with-sidebar .workspace-hero,.with-sidebar .metric,.with-sidebar .card,.with-sidebar .collect-panel,.with-sidebar .filter-bar,.with-sidebar .hero-main,.with-sidebar .hero-side,.with-sidebar .provider,.with-sidebar .project-card,.with-sidebar table,.feed-card,.source-orbit-card,.signal-card,.tone-funnel-viz,.source-orbit-core,.ai-chat-panel,.ai-answer,.agent-card,.insight,.metric-pill,.legend-row{background:linear-gradient(145deg,rgba(26,38,66,.66),rgba(10,16,31,.42))!important;border:1px solid var(--lg-stroke)!important;box-shadow:0 24px 70px rgba(0,0,0,.34),0 0 42px rgba(53,245,240,.075),inset 0 1px 0 rgba(255,255,255,.18),inset 0 -1px 0 rgba(40,69,122,.10)!important;backdrop-filter:blur(26px) saturate(1.38)!important;-webkit-backdrop-filter:blur(26px) saturate(1.38)!important}
.with-sidebar .workspace-hero:before,.with-sidebar .metric:before,.with-sidebar .card:before,.with-sidebar .hero-main:before,.with-sidebar .hero-side:before,.with-sidebar .provider:before{background:linear-gradient(135deg,rgba(255,255,255,.15),transparent 36%,rgba(53,245,240,.08) 68%,rgba(40,69,122,.10))!important}
.with-sidebar .metric:after{height:2px!important;background:linear-gradient(90deg,var(--lg-cyan),var(--lg-blue),var(--accent),var(--accent))!important;opacity:.95!important;box-shadow:0 0 18px rgba(53,245,240,.42)}
.metric:nth-child(2n),.metric:nth-child(3n),.hero-main,.hero-side,.trend-card,.tone-card,.source-orbit,.insight-board{background:linear-gradient(145deg,rgba(30,45,78,.70),rgba(11,17,33,.44))!important}
.metric:hover,.project-card:hover,.provider:hover,.feed-card:hover{transform:translateY(-2px);box-shadow:0 30px 86px rgba(0,0,0,.42),0 0 44px rgba(53,245,240,.13),inset 0 1px 0 rgba(255,255,255,.20)!important}
.with-sidebar .top h1,.hero-main h2,.pagehead h2,.premium-section-title h2,.chart-title h3,.provider h3,.card h3,.section-title,.project-switcher h2,.source-picker-head b,.agent-card h4,.ai-chat-panel h4,.row b,.metric .value,.v,.metric-number,.source-orbit-top b,.signal-card b,.legend-row b,.insight b,.metric-pill b{color:var(--lg-text)!important}
.metric .caption,.k,.snippet,.agent-card p,.agent-list li,.source-orbit-card p,.source-orbit-core p,.signal-card p,.metric-detail p,.metric-detail ul,.metric-mini,.row span{color:var(--lg-muted)!important}
a,.feed-main a,.barline a:first-child,.source-orbit-detail a{color:#77f7ff!important;text-shadow:0 0 18px rgba(53,245,240,.18)}
.btn,.feed-page-btn{background:linear-gradient(135deg,var(--lg-cyan),var(--lg-blue) 58%,var(--accent))!important;color:#06101c!important;border:1px solid rgba(255,255,255,.38)!important;border-radius:999px;box-shadow:0 0 26px rgba(53,245,240,.32),0 12px 34px rgba(93,140,255,.22),inset 0 1px 0 rgba(255,255,255,.54)!important;text-shadow:none}
.btn.secondary{background:linear-gradient(135deg,rgba(24,34,59,.88),rgba(40,69,122,.70))!important;color:#fff!important;border-color:rgba(40,69,122,.34)!important;box-shadow:0 0 28px rgba(40,69,122,.18),inset 0 1px 0 rgba(255,255,255,.18)!important}
.btn.light{background:linear-gradient(145deg,rgba(255,255,255,.12),rgba(255,255,255,.05))!important;color:var(--lg-text)!important;border-color:rgba(205,230,255,.20)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.16),0 12px 28px rgba(0,0,0,.18)!important}
.input,.select,.textarea{background:linear-gradient(145deg,rgba(255,255,255,.12),rgba(255,255,255,.06))!important;border:1px solid rgba(205,230,255,.22)!important;color:var(--lg-text)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.18),0 12px 30px rgba(0,0,0,.20)!important}
.input::placeholder,.textarea::placeholder{color:#7f91aa}.input:focus,.select:focus,.textarea:focus{outline:3px solid rgba(53,245,240,.18)!important;border-color:rgba(53,245,240,.46)!important;box-shadow:0 0 28px rgba(53,245,240,.13),inset 0 1px 0 rgba(255,255,255,.22)!important}
.chip,.pill,.status,.metric-state,.agent-tag,.period-summary span{background:rgba(255,255,255,.10)!important;border:1px solid rgba(205,230,255,.16)!important;color:#dcecff!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.16)!important}
.positive,.metric-state.good,.on{background:rgba(74,255,164,.15)!important;color:#7dffc0!important;border-color:rgba(74,255,164,.24)!important}.negative,.metric-state.bad,.off{background:rgba(255,92,142,.16)!important;color:#ff9bbc!important;border-color:rgba(255,92,142,.24)!important}.neutral{background:rgba(255,255,255,.11)!important;color:#d7e3f1!important}.metric-state.warn{background:rgba(255,185,120,.16)!important;color:#ffd2a6!important;border-color:rgba(255,185,120,.24)!important}
th{background:linear-gradient(145deg,rgba(7,14,28,.96),rgba(22,33,58,.92))!important;color:#f6fbff!important;border-bottom:1px solid rgba(53,245,240,.20)}
td{background:rgba(11,18,34,.42)!important;color:#dce7f4!important;border-top:1px solid rgba(205,230,255,.10)!important}
table{border-collapse:separate;border-spacing:0;overflow:hidden}
.trend-chart{background:linear-gradient(145deg,rgba(15,25,48,.72),rgba(5,10,20,.42))!important;border:1px solid rgba(205,230,255,.18)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.14),0 0 36px rgba(53,245,240,.08)!important}
.trend-chart svg{background:transparent!important}.trend-axis{stroke:rgba(205,230,255,.13)!important}.trend-line{stroke:var(--lg-cyan)!important;filter:drop-shadow(0 0 10px rgba(53,245,240,.58)) drop-shadow(0 8px 16px rgba(93,140,255,.28))!important}.trend-dot{fill:#07101c!important;stroke:var(--lg-cyan)!important;filter:drop-shadow(0 0 8px rgba(53,245,240,.58))}
.spark{border-color:rgba(205,230,255,.14)!important}.spark-col,.fill,.source-orbit-track i{background:linear-gradient(180deg,var(--lg-cyan),var(--lg-blue),var(--accent))!important;box-shadow:0 0 16px rgba(53,245,240,.18)}
.track,.source-orbit-track,.tone-stack{background:rgba(255,255,255,.10)!important}
.source-ring{background:conic-gradient(var(--lg-cyan),var(--lg-blue),var(--accent),var(--accent) calc(var(--p)*1%),rgba(255,255,255,.10) 0)!important;box-shadow:0 0 44px rgba(53,245,240,.15)}.source-ring span{background:linear-gradient(145deg,#081522,#16213a)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.18),0 0 26px rgba(53,245,240,.10)!important}
.tone-funnel-shape{filter:drop-shadow(0 0 22px rgba(53,245,240,.22)) drop-shadow(0 18px 28px rgba(0,0,0,.25))!important}
.feed-card summary,.feed-card[open] summary,.feed-detail,.metric-detail,.source-orbit-detail{background:rgba(7,14,28,.30)!important;border-color:rgba(205,230,255,.12)!important}.feed-detail div{background:rgba(255,255,255,.055)!important;border-color:rgba(205,230,255,.13)!important}.feed-source{color:#f6fbff!important}
.coverage-note{background:rgba(53,245,240,.07)!important;border-color:rgba(53,245,240,.18)!important;border-left-color:var(--lg-cyan)!important;color:#d9e8f6!important}
.sidebar-toggle,.help-dot{background:rgba(15,25,48,.74)!important;color:#f6fbff!important;border-color:rgba(205,230,255,.20)!important;box-shadow:0 0 24px rgba(53,245,240,.10),inset 0 1px 0 rgba(255,255,255,.16)!important}
.login-shell{background:radial-gradient(circle at 22% 12%,rgba(53,245,240,.18),transparent 30%),radial-gradient(circle at 84% 20%,rgba(40,69,122,.18),transparent 30%),linear-gradient(135deg,#050812,#10172a)!important}.login-card{background:linear-gradient(145deg,rgba(26,38,66,.74),rgba(10,16,31,.55))!important;border-color:rgba(205,230,255,.22)!important;color:var(--lg-text);box-shadow:0 30px 90px rgba(0,0,0,.42),0 0 42px rgba(53,245,240,.10),inset 0 1px 0 rgba(255,255,255,.18)!important;backdrop-filter:blur(26px) saturate(1.35)}.login-card h1{color:var(--lg-text)!important}.login-card p{color:var(--lg-muted)!important}
/* Light Liquid Glass correction: bright Vision-style glass with visible depth. */
:root{--ll-bg:#edf7ff;--ll-milk:rgba(255,255,255,.62);--ll-card:rgba(255,255,255,.70);--ll-ink:#111827;--ll-text:#243244;--ll-muted:#697789;--ll-cyan:#35e7ec;--ll-blue:#5b8fff;--ll-violet:#c56cff;--ll-pink:#ff8fcf;--ll-peach:#ffc9a8;--ll-line:rgba(255,255,255,.82);--ll-stroke:rgba(160,203,224,.42)}
body.with-sidebar{background:
radial-gradient(circle at 18% 8%,rgba(53,231,236,.30),transparent 31%),
radial-gradient(circle at 88% 12%,rgba(40,69,122,.24),transparent 29%),
radial-gradient(circle at 65% 88%,rgba(255,201,168,.28),transparent 34%),
linear-gradient(135deg,#f7fbff 0%,#e7f5ff 38%,#f9f4ff 67%,#fff7ef 100%) fixed!important;color:var(--ll-text)}
body.with-sidebar:before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;background:
linear-gradient(90deg,rgba(55,92,124,.045) 1px,transparent 1px),
linear-gradient(180deg,rgba(55,92,124,.04) 1px,transparent 1px);background-size:72px 72px;mask-image:linear-gradient(180deg,rgba(0,0,0,.52),transparent 82%)}
body.with-sidebar:after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:
linear-gradient(122deg,rgba(255,255,255,.72),rgba(255,255,255,.14) 32%,rgba(53,231,236,.13) 62%,rgba(40,69,122,.12)),
radial-gradient(ellipse at 50% -10%,rgba(255,255,255,.88),transparent 42%);mix-blend-mode:normal}
body.with-sidebar .top{background:transparent!important;padding-top:34px}
body.with-sidebar .top h1{color:var(--ll-ink)!important;text-shadow:0 12px 38px rgba(63,126,170,.16)}
body.with-sidebar .top p,.pagehead p,.premium-section-title p,.hint,.muted,.provider small,.hero-main p,.chart-title span{color:var(--ll-muted)!important}
.nav{background:linear-gradient(145deg,rgba(255,255,255,.68),rgba(241,249,255,.48))!important;border:1px solid rgba(255,255,255,.92)!important;box-shadow:0 30px 90px rgba(69,121,157,.16),0 0 46px rgba(53,231,236,.13),inset 0 1px 0 rgba(255,255,255,.98),inset 0 -1px 0 rgba(86,139,175,.12)!important;backdrop-filter:blur(28px) saturate(1.35)!important;-webkit-backdrop-filter:blur(28px) saturate(1.35)!important}
.nav:before{background:linear-gradient(135deg,rgba(255,255,255,.82),transparent 36%,rgba(53,231,236,.11),rgba(40,69,122,.10))!important}
.brand-mark{background:linear-gradient(145deg,#102132,#22374b)!important;border:1px solid rgba(255,255,255,.52);box-shadow:0 18px 34px rgba(50,103,140,.20),inset 0 1px 0 rgba(255,255,255,.24)!important;color:#fff!important}
.nav-brand b,.nav-user b,.nav a{color:var(--ll-ink)!important}.nav-brand small,.nav-user small{color:#7b8796!important}
.nav a{background:rgba(255,255,255,.30)!important;border:1px solid rgba(255,255,255,.12)!important}
.nav a:hover{background:rgba(255,255,255,.70)!important;border-color:rgba(83,163,204,.26)!important;box-shadow:0 16px 34px rgba(63,126,170,.12),inset 0 1px 0 rgba(255,255,255,.86)!important}
.nav a.active{background:linear-gradient(145deg,rgba(255,255,255,.86),rgba(236,251,255,.58))!important;border-color:rgba(53,231,236,.38)!important;box-shadow:0 18px 42px rgba(63,126,170,.15),0 0 22px rgba(53,231,236,.18),inset 0 1px 0 rgba(255,255,255,.96)!important}
.nav-ico,.source-orbit-icon,.signal-icon{background:linear-gradient(145deg,rgba(237,253,255,.86),rgba(255,255,255,.58))!important;border:1px solid rgba(255,255,255,.82);color:#147b91!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.96),0 12px 26px rgba(63,126,170,.10)!important}
.with-sidebar .workspace-hero,.with-sidebar .metric,.with-sidebar .card,.with-sidebar .collect-panel,.with-sidebar .filter-bar,.with-sidebar .hero-main,.with-sidebar .hero-side,.with-sidebar .provider,.with-sidebar .project-card,.with-sidebar table,.feed-card,.source-orbit-card,.signal-card,.tone-funnel-viz,.source-orbit-core,.ai-chat-panel,.ai-answer,.agent-card,.insight,.metric-pill,.legend-row{background:linear-gradient(145deg,rgba(255,255,255,.72),rgba(242,250,255,.48))!important;border:1px solid rgba(255,255,255,.88)!important;box-shadow:0 26px 78px rgba(69,121,157,.14),0 0 42px rgba(53,231,236,.10),inset 0 1px 0 rgba(255,255,255,.98),inset 0 -1px 0 rgba(95,144,178,.10)!important;backdrop-filter:blur(28px) saturate(1.22)!important;-webkit-backdrop-filter:blur(28px) saturate(1.22)!important}
.with-sidebar .workspace-hero:before,.with-sidebar .metric:before,.with-sidebar .card:before,.with-sidebar .hero-main:before,.with-sidebar .hero-side:before,.with-sidebar .provider:before{background:linear-gradient(132deg,rgba(255,255,255,.88),rgba(255,255,255,0) 36%,rgba(53,231,236,.13) 68%,rgba(40,69,122,.10))!important}
.with-sidebar .metric:after{height:2px!important;background:linear-gradient(90deg,var(--ll-cyan),var(--ll-blue),var(--accent),var(--accent))!important;opacity:.82!important;box-shadow:0 0 18px rgba(53,231,236,.35)}
.metric:nth-child(2n),.metric:nth-child(3n),.hero-main,.hero-side,.trend-card,.tone-card,.source-orbit,.insight-board{background:linear-gradient(145deg,rgba(255,255,255,.76),rgba(238,250,255,.52))!important}
.metric:hover,.project-card:hover,.provider:hover,.feed-card:hover{transform:translateY(-2px);box-shadow:0 32px 86px rgba(69,121,157,.18),0 0 44px rgba(53,231,236,.16),inset 0 1px 0 rgba(255,255,255,1)!important}
.with-sidebar .top h1,.hero-main h2,.pagehead h2,.premium-section-title h2,.chart-title h3,.provider h3,.card h3,.section-title,.project-switcher h2,.source-picker-head b,.agent-card h4,.ai-chat-panel h4,.row b,.metric .value,.v,.metric-number,.source-orbit-top b,.signal-card b,.legend-row b,.insight b,.metric-pill b{color:var(--ll-ink)!important}
.metric .caption,.k,.snippet,.agent-card p,.agent-list li,.source-orbit-card p,.source-orbit-core p,.signal-card p,.metric-detail p,.metric-detail ul,.metric-mini,.row span{color:var(--ll-muted)!important}
a,.feed-main a,.barline a:first-child,.source-orbit-detail a{color:#157a96!important;text-shadow:none}
.btn,.feed-page-btn{background:linear-gradient(135deg,var(--ll-cyan),var(--ll-blue) 58%,var(--accent))!important;color:#06101c!important;border:1px solid rgba(255,255,255,.78)!important;border-radius:999px;box-shadow:0 18px 38px rgba(82,144,230,.23),0 0 26px rgba(53,231,236,.20),inset 0 1px 0 rgba(255,255,255,.70)!important;text-shadow:none}
.btn.secondary{background:linear-gradient(145deg,#142436,#263a53)!important;color:#fff!important;border-color:rgba(255,255,255,.34)!important;box-shadow:0 18px 38px rgba(35,66,94,.22),inset 0 1px 0 rgba(255,255,255,.20)!important}
.btn.light{background:linear-gradient(145deg,rgba(255,255,255,.80),rgba(242,249,255,.58))!important;color:var(--ll-ink)!important;border-color:rgba(255,255,255,.88)!important;box-shadow:0 14px 30px rgba(69,121,157,.11),inset 0 1px 0 rgba(255,255,255,.96)!important}
.input,.select,.textarea{background:linear-gradient(145deg,rgba(255,255,255,.82),rgba(242,250,255,.60))!important;border:1px solid rgba(255,255,255,.90)!important;color:var(--ll-ink)!important;box-shadow:0 12px 28px rgba(69,121,157,.09),inset 0 1px 0 rgba(255,255,255,.98)!important}
.input::placeholder,.textarea::placeholder{color:#8b98a8}.input:focus,.select:focus,.textarea:focus{outline:3px solid rgba(53,231,236,.18)!important;border-color:rgba(53,231,236,.55)!important;box-shadow:0 0 28px rgba(53,231,236,.18),inset 0 1px 0 rgba(255,255,255,.98)!important}
.chip,.pill,.status,.metric-state,.agent-tag,.period-summary span{background:rgba(255,255,255,.56)!important;border:1px solid rgba(255,255,255,.82)!important;color:#435267!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.86)!important}
.positive,.metric-state.good,.on{background:rgba(216,249,231,.78)!important;color:#17613d!important;border-color:rgba(132,222,174,.40)!important}.negative,.metric-state.bad,.off{background:rgba(255,226,236,.78)!important;color:#a22d59!important;border-color:rgba(255,143,191,.36)!important}.neutral{background:rgba(235,240,246,.78)!important;color:#5f6b79!important}.metric-state.warn{background:rgba(255,239,211,.80)!important;color:#91601f!important;border-color:rgba(255,201,138,.42)!important}
th{background:linear-gradient(145deg,rgba(20,36,54,.95),rgba(38,58,83,.92))!important;color:#f7fbff!important;border-bottom:1px solid rgba(255,255,255,.22)}
td{background:rgba(255,255,255,.48)!important;color:#314052!important;border-top:1px solid rgba(160,203,224,.22)!important}
table{border-collapse:separate;border-spacing:0;overflow:hidden}
.trend-chart{background:linear-gradient(145deg,rgba(255,255,255,.54),rgba(235,248,255,.34))!important;border:1px solid rgba(255,255,255,.86)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.92),0 0 36px rgba(53,231,236,.12)!important}
.trend-chart svg{background:transparent!important}.trend-axis{stroke:rgba(80,116,145,.16)!important}.trend-line{stroke:#35bde8!important;filter:drop-shadow(0 0 8px rgba(53,231,236,.36)) drop-shadow(0 8px 16px rgba(82,144,230,.18))!important}.trend-dot{fill:#f8fdff!important;stroke:#35bde8!important;filter:drop-shadow(0 0 8px rgba(53,231,236,.36))}
.spark{border-color:rgba(80,116,145,.18)!important}.spark-col,.fill,.source-orbit-track i{background:linear-gradient(180deg,var(--ll-cyan),var(--ll-blue),var(--accent))!important;box-shadow:0 0 16px rgba(53,231,236,.16)}
.track,.source-orbit-track,.tone-stack{background:rgba(77,110,138,.12)!important}
.source-ring{background:conic-gradient(var(--ll-cyan),var(--ll-blue),var(--accent),var(--accent) calc(var(--p)*1%),rgba(77,110,138,.12) 0)!important;box-shadow:0 0 44px rgba(53,231,236,.17)}.source-ring span{background:linear-gradient(145deg,#12243a,#263b54)!important;color:#fff!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.20),0 0 26px rgba(53,231,236,.12)!important}
.tone-funnel-shape{filter:drop-shadow(0 0 22px rgba(53,231,236,.18)) drop-shadow(0 18px 28px rgba(69,121,157,.16))!important}
.feed-card summary,.feed-card[open] summary,.feed-detail,.metric-detail,.source-orbit-detail{background:rgba(255,255,255,.34)!important;border-color:rgba(255,255,255,.52)!important}.feed-detail div{background:rgba(255,255,255,.44)!important;border-color:rgba(255,255,255,.72)!important}.feed-source{color:var(--ll-ink)!important}
.coverage-note{background:rgba(255,255,255,.46)!important;border-color:rgba(255,255,255,.76)!important;border-left-color:var(--ll-cyan)!important;color:#4d5b6c!important}
.sidebar-toggle,.help-dot{background:rgba(255,255,255,.76)!important;color:var(--ll-ink)!important;border-color:rgba(255,255,255,.86)!important;box-shadow:0 14px 30px rgba(69,121,157,.12),inset 0 1px 0 rgba(255,255,255,.96)!important}
.login-shell{background:radial-gradient(circle at 22% 12%,rgba(53,231,236,.28),transparent 31%),radial-gradient(circle at 84% 20%,rgba(40,69,122,.22),transparent 30%),linear-gradient(135deg,#f7fbff,#eaf7ff 55%,#fff8f1)!important}.login-card{background:linear-gradient(145deg,rgba(255,255,255,.74),rgba(242,250,255,.50))!important;border-color:rgba(255,255,255,.88)!important;color:var(--ll-text);box-shadow:0 30px 90px rgba(69,121,157,.16),0 0 42px rgba(53,231,236,.12),inset 0 1px 0 rgba(255,255,255,.98)!important;backdrop-filter:blur(28px) saturate(1.25)}.login-card h1{color:var(--ll-ink)!important}.login-card p{color:var(--ll-muted)!important}
/* Product layout correction: clearer hierarchy, calmer glass palette, less explanatory noise. */
body.with-sidebar{background:
radial-gradient(circle at 18% 7%,rgba(58,217,224,.18),transparent 30%),
radial-gradient(circle at 88% 11%,rgba(172,133,245,.14),transparent 31%),
linear-gradient(135deg,#f8fcff 0%,#eef8ff 46%,#f8fbff 100%) fixed!important}
body.with-sidebar:after{background:linear-gradient(120deg,rgba(255,255,255,.72),rgba(255,255,255,.10) 46%,rgba(170,222,238,.08))!important}
.workspace-hero-single{display:grid!important;grid-template-columns:1fr!important;gap:14px;margin-bottom:14px}
.hero-solo{min-height:0!important;padding:22px 26px!important;background:linear-gradient(145deg,rgba(255,255,255,.82),rgba(240,250,255,.56))!important}
.hero-solo .eyebrow{margin-bottom:7px}.hero-solo h2{font-size:28px!important;max-width:980px}.hero-actions{margin-top:16px!important}
.workspace-hero-single .quick-project{background:linear-gradient(145deg,rgba(255,255,255,.68),rgba(243,250,255,.48));border:1px solid rgba(255,255,255,.86);border-radius:8px;padding:12px 14px;box-shadow:0 18px 44px rgba(69,121,157,.10),inset 0 1px 0 rgba(255,255,255,.96)}
.workspace-hero-single .quick-project summary{color:#143142}.workspace-hero-single .quick-project-form{grid-template-columns:minmax(220px,.55fr) minmax(300px,1fr) auto}
.filter-bar{margin:0 0 14px!important;padding:12px!important;gap:10px!important;align-items:center;background:linear-gradient(145deg,rgba(255,255,255,.74),rgba(245,251,255,.50))!important}
.filter-bar .input,.filter-bar .select{min-height:42px}.filter-bar .btn{min-height:42px}
.metric-grid{margin-bottom:14px!important}.metric{min-height:104px!important}.metric .value{font-size:30px!important}
.collect-panel{padding:13px 14px!important;margin-bottom:14px!important}
.collect-panel .source-picker-head{align-items:center;margin-bottom:8px}.collect-panel .source-picker-head b{font-size:18px}.collect-panel .source-picker-head span{font-size:12px;color:#748294!important}
.collect-panel .source-picker-head div span{display:block;margin-top:4px}
.collect-panel .bar{margin:0!important;gap:10px!important}.collect-panel label.muted{font-size:13px}.collect-panel .select{min-width:150px}
.premium-section-title{margin:16px 0 10px}.premium-section-title h2{font-size:23px!important}.premium-section-title p{font-size:13px!important}
.viz-grid{gap:14px!important}.agent-focus,.trend-card,.tone-card,.source-orbit,.insight-board,.citation-panel{margin-bottom:0}
.chart-title h3{font-size:22px!important}.chart-title span{font-size:12px!important}
.trend-controls{background:rgba(255,255,255,.42);border:1px solid rgba(255,255,255,.72);border-radius:999px;padding:5px;box-shadow:inset 0 1px 0 rgba(255,255,255,.8)}
.trend-controls .input,.trend-controls .select{min-height:34px;border-radius:999px!important}.trend-controls .btn{min-height:34px}
.widget-settings{width:min(360px,calc(100vw - 42px))!important;border-radius:8px!important;background:rgba(255,255,255,.92)!important;box-shadow:0 24px 70px rgba(69,121,157,.18),inset 0 1px 0 rgba(255,255,255,.96)!important}
.period-summary{margin:8px 0 10px!important}.period-summary span{background:rgba(255,255,255,.48)!important}
.layout{margin-top:0}.feed-card summary{background:rgba(255,255,255,.46)!important}
/* Collapsed sidebar fix: no slide-out cards, strict icon rail geometry. */
body.with-sidebar.sidebar-collapsed{padding-left:112px!important}
body.sidebar-collapsed .nav{left:20px!important;top:20px!important;bottom:20px!important;width:72px!important;padding:12px 9px!important;overflow:hidden!important;align-items:center!important}
body.sidebar-collapsed .sidebar-toggle{left:57px!important;top:35px!important;width:30px!important;height:30px!important;border-radius:8px!important;transform:none!important;font-size:14px!important}
body.sidebar-collapsed .nav-brand{width:100%;justify-content:center!important;padding:10px 0 14px!important;margin-top:24px!important;border-bottom:1px solid rgba(122,166,190,.20)!important}
body.sidebar-collapsed .brand-mark{width:44px!important;height:44px!important;border-radius:8px!important;font-size:16px!important}
body.sidebar-collapsed .nav-links{width:100%;display:grid!important;gap:10px!important;justify-items:center!important}
body.sidebar-collapsed .nav a{width:52px!important;height:52px!important;min-height:52px!important;padding:0!important;justify-content:center!important;border-radius:8px!important;background:transparent!important;box-shadow:none!important}
body.sidebar-collapsed .nav a.active{background:rgba(255,255,255,.50)!important;border:1px solid rgba(53,231,236,.46)!important;box-shadow:0 14px 32px rgba(69,121,157,.12),0 0 22px rgba(53,231,236,.16),inset 0 1px 0 rgba(255,255,255,.88)!important}
body.sidebar-collapsed .nav a:hover{background:rgba(255,255,255,.44)!important}
body.sidebar-collapsed .nav-ico{width:34px!important;height:34px!important;border-radius:8px!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.92),0 8px 18px rgba(69,121,157,.08)!important}
body.sidebar-collapsed .nav-bottom{width:100%;gap:10px!important;align-items:center!important;justify-items:center!important;padding-top:14px!important;border-top:1px solid rgba(122,166,190,.20)!important}
body.sidebar-collapsed .nav-user{width:52px!important;height:52px!important;padding:0!important;justify-content:center!important;background:rgba(255,255,255,.36)!important;border-radius:8px!important}
body.sidebar-collapsed .nav-avatar{width:34px!important;height:34px!important}
body.sidebar-collapsed .nav .logout{width:52px!important;height:52px!important}
/* Quiet background experiment: almost-white workspace, softer glass, no loud backdrop. */
body.with-sidebar{background:
radial-gradient(circle at 12% 0%,rgba(91,211,230,.065),transparent 30%),
radial-gradient(circle at 92% 4%,rgba(154,133,245,.045),transparent 28%),
linear-gradient(135deg,#fbfdff 0%,#f7fbff 48%,#fbfbff 100%) fixed!important}
body.with-sidebar:before{display:none!important}
body.with-sidebar:after{background:linear-gradient(120deg,rgba(255,255,255,.74),rgba(255,255,255,.16) 52%,rgba(225,242,248,.06))!important}
.with-sidebar .workspace-hero,.with-sidebar .metric,.with-sidebar .card,.with-sidebar .collect-panel,.with-sidebar .filter-bar,.with-sidebar .hero-main,.with-sidebar .hero-side,.with-sidebar .provider,.with-sidebar .project-card,.with-sidebar table,.feed-card{background:linear-gradient(145deg,rgba(255,255,255,.80),rgba(249,252,255,.62))!important;border-color:rgba(203,222,229,.78)!important;box-shadow:0 18px 44px rgba(54,91,112,.075),inset 0 1px 0 rgba(255,255,255,.88)!important;backdrop-filter:blur(14px) saturate(1.04)!important;-webkit-backdrop-filter:blur(14px) saturate(1.04)!important}
.with-sidebar .nav{background:rgba(255,255,255,.68)!important;border-color:rgba(255,255,255,.82)!important;box-shadow:0 24px 58px rgba(54,91,112,.12),inset 0 1px 0 rgba(255,255,255,.92)!important}
.with-sidebar .hero-main{background:linear-gradient(145deg,rgba(255,255,255,.86),rgba(250,253,255,.66))!important}
.with-sidebar .hero-side,.with-sidebar .agent-card,.with-sidebar .insight,.with-sidebar .legend-row,.with-sidebar .metric-pill{background:rgba(255,255,255,.64)!important;border-color:rgba(205,224,231,.76)!important}
.with-sidebar .trend-card,.with-sidebar .tone-card,.with-sidebar .source-orbit,.with-sidebar .agent-focus{background:linear-gradient(145deg,rgba(255,255,255,.82),rgba(248,252,255,.60))!important}
.with-sidebar .metric:after{background:linear-gradient(90deg,#27c5d2,#7fded9)!important;opacity:.52!important}
.with-sidebar .trend-chart{box-shadow:inset 0 1px 0 rgba(255,255,255,.90),0 20px 40px rgba(54,91,112,.055)!important}
.with-sidebar .trend-chart svg{background:linear-gradient(145deg,rgba(255,255,255,.44),rgba(245,251,255,.28))!important}
.with-sidebar .trend-line{filter:drop-shadow(0 5px 8px rgba(74,169,255,.16))!important}
.with-sidebar .source-ring{box-shadow:0 20px 46px rgba(54,91,112,.08)!important}
.with-sidebar .filter-bar,.with-sidebar .collect-panel{background:linear-gradient(145deg,rgba(255,255,255,.78),rgba(248,252,255,.56))!important}
.with-sidebar .input,.with-sidebar .select,.with-sidebar .textarea{background:rgba(255,255,255,.70)!important;border-color:rgba(199,218,226,.82)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.84)!important}
.with-sidebar .chip,.with-sidebar .pill,.with-sidebar .status,.with-sidebar .metric-state,.with-sidebar .agent-tag,.with-sidebar .period-summary span{box-shadow:none!important}
/* Keep violet as a CTA accent only; large panels stay clean white-cyan. */
body.with-sidebar{background:
radial-gradient(circle at 12% 0%,rgba(91,211,230,.060),transparent 30%),
radial-gradient(circle at 90% 2%,rgba(117,197,224,.040),transparent 28%),
linear-gradient(135deg,#fcfeff 0%,#f8fcff 52%,#fbfdff 100%) fixed!important}
.with-sidebar .workspace-hero,.workspace-hero-single,.hero-solo,.with-sidebar .hero-main{background:
linear-gradient(145deg,rgba(255,255,255,.90) 0%,rgba(247,253,255,.76) 54%,rgba(232,250,252,.52) 100%)!important}
.with-sidebar .hero-side{background:linear-gradient(145deg,rgba(255,255,255,.84),rgba(245,252,255,.62))!important}
.workspace-hero-single .quick-project,.with-sidebar .filter-bar,.with-sidebar .collect-panel{background:
linear-gradient(145deg,rgba(255,255,255,.82),rgba(247,252,255,.62))!important}
.with-sidebar .metric,.with-sidebar .card,.with-sidebar .provider,.with-sidebar .project-card,.feed-card{background:
linear-gradient(145deg,rgba(255,255,255,.82),rgba(250,253,255,.64))!important}
/* Button and navigation polish: no glow shadows, clearer depth, richer icons. */
.with-sidebar .btn,.with-sidebar .hero-actions .btn,.with-sidebar .quick-project-actions .btn,.with-sidebar button.btn{box-shadow:inset 0 1px 0 rgba(255,255,255,.54),inset 0 -2px 0 rgba(12,34,51,.16)!important;border:1px solid rgba(255,255,255,.70)!important}
.with-sidebar .btn:not(.light),.with-sidebar .hero-actions .btn:not(.light){background:linear-gradient(145deg,#31d5e3 0%,#28457A 58%,#28457A 100%)!important;color:#0d1828!important}
.with-sidebar .btn.secondary{background:linear-gradient(145deg,#21384c,#102f3a)!important;color:#fff!important;border-color:rgba(255,255,255,.28)!important}
.with-sidebar .btn.light,.with-sidebar .hero-actions .btn.light{background:linear-gradient(145deg,rgba(255,255,255,.88),rgba(245,252,255,.66))!important;color:#111827!important;border-color:rgba(255,255,255,.86)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.98),inset 0 -2px 0 rgba(37,78,98,.10)!important}
.with-sidebar .btn:hover,.with-sidebar .hero-actions .btn:hover{filter:saturate(1.08) brightness(1.01);transform:translateY(-1px)}
.with-sidebar .nav-ico{color:#0f8aa3!important;background:linear-gradient(145deg,rgba(255,255,255,.86),rgba(232,250,253,.70))!important;border:1px solid rgba(255,255,255,.86)!important}
.with-sidebar .nav a.active{background:linear-gradient(145deg,rgba(255,255,255,.92),rgba(223,251,253,.72))!important;border:1px solid rgba(62,224,234,.72)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.98),inset 0 -2px 0 rgba(37,196,211,.13)!important}
.with-sidebar .nav a.active .nav-ico{background:linear-gradient(145deg,#1ec7d4,#147b92)!important;color:#fff!important;border-color:rgba(255,255,255,.34)!important}
.with-sidebar .nav a:hover .nav-ico{color:#08758c!important}
body.sidebar-collapsed .nav a.active{background:linear-gradient(145deg,rgba(255,255,255,.94),rgba(218,251,253,.74))!important;border-color:rgba(62,224,234,.76)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.98),inset 0 -2px 0 rgba(37,196,211,.13)!important}
body.sidebar-collapsed .nav a.active .nav-ico{background:linear-gradient(145deg,#1ec7d4,#147b92)!important;color:#fff!important}
/* Dashboard typography audit: one visual voice for labels, values and navigation. */
body{font-family:"SF Pro Text","SF Pro Display",Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif!important;letter-spacing:0!important;font-variant-numeric:tabular-nums}
.with-sidebar .top h1,.hero-main h2,.pagehead h2,.premium-section-title h2,.chart-title h3,.provider h3,.card h3,.section-title,.source-picker-head b{font-family:"SF Pro Display","SF Pro Text",Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif!important;font-weight:760!important;letter-spacing:0!important}
.with-sidebar .top h1{font-size:34px!important;line-height:1.06!important}.with-sidebar .top p{font-size:15px!important;line-height:1.42!important;font-weight:560!important}
.hero-main h2{font-size:29px!important;line-height:1.12!important;font-weight:780!important}.hero-main .eyebrow{font-size:12px!important;letter-spacing:.035em!important;font-weight:760!important;color:#9c6a3b!important}
.with-sidebar .nav a{font-size:16px!important;font-weight:720!important;letter-spacing:0!important}
.with-sidebar .nav a.active{background:linear-gradient(145deg,rgba(255,255,255,.92),rgba(230,251,253,.68))!important;border-color:transparent!important;outline:0!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.98),inset 0 -2px 0 rgba(28,171,188,.12)!important}
.with-sidebar .nav a.active .nav-ico{background:linear-gradient(145deg,#18c4d3,#0f8aa3)!important;color:#fff!important}
body.sidebar-collapsed .nav a.active{border-color:transparent!important;outline:0!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.98),inset 0 -2px 0 rgba(28,171,188,.12)!important}
.with-sidebar .metric{padding:18px 18px 16px!important;min-height:116px!important;display:flex!important;flex-direction:column!important;justify-content:flex-start!important;gap:0!important}
.with-sidebar .metric .k{font-size:14px!important;line-height:1.2!important;font-weight:680!important;text-transform:none!important;letter-spacing:0!important;color:#667387!important;margin:0 0 12px!important}
.with-sidebar .metric .value{font-family:"SF Pro Display","SF Pro Text",Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif!important;color:#101827!important;margin:0!important;font-weight:780!important;letter-spacing:0!important}
.with-sidebar .metric .value-numeric{font-size:34px!important;line-height:.98!important}
.with-sidebar .metric .value-text{font-size:27px!important;line-height:1.10!important;max-width:12ch}
.with-sidebar .metric .caption{font-size:14px!important;line-height:1.28!important;font-weight:520!important;color:#69778a!important;margin-top:12px!important}
.with-sidebar .metric:after{left:18px!important;right:18px!important;height:2px!important;border-radius:99px!important;opacity:.42!important}
.with-sidebar .btn,.with-sidebar .hero-actions .btn,.with-sidebar button,.with-sidebar .select,.with-sidebar .input{font-family:"SF Pro Text",Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif!important;font-size:14px!important;font-weight:680!important;letter-spacing:0!important}
.with-sidebar .hero-actions .btn{font-size:15px!important}
.with-sidebar .btn.secondary{font-weight:760!important}
.with-sidebar .muted,.with-sidebar .hint,.with-sidebar .caption,.with-sidebar .source-picker-head span{font-weight:520!important;letter-spacing:0!important}
/* Dashboard readability tightening after visual review. */
.with-sidebar .metric .k{font-size:13px!important;font-weight:640!important;color:#748092!important;margin-bottom:13px!important}
.with-sidebar .metric .caption{font-size:13px!important;font-weight:500!important;color:#718095!important;margin-top:13px!important}
.with-sidebar .metric .value-numeric{font-size:33px!important;font-weight:760!important}
.with-sidebar .metric .value-text{font-size:25px!important;font-weight:760!important;line-height:1.12!important}
.with-sidebar .metric{min-height:112px!important}
.with-sidebar .metric-grid{gap:12px!important}
.with-sidebar .nav a.active{background:linear-gradient(145deg,rgba(255,255,255,.88),rgba(232,250,252,.62))!important}
.with-sidebar .nav a.active .nav-ico{background:linear-gradient(145deg,#1fc9d6,#128fa7)!important}
/* Query performance panel: full queries, readable counts, expandable actions. */
.query-performance{padding:22px!important}
.query-performance .chart-title{margin-bottom:14px!important}
.query-performance .chart-title h3{font-size:24px!important;line-height:1.14!important}
.query-hit-list{display:grid;gap:10px}
.query-hit{border:1px solid rgba(201,220,225,.80);border-radius:8px;background:linear-gradient(145deg,rgba(255,255,255,.72),rgba(248,253,255,.56));overflow:hidden}
.query-hit summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:34px minmax(0,1fr) auto;align-items:start;gap:12px;padding:13px 14px}
.query-hit summary::-webkit-details-marker{display:none}
.query-hit summary:after{content:"";grid-column:2/3;width:7px;height:7px;border-right:2px solid #168aa1;border-bottom:2px solid #168aa1;transform:rotate(45deg);justify-self:start;margin-top:5px;opacity:.72}
.query-hit[open] summary:after{transform:rotate(225deg);margin-top:9px}
.query-rank{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;background:rgba(228,248,250,.82);color:#12879f;font-weight:760;font-size:13px}
.query-title{color:#172033;font-size:16px;font-weight:680;line-height:1.28;overflow-wrap:anywhere}
.query-count{font-size:24px;line-height:1;color:#111827;font-weight:760;justify-self:end}
.query-hit-detail{display:grid;grid-template-columns:minmax(140px,1fr) auto auto;align-items:center;gap:12px;padding:0 14px 13px 60px;color:#718095;font-size:13px;font-weight:560}
.query-progress{height:9px;border-radius:999px;background:rgba(211,226,233,.70);overflow:hidden}
.query-progress i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#27c9d8,#28457A);box-shadow:inset 0 1px 0 rgba(255,255,255,.44)}
.query-hit-detail a{font-weight:720;color:#137d93;white-space:nowrap}
.query-hit:hover{background:linear-gradient(145deg,rgba(255,255,255,.84),rgba(240,252,254,.64));border-color:rgba(148,213,222,.78)}
@media(max-width:700px){.query-performance{padding:16px!important}.query-hit summary{grid-template-columns:30px minmax(0,1fr);gap:10px}.query-count{grid-column:2/3;justify-self:start;font-size:20px}.query-hit summary:after{grid-column:2/3}.query-hit-detail{grid-template-columns:1fr;padding:0 12px 12px 52px;gap:8px}.query-hit-detail a{white-space:normal}}
/* Query detail cleanup: no cramped secondary row. */
.query-hit summary{position:relative}
.query-hit summary:after{position:absolute;left:62px;bottom:12px;grid-column:auto!important;margin:0!important}
.query-hit-detail{grid-template-columns:1fr auto!important;gap:9px 12px!important}
.query-progress{grid-column:1/-1}
.query-hit-detail span{white-space:normal;line-height:1.25}
.query-hit-detail a{display:inline-flex;align-items:center;justify-content:center;min-height:30px;padding:5px 10px;border-radius:999px;background:rgba(232,250,253,.72);border:1px solid rgba(190,229,236,.80)}
@media(max-width:700px){.query-hit summary:after{left:52px}.query-hit-detail{grid-template-columns:1fr!important}.query-hit-detail a{justify-self:start}}
/* Daily chart now uses the empty space for decision-ready period insights. */
.daily-insights{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:18px}
.daily-insight{display:block;min-height:104px;padding:13px;border-radius:8px;background:linear-gradient(145deg,rgba(255,255,255,.62),rgba(241,252,254,.46));border:1px solid rgba(202,224,231,.78);color:#172033}
.daily-insight:hover{text-decoration:none;background:linear-gradient(145deg,rgba(255,255,255,.82),rgba(230,250,253,.60))}
.daily-insight span{display:block;color:#718095;font-size:12px;font-weight:660;line-height:1.2}
.daily-insight b{display:block;color:#111827;font-size:22px;font-weight:760;line-height:1.08;margin-top:8px}
.daily-insight em{display:block;color:#6b788a;font-style:normal;font-size:12px;font-weight:540;line-height:1.24;margin-top:8px}
.daily-insight-peak{background:linear-gradient(145deg,rgba(232,252,254,.78),rgba(255,255,255,.62));border-color:rgba(91,211,230,.44)}
.daily-top-days{display:grid;grid-template-columns:auto minmax(0,1fr);gap:12px;align-items:center;margin-top:12px;padding:12px 13px;border-radius:8px;background:rgba(255,255,255,.46);border:1px solid rgba(205,224,231,.66)}
.daily-top-days b{display:block;color:#172033;font-size:14px;font-weight:740}.daily-top-days span{display:block;color:#718095;font-size:12px;font-weight:520;margin-top:3px}
.daily-top-days nav{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}
.daily-top-days nav a{display:inline-flex;align-items:center;gap:8px;min-height:30px;padding:5px 10px;border-radius:999px;background:rgba(232,250,253,.72);border:1px solid rgba(190,229,236,.80);color:#137d93;font-weight:700}
.daily-top-days nav a span{margin:0;color:#137d93;font-size:13px;font-weight:700}.daily-top-days nav a b{font-size:13px;color:#111827}
.viz-grid{align-items:start!important}.viz-grid>*{align-self:start!important}
@media(max-width:1180px){.daily-insights{grid-template-columns:repeat(2,minmax(0,1fr))}.daily-top-days{grid-template-columns:1fr}.daily-top-days nav{justify-content:flex-start}}
@media(max-width:700px){.daily-insights{grid-template-columns:1fr}.daily-insight{min-height:0}.daily-top-days nav a{width:100%;justify-content:space-between}}
@media(max-width:1180px){.source-orbit-layout{grid-template-columns:1fr}.source-orbit-core{min-height:150px}.source-ring{width:86px;height:86px}.source-ring span{width:48px;height:48px;font-size:22px}.source-orbit-list{grid-template-columns:repeat(auto-fit,minmax(min(190px,100%),1fr))}.insight-stream{grid-template-columns:1fr}}
@media(max-width:520px){.source-orbit{padding:14px}.source-orbit-card{padding:10px}.source-orbit-icon{width:32px;height:32px}.source-orbit-top{align-items:flex-start}.source-orbit-top b{white-space:normal;line-height:1.15}.source-orbit-core{min-height:132px}}
@media(max-width:1180px){.workspace-hero{grid-template-columns:1fr}.hero-main,.hero-side{min-height:0}.signal-grid{grid-template-columns:repeat(4,1fr)}}
@media(max-width:900px){body.with-sidebar,body.with-sidebar.sidebar-collapsed{padding-left:0}.nav{position:relative;left:auto;top:auto;bottom:auto;width:auto;margin:12px 12px 0;padding:10px;display:block;overflow-x:auto;white-space:nowrap}.nav-brand,.nav-bottom{display:none}.nav-links{display:flex;gap:8px}.nav a{display:inline-flex}.sidebar-toggle{display:none}.grid,.metric-grid,.layout,.charts,.settings,.split,.viz-grid,.insights,.metric-list,.legend,.source-checks,.admin-grid,.project-switcher,.quick-project-form,.agent-hero,.agent-grid,.agent-evidence,.workspace-hero,.signal-grid,.ai-chat{grid-template-columns:1fr}.project-switcher form{display:block}.project-select-field select{min-width:0;width:100%;box-sizing:border-box}.quick-project-actions{display:grid}.pagehead,.chart-title,.source-picker-head,.premium-section-title{display:block}.chart-title span,.source-picker-head span{display:block;margin-top:4px}.wrap,.with-sidebar .wrap{padding:16px}.top,.with-sidebar .top{padding:18px}.spark{overflow-x:auto}.project-switcher{display:grid}.hero-main h2{font-size:24px}.feed-card summary{grid-template-columns:1fr;gap:8px}.feed-source,.feed-more{text-align:left}.feed-detail{grid-template-columns:1fr}.feed-detail-wide{grid-column:auto}}
@media(max-width:700px){.citation-panel{padding:14px}.citation-table-wrap{overflow:visible}.citation-table,.citation-table thead,.citation-table tbody,.citation-table tr,.citation-table td{display:block;width:100%!important}.citation-table{border:0;background:transparent;box-shadow:none;table-layout:auto}.citation-table thead{display:none}.citation-table tr{margin:0 0 12px;border:1px solid rgba(202,221,228,.86);border-radius:8px;background:rgba(255,255,255,.82);box-shadow:0 12px 26px rgba(38,82,104,.07);overflow:hidden}.citation-table td{border-top:0!important;padding:10px 12px 11px;background:transparent!important;font-size:14px}.citation-table td+td{border-top:1px solid rgba(226,235,239,.86)!important}.citation-table td:before{content:attr(data-label);display:block;margin-bottom:4px;color:#73858d;font-size:11px;font-weight:950;text-transform:uppercase;letter-spacing:.035em}.citation-table td:first-child a{font-size:16px;display:block}.citation-table .muted{font-size:13px}.citation-table .metric-mini{padding-top:6px;margin-top:6px}.citation-table .metric-mini span{white-space:normal}.citation-table b{font-size:18px;color:#102f3a}.citation-table td:nth-child(3) b a{font-size:13px}.citation-panel .chart-title h3{font-size:20px}.citation-panel .chart-title span{font-size:13px}}
/* Apple premium visual system. Final layer intentionally neutralizes previous experiments. */
:root{
  --accent:#28457A;
  --accent-press:#1F3661;
  --accent-soft:#EAF3FE;
  --bg:#FBFBFD;
  --card:#FFFFFF;
  --border:#EBEBF0;
  --hairline:#F0F0F3;
  --ink:#1D1D1F;
  --ink-2:#6E6E73;
  --ink-3:#A1A1A6;
  --pos:#2D9F6F;
  --pos-bg:#EEF7F2;
  --warn:#B8860B;
  --warn-bg:#FBF4E3;
  --danger:#B42318;
  --danger-bg:#FFF1F0;
  --r-card:18px;
  --r-inner:12px;
  --r-pill:980px;
  --shadow:0 1px 2px rgba(0,0,0,.04),0 1px 1px rgba(0,0,0,.02);
  --shadow-hover:0 4px 16px rgba(0,0,0,.05);
  --font:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",Inter,sans-serif;
}
html{background:var(--bg)!important}
body,body.with-sidebar,body.with-sidebar.sidebar-collapsed,.login-shell{
  background:var(--bg)!important;color:var(--ink)!important;font-family:var(--font)!important;
  letter-spacing:0!important;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility
}
body.with-sidebar:before,body.with-sidebar:after,.top:after,.wrap:before,.nav:before,
.workspace-hero:before,.metric:before,.metric:after,.card:before,.hero-main:before,.hero-side:before,.provider:before,
.source-orbit:before{display:none!important;content:none!important}
body.with-sidebar{padding-left:280px!important;transition:padding-left .15s ease!important}
body.with-sidebar.sidebar-collapsed{padding-left:104px!important}
.top,.with-sidebar .top{background:var(--bg)!important;color:var(--ink)!important;box-shadow:none!important;padding:40px 40px 8px!important;overflow:visible!important}
.top h1,.with-sidebar .top h1{color:var(--ink)!important;font-size:34px!important;line-height:1.08!important;font-weight:600!important;letter-spacing:-.8px!important;text-shadow:none!important;margin:0!important}
.top p,.with-sidebar .top p{color:var(--ink-2)!important;font-size:15px!important;font-weight:400!important;line-height:1.45!important;margin:8px 0 0!important;max-width:980px!important}
.wrap,.with-sidebar .wrap{max-width:none!important;margin:0!important;padding:24px 40px 64px!important}
a,.feed-main a,.barline a:first-child,.source-orbit-detail a{color:var(--ink)!important;text-shadow:none!important;text-decoration:none!important}
a:hover{text-decoration:underline!important}
.nav{
  position:fixed!important;left:0!important;top:0!important;bottom:0!important;width:248px!important;margin:0!important;padding:28px 16px!important;
  display:flex!important;flex-direction:column!important;gap:20px!important;z-index:40!important;border-radius:0!important;
  background:var(--card)!important;border:0!important;border-right:1px solid var(--border)!important;box-shadow:none!important;
  backdrop-filter:none!important;-webkit-backdrop-filter:none!important;overflow:hidden!important;white-space:normal!important
}
.nav-brand{display:flex!important;align-items:center!important;gap:12px!important;min-height:0!important;padding:0 8px 24px!important;margin:0!important;border-bottom:1px solid var(--hairline)!important}
.brand-mark{width:40px!important;height:40px!important;border-radius:10px!important;background:var(--ink)!important;color:#fff!important;border:0!important;box-shadow:none!important;display:grid!important;place-items:center!important;font-size:13px!important;font-weight:600!important;letter-spacing:.5px!important;flex:0 0 auto!important}
.nav-brand b,.nav-user b{display:block!important;color:var(--ink)!important;font-size:16px!important;line-height:1.12!important;font-weight:600!important;letter-spacing:-.2px!important}
.nav-brand small,.nav-user small{display:block!important;color:var(--ink-3)!important;font-size:11px!important;margin-top:2px!important;line-height:1.2!important;font-weight:400!important}
.nav-links{display:grid!important;gap:4px!important}
.nav a{display:flex!important;align-items:center!important;gap:12px!important;min-height:42px!important;padding:10px 12px!important;border-radius:var(--r-inner)!important;border:0!important;background:transparent!important;color:var(--ink-2)!important;box-shadow:none!important;font-size:14px!important;font-weight:450!important;line-height:1.15!important;transition:background .15s,color .15s,transform .15s,box-shadow .15s!important}
.nav a:hover{background:var(--bg)!important;color:var(--ink)!important;box-shadow:none!important;transform:none!important;text-decoration:none!important}
.nav a.active{background:var(--accent-soft)!important;color:var(--accent)!important;font-weight:550!important;border:0!important;outline:0!important;box-shadow:none!important}
.nav-ico{width:18px!important;height:18px!important;min-width:18px!important;border-radius:0!important;background:transparent!important;border:0!important;box-shadow:none!important;color:var(--ink-3)!important;display:grid!important;place-items:center!important}
.nav-ico svg{width:18px!important;height:18px!important;display:block!important;stroke:currentColor!important;stroke-width:2!important;fill:none!important;stroke-linecap:round!important;stroke-linejoin:round!important}
.nav a:hover .nav-ico{color:var(--ink-2)!important}
.nav a.active .nav-ico{background:transparent!important;color:var(--accent)!important;border:0!important;box-shadow:none!important}
.nav-bottom{margin-top:auto!important;display:grid!important;gap:8px!important;padding-top:16px!important;border-top:1px solid var(--hairline)!important}
.nav-user{display:flex!important;align-items:center!important;gap:12px!important;padding:8px 12px!important;border-radius:var(--r-inner)!important;background:transparent!important;border:0!important}
.nav-avatar{width:32px!important;height:32px!important;border-radius:50%!important;background:var(--bg)!important;border:1px solid var(--border)!important;color:var(--ink-2)!important;box-shadow:none!important;font-weight:600!important;display:grid!important;place-items:center!important}
.nav .logout{color:var(--ink-2)!important}
.sidebar-toggle{position:fixed!important;left:224px!important;top:32px!important;width:36px!important;height:36px!important;border:1px solid var(--border)!important;border-radius:var(--r-inner)!important;background:var(--card)!important;color:var(--ink-2)!important;box-shadow:var(--shadow)!important;font-size:0!important;z-index:45!important;transition:background .15s,border-color .15s,transform .05s,left .15s!important}
.sidebar-toggle:before{content:"";width:16px;height:2px;display:block;margin:auto;background:var(--ink-2);box-shadow:0 5px 0 var(--ink-2),0 10px 0 var(--ink-2)}
.sidebar-toggle:hover{background:var(--bg)!important;border-color:var(--ink-3)!important}
.sidebar-toggle:active{transform:scale(.98)!important}
body.sidebar-collapsed .nav{width:72px!important;padding:20px 12px!important;align-items:center!important}
body.sidebar-collapsed .sidebar-toggle{left:54px!important;top:28px!important;transform:none!important}
body.sidebar-collapsed .nav-brand{justify-content:center!important;padding:44px 0 18px!important;width:100%!important}
body.sidebar-collapsed .brand-mark{width:44px!important;height:44px!important;border-radius:12px!important}
body.sidebar-collapsed .nav-label{display:none!important}
body.sidebar-collapsed .nav-links{width:100%!important;gap:8px!important}
body.sidebar-collapsed .nav a{width:48px!important;height:48px!important;min-height:48px!important;justify-content:center!important;padding:0!important}
body.sidebar-collapsed .nav a.active{background:var(--accent-soft)!important;border:0!important;box-shadow:none!important}
body.sidebar-collapsed .nav-ico{width:20px!important;height:20px!important}
body.sidebar-collapsed .nav-ico svg{width:20px!important;height:20px!important}
body.sidebar-collapsed .nav-bottom{width:100%!important;align-items:center!important;justify-items:center!important}
body.sidebar-collapsed .nav-user{width:48px!important;height:48px!important;padding:0!important;justify-content:center!important}
body.sidebar-collapsed .nav-avatar{width:32px!important;height:32px!important}
body.sidebar-collapsed .nav .logout{width:48px!important;height:48px!important;justify-content:center!important}
.workspace-hero,.workspace-hero-single,.hero-main,.hero-side,.hero-solo,.project-switcher,.collect-panel,.filter-bar,.card,.metric,.provider,.project-card,
table,.feed-card,.source-orbit-card,.source-orbit-core,.signal-card,.tone-funnel-viz,.ai-chat-panel,.ai-answer,.agent-card,.insight,.metric-pill,.legend-row,
.signal,.daily-insight,.daily-top-days,.query-hit,.widget-settings,.login-card{
  background:var(--card)!important;border:1px solid var(--border)!important;border-radius:var(--r-card)!important;box-shadow:var(--shadow)!important;
  backdrop-filter:none!important;-webkit-backdrop-filter:none!important;overflow:hidden;transition:box-shadow .15s,transform .15s,border-color .15s,background .15s!important
}
.card,.metric,.hero-main,.hero-side,.provider,.project-card,.feed-card,.query-hit,.daily-insight,.signal-card,.source-orbit-card{position:relative}
.card:hover,.metric:hover,.hero-main:hover,.hero-side:hover,.provider:hover,.project-card:hover,.feed-card:hover,.query-hit:hover,.daily-insight:hover,.signal-card:hover,.source-orbit-card:hover{
  transform:translateY(-1px)!important;box-shadow:var(--shadow-hover)!important;background:var(--card)!important;border-color:var(--border)!important
}
.hero-main,.hero-side,.hero-solo{padding:28px!important;min-height:0!important}
.hero-main h2,.hero-solo h2,.pagehead h2,.premium-section-title h2,.chart-title h3,.provider h3,.card h3,.section-title,.source-picker-head b{
  color:var(--ink)!important;font-family:var(--font)!important;font-weight:600!important;letter-spacing:-.5px!important;text-shadow:none!important
}
.hero-main h2,.hero-solo h2{font-size:32px!important;line-height:1.12!important;letter-spacing:-.9px!important;max-width:980px!important}
.pagehead h2{font-size:28px!important}.chart-title h3,.premium-section-title h2{font-size:22px!important}
.provider h3,.card h3,.section-title,.source-picker-head b{font-size:20px!important}
.hero-main p,.hero-solo p,.pagehead p,.premium-section-title p,.hint,.muted,.provider small,.chart-title span,.source-picker-head span,.snippet,.agent-card p,.agent-list li,.metric-detail p,.metric-detail ul,.metric-mini,.row span,.source-orbit-card p,.signal-card p{
  color:var(--ink-2)!important;font-weight:400!important;line-height:1.45!important;text-shadow:none!important
}
.eyebrow{color:var(--ink-3)!important;font-size:12px!important;font-weight:600!important;letter-spacing:.6px!important;text-transform:uppercase!important}
.wrap .card,.provider,.collect-panel,.filter-bar{padding:24px!important}
.metric{padding:20px!important;min-height:124px!important;display:flex!important;flex-direction:column!important;justify-content:flex-start!important}
.metric .k,.k{color:var(--ink-2)!important;font-size:13px!important;font-weight:500!important;line-height:1.25!important;text-transform:none!important;letter-spacing:0!important;margin:0 0 14px!important}
.metric .value,.v,.metric-number,.agent-score,.source-orbit-top b,.signal-card b,.legend-row b,.insight b,.metric-pill b,.query-count,.daily-insight b{
  color:var(--ink)!important;font-family:var(--font)!important;font-weight:600!important;letter-spacing:-1px!important;text-shadow:none!important
}
.metric .value-numeric,.metric .value{font-size:34px!important;line-height:1!important}
.metric .value-text{font-size:28px!important;line-height:1.1!important;letter-spacing:-.6px!important;max-width:none!important}
.metric .caption{color:var(--ink-2)!important;font-size:13px!important;font-weight:400!important;line-height:1.32!important;margin-top:14px!important}
.btn,.feed-page-btn,.ai-suggestions button{
  font-family:var(--font)!important;font-size:14px!important;font-weight:550!important;letter-spacing:0!important;border-radius:var(--r-inner)!important;
  padding:11px 20px!important;min-height:42px!important;border:1px solid var(--border)!important;background:var(--card)!important;color:var(--ink)!important;
  box-shadow:none!important;text-shadow:none!important;filter:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;gap:8px!important;
  transition:background .15s,border-color .15s,color .15s,transform .05s!important
}
button.btn[type="submit"],form .btn[type="submit"]:not(.light),.login-card .btn,.hero-actions>.btn:not(.light):first-of-type,.collect-panel button.btn[type="submit"]{
  background:var(--accent)!important;border-color:var(--accent)!important;color:#fff!important
}
.btn:hover,.feed-page-btn:hover,.ai-suggestions button:hover{background:var(--card)!important;border-color:var(--ink-3)!important;text-decoration:none!important;transform:none!important}
button.btn[type="submit"]:hover,form .btn[type="submit"]:not(.light):hover,.login-card .btn:hover,.hero-actions>.btn:not(.light):first-of-type:hover,.collect-panel button.btn[type="submit"]:hover{
  background:var(--accent-press)!important;border-color:var(--accent-press)!important;color:#fff!important
}
.btn:active,.feed-page-btn:active,.ai-suggestions button:active{transform:scale(.98)!important}
.btn.light,.btn.secondary,.feed-page-btn{background:var(--card)!important;color:var(--ink)!important;border-color:var(--border)!important}
.input,.select,.textarea,input,select,textarea{
  font-family:var(--font)!important;background:var(--card)!important;color:var(--ink)!important;border:1px solid var(--border)!important;border-radius:var(--r-inner)!important;
  box-shadow:none!important;padding:10px 12px!important;font-size:14px!important;line-height:1.35!important;transition:border-color .15s,box-shadow .15s!important
}
.input::placeholder,.textarea::placeholder,input::placeholder,textarea::placeholder{color:var(--ink-3)!important}
.input:focus,.select:focus,.textarea:focus,input:focus,select:focus,textarea:focus{outline:3px solid var(--accent-soft)!important;border-color:var(--accent)!important}
.textarea,textarea{border-radius:var(--r-inner)!important}
.chip,.pill,.status,.metric-state,.agent-tag,.period-summary span{
  display:inline-flex!important;align-items:center!important;width:auto!important;border-radius:var(--r-pill)!important;border:0!important;box-shadow:none!important;
  padding:4px 9px!important;font-size:11px!important;line-height:1.2!important;font-weight:600!important;letter-spacing:0!important;background:var(--hairline)!important;color:var(--ink-2)!important
}
.positive,.metric-state.good,.risk-low,.on{background:var(--pos-bg)!important;color:var(--pos)!important}
.negative,.metric-state.bad,.risk-high,.off{background:var(--danger-bg)!important;color:var(--danger)!important}
.neutral{background:var(--hairline)!important;color:var(--ink-2)!important}
.metric-state.warn,.risk-mid,.signal.gold{background:var(--warn-bg)!important;color:var(--warn)!important}
.track,.source-orbit-track,.tone-stack{background:var(--hairline)!important;border-radius:var(--r-pill)!important;box-shadow:none!important}
.fill,.source-orbit-track i,.query-progress i{background:#5E9FEA!important;border-radius:inherit!important;box-shadow:none!important}
.fill.pos,.tone-pos{background:var(--pos)!important}.fill.neg,.tone-neg{background:var(--danger)!important}.fill.neu,.tone-neu{background:var(--ink-3)!important}
.query-progress{height:8px!important;background:var(--hairline)!important;border-radius:var(--r-pill)!important;overflow:hidden!important}
.spark{border-left:1px solid var(--hairline)!important;border-bottom:1px solid var(--hairline)!important;gap:8px!important}
.spark-col{background:#5E9FEA!important;border-radius:6px 6px 0 0!important;box-shadow:none!important}
.spark-col b{color:var(--ink)!important;font-weight:600!important}.spark-col span{color:var(--ink-2)!important}
.trend-card,.tone-card,.source-orbit,.insight-board,.agent-focus{background:var(--card)!important}
.trend-chart{background:var(--card)!important;border:1px solid var(--hairline)!important;border-radius:var(--r-card)!important;box-shadow:none!important}
.trend-chart svg{background:var(--card)!important}
.trend-line{stroke:var(--accent)!important;stroke-width:3!important;filter:none!important}
.trend-dot,.trend-point .trend-dot{fill:#fff!important;stroke:var(--accent)!important;stroke-width:3!important;filter:none!important}
.trend-dot-muted{fill:var(--accent-soft)!important;stroke:#A8CEF7!important}
.trend-axis,.trend-grid{stroke:var(--hairline)!important;stroke-width:1!important;stroke-dasharray:none!important}
.trend-area{fill:rgba(40,69,122,.06)!important}
.trend-active-band{fill:rgba(40,69,122,.08)!important}
.trend-tooltip{fill:var(--ink)!important;filter:none!important}.trend-tooltip-title{fill:#C7C7CC!important}.trend-tooltip-value{fill:#fff!important}
.tone-funnel-shape{filter:none!important;fill:rgba(40,69,122,.16)!important}.tone-funnel-line{stroke:var(--hairline)!important}.tone-funnel-label{fill:var(--ink-2)!important}.tone-funnel-percent{fill:var(--ink)!important}
table{border-collapse:separate!important;border-spacing:0!important;background:var(--card)!important;border-radius:var(--r-card)!important;overflow:hidden!important}
th{background:var(--ink)!important;color:#fff!important;padding:14px 16px!important;font-size:12px!important;font-weight:600!important;letter-spacing:.02em!important;text-transform:uppercase!important;border:0!important}
td{background:var(--card)!important;color:var(--ink-2)!important;border-top:1px solid var(--hairline)!important;padding:14px 16px!important;font-size:14px!important}
tr:hover td{background:var(--bg)!important}
.feed-card summary{background:var(--card)!important;border:0!important;grid-template-columns:130px minmax(0,1fr) minmax(120px,180px) 92px!important;padding:16px 20px!important}
.feed-card[open] summary,.feed-detail,.metric-detail,.source-orbit-detail{background:var(--bg)!important;border-color:var(--hairline)!important}
.feed-detail div{background:var(--card)!important;border:1px solid var(--border)!important;border-radius:var(--r-inner)!important}
.feed-main a{color:var(--ink)!important;font-size:16px!important;font-weight:600!important;letter-spacing:-.2px!important}
.feed-main span,.feed-source,.feed-more{color:var(--ink-2)!important}
.feed-more{font-weight:600!important}.feed-more:hover{color:var(--accent)!important}
.query-performance{padding:24px!important}
.query-hit{background:var(--card)!important;border-radius:var(--r-card)!important}
.query-rank{background:var(--hairline)!important;color:var(--ink-2)!important;border-radius:var(--r-inner)!important;font-weight:600!important}
.query-title{color:var(--ink)!important;font-weight:600!important;letter-spacing:-.2px!important}
.query-hit summary:after{border-color:var(--accent)!important}
.query-hit-detail{color:var(--ink-2)!important}
.query-hit-detail a,.daily-top-days nav a{background:var(--card)!important;border:1px solid var(--border)!important;color:var(--ink)!important;box-shadow:none!important;border-radius:var(--r-pill)!important}
.query-hit-detail a:hover,.daily-top-days nav a:hover{border-color:var(--accent)!important;text-decoration:none!important}
.daily-insights{gap:16px!important}.daily-insight{background:var(--card)!important;border-radius:var(--r-card)!important}
.daily-insight span,.daily-insight em,.daily-top-days span{color:var(--ink-2)!important}.daily-insight b,.daily-top-days b{color:var(--ink)!important}
.daily-insight-peak{border-color:var(--accent)!important;background:var(--card)!important}
.daily-top-days{background:var(--card)!important;border-radius:var(--r-card)!important}
.source-ring{background:var(--card)!important;border:10px solid var(--hairline)!important;border-top-color:#5E9FEA!important;border-right-color:#5E9FEA!important;box-shadow:none!important}
.source-ring span{background:var(--ink)!important;color:#fff!important;border-radius:var(--r-inner)!important;box-shadow:none!important}
.source-orbit-icon,.signal-icon{background:var(--hairline)!important;color:var(--ink-2)!important;border:0!important;border-radius:var(--r-inner)!important;box-shadow:none!important}
.source-orbit-track i{background:#5E9FEA!important}
.coverage-note{background:var(--card)!important;border:1px solid var(--border)!important;border-radius:var(--r-inner)!important;color:var(--ink-2)!important}
.help-dot,.gear{background:var(--card)!important;color:var(--ink-2)!important;border:1px solid var(--border)!important;border-radius:var(--r-inner)!important;box-shadow:var(--shadow)!important}
.help-dot:hover:after{background:var(--ink)!important;color:#fff!important;box-shadow:var(--shadow-hover)!important}
.widget-settings{background:var(--card)!important;border-color:var(--border)!important;border-radius:var(--r-card)!important;box-shadow:0 18px 40px rgba(0,0,0,.08)!important}
.login-card{width:min(430px,100%)!important;padding:28px!important}.login-card h1{color:var(--ink)!important}.login-card p{color:var(--ink-2)!important}
pre.card{background:var(--bg)!important}
@media(max-width:900px){
  body.with-sidebar,body.with-sidebar.sidebar-collapsed{padding-left:0!important}
  .nav{position:relative!important;left:auto!important;top:auto!important;bottom:auto!important;width:auto!important;margin:12px!important;padding:10px!important;display:block!important;overflow-x:auto!important;border:1px solid var(--border)!important;border-radius:var(--r-card)!important}
  .nav-brand,.nav-bottom{display:none!important}.nav-links{display:flex!important;gap:8px!important}.nav a{display:inline-flex!important;white-space:nowrap!important}.sidebar-toggle{display:none!important}
  .wrap,.with-sidebar .wrap{padding:16px!important}.top,.with-sidebar .top{padding:18px 16px 8px!important}
  .feed-card summary{grid-template-columns:1fr!important}
}
/* Liquid Glass light visual system. Final layer: one accent, one geometry, no legacy gradients. */
:root{
  --accent:#28457A;--accent-press:#1F3661;--accent-soft:rgba(40,69,122,0.10);
  --base:#EAEEF5;
  --glass:rgba(255,255,255,0.55);--glass-strong:rgba(255,255,255,0.72);
  --glass-border:rgba(255,255,255,0.85);--glass-hi:rgba(255,255,255,0.95);
  --ink:#1D1D1F;--ink-2:#57575C;--ink-3:#8A8A90;
  --pos:#1E9E6A;--neu:var(--accent);--neg:#C0493D;--warn:#B8860B;
  --r-card:24px;--r-inner:16px;--r-pill:980px;
  --blur:blur(28px) saturate(180%);
  --grid:rgba(0,0,0,0.06);
  --panel-shadow:inset 0 1px 0 var(--glass-hi),0 8px 32px rgba(60,70,120,0.12);
  --inner:rgba(255,255,255,0.45);
  --inner-strong:rgba(255,255,255,0.66);
  --font:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Inter",sans-serif;
}
html{background:var(--base)!important}
body,body.with-sidebar,body.with-sidebar.sidebar-collapsed,.login-shell{
  min-height:100vh;background:var(--base)!important;color:var(--ink)!important;font-family:var(--font)!important;
  letter-spacing:0!important;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility
}
body.with-sidebar:before,body:before{
  content:""!important;display:block!important;position:fixed!important;inset:0!important;z-index:-2!important;pointer-events:none!important;
  background:
    radial-gradient(42% 52% at 14% 16%,rgba(40,69,122,0.26),transparent 70%),
    radial-gradient(40% 46% at 86% 12%,rgba(40,160,170,0.18),transparent 70%),
    radial-gradient(48% 50% at 76% 84%,rgba(70,90,150,0.18),transparent 72%),
    radial-gradient(42% 42% at 24% 92%,rgba(255,150,120,0.12),transparent 72%)!important;
  filter:blur(12px)!important;opacity:1!important
}
body.with-sidebar:after,.top:after,.wrap:before,.nav:before,.workspace-hero:before,.workspace-hero:after,.metric:before,.metric:after,.card:before,.card:after,.hero-main:before,.hero-side:before,.provider:before,.source-orbit:before{display:none!important;content:none!important}
body.with-sidebar{padding-left:288px!important;transition:padding-left .15s ease!important}
body.with-sidebar.sidebar-collapsed{padding-left:112px!important}
.glass,.nav,.workspace-hero,.workspace-hero-single,.hero-main,.hero-side,.hero-solo,.collect-panel,.filter-bar,.card,.metric,.provider,.project-card,.login-card,.ai-chat-panel,.ai-answer,.agent-card,.widget-settings{
  background:var(--glass)!important;backdrop-filter:var(--blur)!important;-webkit-backdrop-filter:var(--blur)!important;
  border:1px solid var(--glass-border)!important;border-radius:var(--r-card)!important;box-shadow:var(--panel-shadow)!important;
  overflow:hidden;transition:box-shadow .15s ease,transform .15s ease,border-color .15s ease,background .15s ease!important
}
.card:hover,.metric:hover,.hero-main:hover,.hero-side:hover,.provider:hover,.project-card:hover,.feed-card:hover,.query-hit:hover,.daily-insight:hover,.signal-card:hover,.source-orbit-card:hover{
  transform:translateY(-1px)!important;box-shadow:inset 0 1px 0 var(--glass-hi),0 12px 36px rgba(60,70,120,.14)!important
}
.top,.with-sidebar .top{background:transparent!important;box-shadow:none!important;color:var(--ink)!important;padding:40px 40px 8px!important;overflow:visible!important}
.wrap,.with-sidebar .wrap{max-width:none!important;margin:0!important;padding:24px 40px 72px!important}
.top h1,.with-sidebar .top h1,.hero-main h2,.hero-solo h2{
  color:var(--ink)!important;font-size:36px!important;line-height:1.08!important;font-weight:650!important;letter-spacing:-1px!important;margin:0!important;text-shadow:none!important
}
.top p,.with-sidebar .top p,.hero-main p,.hero-solo p,.pagehead p,.premium-section-title p,.hint,.muted,.provider small,.chart-title span,.source-picker-head span,.snippet,.agent-card p,.agent-list li,.metric-detail p,.metric-detail ul,.row span,.source-orbit-card p,.signal-card p{
  color:var(--ink-2)!important;font-weight:400!important;line-height:1.45!important;text-shadow:none!important
}
h1,h2,h3,h4,.pagehead h2,.premium-section-title h2,.chart-title h3,.provider h3,.card h3,.section-title,.source-picker-head b{
  color:var(--ink)!important;font-family:var(--font)!important;font-weight:650!important;letter-spacing:-.6px!important;text-shadow:none!important
}
a,.feed-main a,.barline a:first-child,.source-orbit-detail a{color:var(--ink)!important;text-shadow:none!important;text-decoration:none!important}
a:hover{color:var(--accent)!important;text-decoration:none!important}
.nav{
  position:fixed!important;left:16px!important;top:16px!important;bottom:16px!important;width:240px!important;margin:0!important;padding:24px 14px!important;
  display:flex!important;flex-direction:column!important;gap:20px!important;z-index:40!important;white-space:normal!important
}
.nav-brand{display:flex!important;align-items:center!important;gap:12px!important;padding:0 8px 22px!important;margin:0!important;border-bottom:1px solid rgba(255,255,255,.62)!important}
.brand-mark{width:44px!important;height:44px!important;border-radius:14px!important;background:var(--ink)!important;color:#fff!important;border:1px solid rgba(255,255,255,.82)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.22)!important;display:grid!important;place-items:center!important;font-size:13px!important;font-weight:650!important;letter-spacing:.5px!important;flex:0 0 auto!important}
.nav-brand b,.nav-user b{display:block!important;color:var(--ink)!important;font-size:15px!important;line-height:1.12!important;font-weight:650!important;letter-spacing:-.2px!important}
.nav-brand small,.nav-user small{display:block!important;color:var(--ink-3)!important;font-size:11px!important;margin-top:2px!important;line-height:1.2!important;font-weight:450!important}
.nav-links{display:grid!important;gap:8px!important}
.nav a{display:flex!important;align-items:center!important;gap:12px!important;min-height:48px!important;padding:12px 14px!important;border-radius:var(--r-inner)!important;border:1px solid transparent!important;background:transparent!important;color:var(--ink-2)!important;box-shadow:none!important;font-size:14px!important;font-weight:520!important;line-height:1.12!important;transition:background .15s,color .15s,border-color .15s,transform .05s!important}
.nav a:hover{background:rgba(255,255,255,.42)!important;color:var(--ink)!important;transform:none!important}
.nav a.active{background:rgba(255,255,255,.70)!important;color:var(--accent)!important;font-weight:600!important;border-color:rgba(40,69,122,.30)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.95)!important}
.nav-ico{width:18px!important;height:18px!important;min-width:18px!important;border-radius:0!important;background:transparent!important;border:0!important;box-shadow:none!important;color:var(--ink-3)!important;display:grid!important;place-items:center!important}
.nav-ico svg{width:18px!important;height:18px!important;display:block!important;stroke:currentColor!important;stroke-width:2!important;fill:none!important;stroke-linecap:round!important;stroke-linejoin:round!important}
.nav a.active .nav-ico{color:var(--accent)!important}
.nav-bottom{margin-top:auto!important;display:grid!important;gap:8px!important;padding-top:18px!important;border-top:1px solid rgba(255,255,255,.62)!important}
.nav-user{display:flex!important;align-items:center!important;gap:12px!important;padding:8px 10px!important;border-radius:var(--r-inner)!important;background:rgba(255,255,255,.34)!important;border:1px solid rgba(255,255,255,.54)!important}
.nav-avatar{width:34px!important;height:34px!important;border-radius:50%!important;background:rgba(255,255,255,.62)!important;border:1px solid rgba(255,255,255,.78)!important;color:var(--ink-2)!important;box-shadow:none!important;font-weight:650!important;display:grid!important;place-items:center!important}
.sidebar-toggle{position:fixed!important;left:232px!important;top:34px!important;width:40px!important;height:40px!important;border:1px solid var(--glass-border)!important;border-radius:14px!important;background:var(--glass-strong)!important;color:var(--ink-2)!important;backdrop-filter:var(--blur)!important;-webkit-backdrop-filter:var(--blur)!important;box-shadow:var(--panel-shadow)!important;font-size:0!important;line-height:0!important;z-index:45!important;display:grid!important;place-items:center!important;transition:background .15s,border-color .15s,transform .05s,left .15s!important}
.sidebar-toggle:before{content:""!important;width:18px!important;height:14px!important;display:block!important;margin:0!important;background:transparent!important;border-top:2px solid currentColor!important;border-bottom:2px solid currentColor!important;border-radius:1px!important;box-shadow:none!important}
.sidebar-toggle:after{content:""!important;position:absolute!important;left:50%!important;top:50%!important;width:18px!important;height:2px!important;background:currentColor!important;border-radius:2px!important;transform:translate(-50%,-50%)!important;box-shadow:none!important}
.sidebar-toggle:active,.btn:active,.feed-page-btn:active,.ai-suggestions button:active{transform:scale(.98)!important}
body.sidebar-collapsed .nav{width:72px!important;align-items:center!important;padding:22px 12px!important}
body.sidebar-collapsed .sidebar-toggle{left:64px!important}
body.sidebar-collapsed .nav-brand{justify-content:center!important;padding:44px 0 18px!important;width:100%!important}
body.sidebar-collapsed .nav-label,body.sidebar-collapsed .nav-brand div:not(.brand-mark),body.sidebar-collapsed .nav-user div{display:none!important}
body.sidebar-collapsed .nav-links,body.sidebar-collapsed .nav-bottom{width:100%!important;justify-items:center!important}
body.sidebar-collapsed .nav a,body.sidebar-collapsed .nav-user{width:48px!important;height:48px!important;min-height:48px!important;justify-content:center!important;padding:0!important}
.hero-main,.hero-side,.hero-solo,.wrap .card,.provider,.collect-panel,.filter-bar{padding:24px!important}
.hero-actions{display:flex!important;gap:12px!important;flex-wrap:wrap!important}
.btn,.feed-page-btn,.ai-suggestions button{
  font-family:var(--font)!important;font-size:14px!important;font-weight:600!important;letter-spacing:0!important;border-radius:var(--r-inner)!important;
  padding:11px 20px!important;min-height:44px!important;border:1px solid rgba(255,255,255,.86)!important;background:var(--glass-strong)!important;color:var(--ink)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 1px 2px rgba(60,70,120,.06)!important;text-shadow:none!important;filter:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;gap:8px!important;
  transition:background .15s,border-color .15s,color .15s,transform .05s!important
}
button.btn[type="submit"],form .btn[type="submit"]:not(.light),.login-card .btn,.hero-actions>.btn:not(.light):first-of-type,.collect-panel button.btn[type="submit"]{background:var(--accent)!important;border-color:var(--accent)!important;color:#fff!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.24)!important}
button.btn[type="submit"]:hover,form .btn[type="submit"]:not(.light):hover,.login-card .btn:hover,.hero-actions>.btn:not(.light):first-of-type:hover,.collect-panel button.btn[type="submit"]:hover{background:var(--accent-press)!important;border-color:var(--accent-press)!important;color:#fff!important}
.btn:hover,.feed-page-btn:hover,.ai-suggestions button:hover{background:rgba(255,255,255,.86)!important;border-color:rgba(40,69,122,.25)!important;color:var(--ink)!important}
.input,.select,.textarea,input,select,textarea{
  font-family:var(--font)!important;background:rgba(255,255,255,.62)!important;color:var(--ink)!important;border:1px solid rgba(255,255,255,.86)!important;border-radius:var(--r-inner)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.82)!important;padding:11px 14px!important;font-size:14px!important;line-height:1.35!important;transition:border-color .15s,box-shadow .15s,background .15s!important
}
.input:focus,.select:focus,.textarea:focus,input:focus,select:focus,textarea:focus{outline:3px solid var(--accent-soft)!important;border-color:rgba(40,69,122,.62)!important;background:rgba(255,255,255,.82)!important}
.metric-grid{grid-template-columns:repeat(6,minmax(150px,1fr))!important;gap:16px!important}
.metric{padding:18px 20px!important;min-height:112px!important;display:flex!important;flex-direction:column!important;justify-content:center!important}
.metric .k,.k{color:var(--ink-2)!important;font-size:12px!important;font-weight:650!important;line-height:1.25!important;text-transform:uppercase!important;letter-spacing:.03em!important;margin:0 0 12px!important}
.metric .value,.metric-number,.agent-score,.source-orbit-top b,.signal-card b,.legend-row b,.insight b,.metric-pill b,.query-count,.daily-insight b{
  color:var(--ink)!important;font-family:var(--font)!important;font-weight:650!important;letter-spacing:-1px!important;text-shadow:none!important
}
.metric .value{font-size:34px!important;line-height:1!important}.metric .value-text{font-size:28px!important;line-height:1.08!important;letter-spacing:-.8px!important}
.metric .caption{color:var(--ink-2)!important;font-size:13px!important;font-weight:450!important;line-height:1.34!important;margin-top:10px!important}
.chip,.pill,.status,.metric-state,.agent-tag,.period-summary span,.pr-tag{
  display:inline-flex!important;align-items:center!important;width:auto!important;border-radius:var(--r-pill)!important;border:0!important;box-shadow:none!important;
  padding:4px 9px!important;font-size:11px!important;line-height:1.2!important;font-weight:650!important;letter-spacing:0!important;background:rgba(255,255,255,.52)!important;color:var(--ink-2)!important
}
.positive,.metric-state.good,.risk-low,.on,.feed-badge.pos,.pr-tag.ok{background:rgba(30,158,106,.10)!important;color:var(--pos)!important}
.negative,.metric-state.bad,.risk-high,.off,.feed-badge.neg{background:rgba(192,73,61,.10)!important;color:var(--neg)!important}
.neutral,.feed-badge.neu{background:var(--accent-soft)!important;color:var(--neu)!important}
.metric-state.warn,.risk-mid,.signal.gold,.pr-tag.warn{background:rgba(184,134,11,.12)!important;color:var(--warn)!important}
.period-summary{display:flex!important;gap:8px!important;flex-wrap:wrap!important;margin:12px 0 16px!important}
.period-summary span{background:rgba(255,255,255,.42)!important;color:var(--ink-2)!important}.period-summary b{color:var(--ink)!important}
.track,.source-orbit-track,.tone-stack,.query-progress,.src-track,.mm-track{background:rgba(0,0,0,.06)!important;border-radius:var(--r-pill)!important;box-shadow:none!important;overflow:hidden!important}
.fill,.source-orbit-track i,.query-progress i,.src-fill,.mm-fill{background:var(--accent)!important;border-radius:inherit!important;box-shadow:none!important}
.trend-card,.tone-card,.source-orbit,.insight-board,.agent-focus,.citation-panel{background:var(--glass)!important}
.trend-chart,.chart-shell,.spark-scroll{background:rgba(255,255,255,.40)!important;border:1px solid rgba(255,255,255,.64)!important;border-radius:var(--r-inner)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.72)!important;overflow:hidden!important}
.trend-chart svg,.chart-svg{background:transparent!important;display:block;width:100%!important;height:auto!important}
.trend-grid,.trend-axis{stroke:var(--grid)!important;stroke-width:1!important;stroke-dasharray:none!important}
.trend-y-label,.trend-x-label,.axis-label{fill:var(--ink-3)!important;color:var(--ink-3)!important;font-size:12px!important;font-weight:550!important}
.trend-line{stroke:var(--accent)!important;stroke-width:2.5!important;filter:none!important;fill:none!important}
.trend-area{fill:url(#trendFill)!important}
.trend-dot{fill:var(--accent)!important;stroke:#fff!important;stroke-width:2.5!important;filter:none!important}
.trend-dot-muted{fill:#fff!important;stroke:rgba(40,69,122,.52)!important;stroke-width:2!important}
.trend-panel-bg{fill:rgba(255,255,255,.24)!important}.trend-active-band{fill:rgba(40,69,122,.08)!important}
.trend-tooltip{fill:var(--ink)!important;filter:none!important}.trend-tooltip-title{fill:rgba(255,255,255,.72)!important}.trend-tooltip-value{fill:#fff!important}
.daily-svg .daily-bar{fill:var(--accent)!important}.daily-svg .daily-bar-zero{opacity:.18!important}.daily-svg .daily-grid{stroke:var(--grid)!important}.daily-svg .daily-axis{stroke:rgba(0,0,0,.08)!important}.daily-svg text{fill:var(--ink-3)!important;font-weight:550!important;font-size:12px!important}
.tone-funnel-viz{display:none!important}
.tone-segments{display:flex!important;height:18px!important;border-radius:var(--r-pill)!important;overflow:hidden!important;background:rgba(0,0,0,.06)!important;margin:16px 0 18px!important}
.tone-segments a{display:block!important;height:100%!important;min-width:2px!important}.tone-seg-pos{background:var(--pos)!important}.tone-seg-neu{background:var(--neu)!important}.tone-seg-neg{background:var(--neg)!important}
.tone-funnel-metrics{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:12px!important;border:0!important;margin:0!important}
.tone-stage{background:var(--inner)!important;border:1px solid rgba(255,255,255,.62)!important;border-radius:var(--r-inner)!important;padding:14px!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.72)!important}
.tone-stage b{font-size:28px!important;color:var(--ink)!important}.tone-stage span{color:var(--ink-2)!important}.tone-stage small{color:var(--ink-3)!important}
.tone-stage.positive span,.tone-stage.positive small{color:var(--pos)!important}.tone-stage.negative span,.tone-stage.negative small{color:var(--neg)!important}
.spark{border:0!important;gap:10px!important;padding:16px 16px 34px!important;min-height:210px!important;background:transparent!important}
.spark-col{background:var(--accent)!important;border-radius:6px 6px 0 0!important;box-shadow:none!important}.spark-col b{color:var(--ink)!important}.spark-col span{color:var(--ink-3)!important}
.daily-insights{grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:16px!important}.daily-insight,.daily-top-days{background:var(--inner)!important;border:1px solid rgba(255,255,255,.62)!important;border-radius:var(--r-inner)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.72)!important;min-height:0!important}
.daily-insight span,.daily-insight em,.daily-top-days span{color:var(--ink-2)!important}.daily-insight b,.daily-top-days b{color:var(--ink)!important}
.source-orbit-layout{grid-template-columns:280px minmax(0,1fr)!important;gap:24px!important}
.source-orbit-core,.source-orbit-card,.signal-card,.feed-card,.query-hit,.legend-row,.insight,.metric-pill,.metric-detail,.feed-detail div,.source-orbit-detail,.pr-card{
  background:var(--inner)!important;border:1px solid rgba(255,255,255,.62)!important;border-radius:var(--r-inner)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.72)!important
}
.source-ring{background:rgba(255,255,255,.62)!important;border:10px solid rgba(0,0,0,.06)!important;border-top-color:var(--accent)!important;border-right-color:var(--accent)!important;box-shadow:none!important}
.source-ring span{background:var(--ink)!important;color:#fff!important;border-radius:18px!important;box-shadow:none!important}
.source-orbit-list{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:14px!important}
.source-orbit-card summary{display:grid!important;grid-template-columns:44px minmax(0,1fr)!important;gap:14px!important;padding:16px!important}
.source-orbit-icon{width:44px!important;height:44px!important;border-radius:14px!important;background:rgba(40,69,122,.08)!important;color:var(--accent)!important;border:1px solid rgba(255,255,255,.72)!important;font-size:13px!important;font-weight:700!important;display:grid!important;place-items:center!important}
.source-orbit-top{display:flex!important;justify-content:space-between!important;gap:12px!important;align-items:center!important}.source-orbit-top b{font-size:17px!important;letter-spacing:-.3px!important}.source-orbit-top span{color:var(--accent)!important;font-weight:650!important}
.source-orbit-track{height:8px!important;margin:8px 0 10px!important}.source-orbit-card p{margin:0 0 12px!important}.source-orbit-card small{color:var(--ink-2)!important;font-weight:600!important}
.source-orbit-detail{margin:0 16px 16px!important;padding:14px!important}.source-orbit-detail ul{display:grid!important;gap:8px!important;margin:10px 0 0!important;padding:0!important;list-style:none!important}.source-orbit-detail li{display:flex!important;justify-content:space-between!important;gap:12px!important;color:var(--ink-2)!important}.source-orbit-detail em{font-style:normal!important;color:var(--ink)!important;font-weight:650!important}
.query-performance{padding:24px!important}.query-hit{margin-bottom:10px!important}.query-hit summary{grid-template-columns:44px minmax(0,1fr) auto!important;gap:14px!important;padding:16px!important}
.query-rank{background:rgba(40,69,122,.08)!important;color:var(--accent)!important;border-radius:12px!important;font-weight:650!important}.query-title{color:var(--ink)!important;font-weight:650!important;letter-spacing:-.3px!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important}.query-count{font-size:24px!important}
.query-hit-detail{padding:0 16px 16px 74px!important;color:var(--ink-2)!important}.query-hit-detail a,.daily-top-days nav a{background:rgba(255,255,255,.58)!important;border:1px solid rgba(255,255,255,.72)!important;color:var(--accent)!important;box-shadow:none!important;border-radius:var(--r-pill)!important}
.query-progress{height:8px!important}
table,.citation-table{border-collapse:separate!important;border-spacing:0!important;background:var(--inner)!important;border:1px solid rgba(255,255,255,.62)!important;border-radius:var(--r-inner)!important;overflow:hidden!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.72)!important}
th{background:rgba(255,255,255,.34)!important;color:var(--ink-3)!important;padding:14px 16px!important;font-size:11px!important;font-weight:650!important;letter-spacing:.06em!important;text-transform:uppercase!important;border:0!important}
td{background:transparent!important;color:var(--ink-2)!important;border-top:1px solid rgba(0,0,0,.05)!important;padding:14px 16px!important;font-size:14px!important;vertical-align:top!important}
tr:hover td{background:rgba(255,255,255,.24)!important}
.feed-card{margin-bottom:12px!important}.feed-card summary{grid-template-columns:140px minmax(0,1fr) minmax(140px,180px) 100px!important;padding:16px!important;background:var(--inner)!important}
.feed-card[open] summary,.feed-detail{background:rgba(255,255,255,.28)!important;border-color:rgba(0,0,0,.05)!important}.feed-detail{grid-template-columns:repeat(4,minmax(0,1fr))!important;padding:16px!important;gap:12px!important}
.feed-main a{color:var(--ink)!important;font-size:16px!important;font-weight:650!important;letter-spacing:-.2px!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}
.feed-main span{color:var(--ink-2)!important;font-size:14px!important;display:-webkit-box!important;-webkit-line-clamp:2!important;-webkit-box-orient:vertical!important;overflow:hidden!important}.feed-source,.feed-more{color:var(--ink-2)!important;font-weight:600!important}
.feed-more:hover{color:var(--accent)!important}
.feed-page-btn{border-radius:var(--r-pill)!important}.feed-page-btn.disabled{opacity:.45!important}
.metric-list,.pr-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:16px!important}.metric-pill summary,.pr-card{padding:16px!important;min-height:0!important}.metric-pill summary:after{color:var(--accent)!important}
.coverage-note,.note{background:rgba(255,255,255,.42)!important;border:1px solid rgba(255,255,255,.64)!important;border-left:4px solid var(--accent)!important;border-radius:var(--r-inner)!important;color:var(--ink-2)!important;padding:16px!important}
.help-dot,.gear{background:var(--glass-strong)!important;color:var(--ink-2)!important;border:1px solid var(--glass-border)!important;border-radius:14px!important;box-shadow:var(--panel-shadow)!important}
.widget-settings{background:var(--glass-strong)!important;right:0!important;min-width:320px!important;z-index:20!important}
.sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
.gear svg{display:block!important;width:18px!important;height:18px!important}
.tone-segments a{min-width:0!important}
.spark-scroll{min-height:0!important}
.daily-svg{width:100%!important;height:276px!important;display:block!important}
.with-sidebar .workspace-hero,.with-sidebar .workspace-hero-single,.with-sidebar .metric,.with-sidebar .card,.with-sidebar .collect-panel,.with-sidebar .filter-bar,.with-sidebar .hero-main,.with-sidebar .hero-side,.with-sidebar .hero-solo,.with-sidebar .provider,.with-sidebar .project-card,.with-sidebar .trend-card,.with-sidebar .tone-card,.with-sidebar .source-orbit,.with-sidebar .insight-board,.with-sidebar .agent-focus,.with-sidebar .ai-chat-panel,.with-sidebar .ai-answer,.with-sidebar .agent-card,.with-sidebar .widget-settings{
  background:var(--glass)!important;background-image:none!important;border:1px solid var(--glass-border)!important;border-radius:var(--r-card)!important;
  box-shadow:var(--panel-shadow)!important;backdrop-filter:var(--blur)!important;-webkit-backdrop-filter:var(--blur)!important
}
.with-sidebar .feed-card,.with-sidebar .source-orbit-card,.with-sidebar .signal-card,.with-sidebar .source-orbit-core,.with-sidebar .query-hit,.with-sidebar .daily-insight,.with-sidebar .daily-top-days,.with-sidebar .legend-row,.with-sidebar .insight,.with-sidebar .metric-pill,.with-sidebar .metric-detail,.with-sidebar .feed-detail div,.with-sidebar .source-orbit-detail,.with-sidebar .pr-card{
  background:var(--inner)!important;background-image:none!important;border:1px solid rgba(255,255,255,.62)!important;border-radius:var(--r-inner)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.72)!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important
}
.with-sidebar .nav{background:var(--glass)!important;background-image:none!important;border:1px solid var(--glass-border)!important;border-radius:var(--r-card)!important;box-shadow:var(--panel-shadow)!important;backdrop-filter:var(--blur)!important;-webkit-backdrop-filter:var(--blur)!important}
.with-sidebar .nav a.active,.with-sidebar.sidebar-collapsed .nav a.active{background:rgba(255,255,255,.70)!important;background-image:none!important;color:var(--accent)!important;border:1px solid rgba(40,69,122,.30)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.95)!important}
.with-sidebar .nav a.active .nav-ico,.with-sidebar.sidebar-collapsed .nav a.active .nav-ico,.with-sidebar .nav-ico{background:transparent!important;background-image:none!important;border:0!important;box-shadow:none!important}
.with-sidebar .nav a.active .nav-ico,.with-sidebar.sidebar-collapsed .nav a.active .nav-ico{color:var(--accent)!important}
.with-sidebar .btn:not(.light),.with-sidebar .hero-actions .btn:not(.light),.with-sidebar button.btn[type="submit"]{background:var(--accent)!important;background-image:none!important;color:#fff!important;border-color:var(--accent)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.24)!important}
.with-sidebar .btn:not(.light):hover,.with-sidebar .hero-actions .btn:not(.light):hover,.with-sidebar button.btn[type="submit"]:hover{background:var(--accent-press)!important;background-image:none!important;border-color:var(--accent-press)!important;color:#fff!important}
.with-sidebar .btn.light,.with-sidebar .hero-actions .btn.light,.with-sidebar .feed-page-btn{background:var(--glass-strong)!important;background-image:none!important;color:var(--ink)!important;border-color:var(--glass-border)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 1px 2px rgba(60,70,120,.06)!important}
.with-sidebar .input,.with-sidebar .select,.with-sidebar .textarea{background:rgba(255,255,255,.62)!important;background-image:none!important;color:var(--ink)!important;border-color:rgba(255,255,255,.86)!important}
.with-sidebar .source-ring{background:rgba(255,255,255,.62)!important;background-image:none!important;border:10px solid rgba(0,0,0,.06)!important;border-top-color:var(--accent)!important;border-right-color:var(--accent)!important;box-shadow:none!important}
.with-sidebar .source-ring span{background:var(--ink)!important;background-image:none!important;color:#fff!important;box-shadow:none!important}
.with-sidebar .source-orbit-track i,.with-sidebar .query-progress i,.with-sidebar .spark-col,.with-sidebar .fill{background:var(--accent)!important;background-image:none!important;box-shadow:none!important}
.with-sidebar th{background:rgba(255,255,255,.34)!important;background-image:none!important;color:var(--ink-3)!important}
.with-sidebar .collect-panel .source-picker-head,.with-sidebar .collect-panel .bar{
  background:var(--inner)!important;background-image:none!important;border:1px solid rgba(255,255,255,.62)!important;border-radius:var(--r-inner)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.72)!important;padding:16px!important;margin:0 0 12px!important
}
.with-sidebar .collect-panel .bar{display:flex!important;gap:12px!important;align-items:center!important;flex-wrap:wrap!important}
.with-sidebar .collect-panel label.muted{color:var(--ink-2)!important}
.sidebar-toggle:before,.sidebar-toggle:after{display:none!important;content:none!important}
.sidebar-toggle svg{display:block!important;width:20px!important;height:20px!important;fill:none!important;stroke:var(--ink-2)!important;stroke-width:2!important;stroke-linecap:round!important}
.with-sidebar .project-open-btn{
  background:var(--accent-soft)!important;background-image:none!important;color:var(--accent)!important;
  border:1px solid rgba(40,69,122,.32)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.82)!important
}
.with-sidebar .project-open-btn:hover{background:rgba(40,69,122,.16)!important;color:var(--accent-press)!important;border-color:rgba(40,69,122,.48)!important}
.project-picker{display:flex!important;gap:12px!important;align-items:flex-end!important;flex-wrap:wrap!important}
.project-select-wrap{display:grid!important;gap:6px!important;min-width:260px!important;color:var(--ink-2)!important;font-size:12px!important;font-weight:600!important}
.project-select-wrap .select{width:100%!important;min-width:260px!important}
.project-picker-single{align-items:center!important;padding:6px!important;border:1px solid rgba(255,255,255,.68)!important;border-radius:var(--r-inner)!important;background:rgba(255,255,255,.38)!important}
.project-current{display:grid!important;gap:2px!important;min-width:220px!important;padding:4px 10px!important}
.project-current span{color:var(--ink-3)!important;font-size:11px!important;font-weight:650!important;text-transform:uppercase!important;letter-spacing:.04em!important}
.project-current b{color:var(--ink)!important;font-size:15px!important;font-weight:650!important;letter-spacing:-.2px!important}
.with-sidebar .collect-panel{padding:16px!important}
.with-sidebar .collect-panel .source-picker-head{margin:0 0 12px!important}
.collect-body{display:grid!important;gap:12px!important}
.collect-controls{display:grid!important;grid-template-columns:auto minmax(180px,240px) minmax(180px,240px) 1fr!important;gap:12px!important;align-items:end!important}
.collect-field{display:grid!important;gap:6px!important;color:var(--ink-2)!important;font-size:12px!important;font-weight:600!important}
.collect-field .select{width:100%!important;min-width:0!important}
.collect-options{display:flex!important;gap:24px!important;align-items:center!important;flex-wrap:wrap!important;padding:4px 2px!important}
.check-control{display:inline-flex!important;align-items:center!important;gap:9px!important;color:var(--ink-2)!important;font-size:13px!important;font-weight:520!important;line-height:1.3!important;cursor:pointer!important}
.check-control input{appearance:none!important;-webkit-appearance:none!important;width:18px!important;height:18px!important;min-width:18px!important;margin:0!important;padding:0!important;border:1px solid rgba(40,69,122,.30)!important;border-radius:5px!important;background:rgba(255,255,255,.72)!important;display:grid!important;place-items:center!important}
.check-control input:checked{background:var(--accent)!important;border-color:var(--accent)!important}
.check-control input:checked:after{content:""!important;width:8px!important;height:4px!important;border-left:2px solid white!important;border-bottom:2px solid white!important;transform:rotate(-45deg) translateY(-1px)!important}
.collect-status{display:flex!important;align-items:center!important;gap:12px!important;min-height:48px!important;padding:12px 14px!important;border-radius:var(--r-inner)!important;background:rgba(255,255,255,.44)!important;border:1px solid rgba(255,255,255,.68)!important;color:var(--ink-2)!important}
.collect-status-icon{width:12px!important;height:12px!important;flex:0 0 12px!important;border-radius:50%!important;background:var(--ink-3)!important}
.collect-status div{display:grid!important;gap:2px!important}.collect-status b{color:var(--ink)!important;font-size:14px!important}.collect-status span:last-child{font-size:12px!important}
.collect-status.running .collect-status-icon{background:transparent!important;border:2px solid rgba(40,69,122,.22)!important;border-top-color:var(--accent)!important;animation:collect-spin .8s linear infinite!important}
.collect-status.success .collect-status-icon{background:var(--pos)!important}.collect-status.error .collect-status-icon{background:var(--neg)!important}
.collect-submit:disabled{opacity:.72!important;cursor:wait!important}
@keyframes collect-spin{to{transform:rotate(360deg)}}
.login-card h1{color:var(--ink)!important}.login-card p{color:var(--ink-2)!important}
pre.card{background:rgba(255,255,255,.62)!important}
@media(max-width:1280px){.metric-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}.metric-list,.pr-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}.source-orbit-layout{grid-template-columns:1fr!important}.source-orbit-list{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
@media(max-width:900px){
  body.with-sidebar,body.with-sidebar.sidebar-collapsed{padding-left:0!important}
  .nav{position:sticky!important;left:auto!important;top:0!important;bottom:auto!important;width:auto!important;margin:12px!important;padding:10px!important;display:block!important;overflow-x:auto!important;border-radius:var(--r-card)!important}
  .nav-brand,.nav-bottom{display:none!important}.nav-links{display:flex!important;gap:8px!important}.nav a{display:inline-flex!important;white-space:nowrap!important}.sidebar-toggle{display:none!important}
  .wrap,.with-sidebar .wrap{padding:16px!important}.top,.with-sidebar .top{padding:20px 16px 8px!important}.metric-grid,.grid,.layout,.charts,.settings,.split,.viz-grid,.insights,.metric-list,.legend,.source-checks,.admin-grid,.project-switcher,.quick-project-form,.agent-hero,.agent-grid,.agent-evidence,.workspace-hero,.signal-grid,.ai-chat,.daily-insights,.source-orbit-list,.pr-grid{grid-template-columns:1fr!important}
  .feed-card summary,.feed-detail{grid-template-columns:1fr!important}.feed-detail-wide{grid-column:auto!important}
  .collect-controls{grid-template-columns:1fr!important}.collect-options{display:grid!important;gap:12px!important}
  .project-picker,.project-picker-single{display:grid!important;grid-template-columns:1fr!important;width:100%!important;align-items:stretch!important}
  .project-select-wrap,.project-select-wrap .select,.project-current{min-width:0!important;width:100%!important;box-sizing:border-box!important}
  .project-picker .project-open-btn{width:100%!important;box-sizing:border-box!important;text-align:center!important}
}

/* ── Settings page polish ─────────────────────────────────────────────── */
.settings-overview{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(220px,100%),1fr));gap:14px;margin:0 0 20px}
.settings-overview .tile{background:white;border:1px solid #dce3e8;border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:4px;min-width:0}
.settings-overview .tile .tile-label{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.03em;color:#8194a0}
.settings-overview .tile .tile-value{font-size:22px;font-weight:900;color:#173a47;line-height:1.1}
.settings-overview .tile .tile-sub{font-size:12px;color:#667782}
.settings-overview .tile.accent{border-left:3px solid #147487}
.settings-overview .tile.warn{border-left:3px solid #b8860b}
/* Поля провайдеров тянутся на всю ширину — без инлайн-стилей в разметке */
.provider .input,.provider .select,.provider .textarea{width:100%;box-sizing:border-box}
.provider .input.input-narrow{width:160px;max-width:100%}
.provider .select.input-narrow{width:240px;max-width:100%}
/* Поле токена с кнопкой показа */
.secret-field{position:relative;display:flex;align-items:stretch;gap:0}
.secret-field .input{padding-right:44px}
.reveal-btn{position:absolute;right:6px;top:50%;transform:translateY(-50%);border:0;background:transparent;cursor:pointer;font-size:16px;line-height:1;padding:6px;border-radius:6px;color:#5f8b9d}
.reveal-btn:hover{background:#eef4f6;color:#147487}
/* Сворачиваемая подробная инструкция */
.hint-details{margin:6px 0 0;border-top:1px solid #eef2f4;padding-top:8px}
.hint-details summary{cursor:pointer;display:inline-flex;align-items:center;gap:8px;color:#1f6f85;font-weight:800;font-size:13px;list-style:none}
.hint-details summary::-webkit-details-marker{display:none}
.hint-details summary:before{content:"＋";display:inline-grid;place-items:center;width:18px;height:18px;border-radius:50%;background:#e9f1f4;color:#173a47;font-size:13px}
.hint-details[open] summary:before{content:"－"}
.hint-details .hint{margin-top:8px}
/* Подсветка активного пункта боковой навигации (scroll-spy) */
.side-nav a.active{background:#e9f1f4;color:#0f5468;font-weight:800;border-radius:8px}
/* Sticky-панель сохранения */
.settings-savebar{position:sticky;bottom:0;margin-top:18px;background:rgba(255,255,255,.92);backdrop-filter:blur(6px);border-top:1px solid #dce3e8;padding:14px 0;display:flex;gap:12px;align-items:center;z-index:5}
@media(max-width:760px){.settings-savebar{flex-wrap:wrap}}

/* Более чёткие границы карточек и панелей (читаемее на светлом фоне) */
.with-sidebar .workspace-hero,.with-sidebar .workspace-hero-single,.with-sidebar .metric,.with-sidebar .card,
.with-sidebar .collect-panel,.with-sidebar .filter-bar,.with-sidebar .hero-main,.with-sidebar .hero-side,
.with-sidebar .hero-solo,.with-sidebar .provider,.with-sidebar .project-card,.with-sidebar .trend-card,
.with-sidebar .tone-card,.with-sidebar .source-orbit,.with-sidebar .ai-chat-panel,.with-sidebar .ai-answer,
.with-sidebar .agent-card,.with-sidebar table,.with-sidebar details.provider{
  border:1.5px solid rgba(22,34,58,.14)!important;
}
.with-sidebar .metric:hover{border-color:rgba(22,34,58,.22)!important}
/* Операционный контекст в шапке дашборда */
.hero-meta{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 16px}
/* Дата публикации в свёрнутой карточке ленты */
.feed-date{color:var(--ink-3,#8a8a90);font-size:12px;font-weight:600;white-space:nowrap;margin-right:8px}

/* Контролы шапки дашборда — единый размер, выравнивание и чёткие границы */
.hero-actions{align-items:flex-end!important}                 /* не растягивать кнопки по высоте селектора */
.project-picker{align-items:flex-end!important}
.with-sidebar .hero-actions .btn,.with-sidebar .hero-actions .project-open-btn{
  min-height:46px!important;height:46px!important;padding:0 22px!important;font-size:15px!important;
}
/* Селектор проекта: всегда видимая рамка, ровно та же высота, что у кнопок */
.with-sidebar .project-select-wrap .select,.with-sidebar .hero-actions .select{
  min-height:46px!important;height:46px!important;background:#fff!important;
  border:1.5px solid rgba(22,34,58,.20)!important;border-radius:var(--r-inner)!important;
  padding:0 16px!important;font-size:15px!important;font-weight:600!important;color:var(--ink)!important;
}
.with-sidebar .project-select-wrap .select:hover{border-color:rgba(22,34,58,.34)!important}
.with-sidebar .project-select-wrap .select:focus{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(40,69,122,.14)!important;outline:none!important}
/* Светлые/вторичные кнопки — видимая рамка, чтобы читались как кнопки */
.with-sidebar .btn.light,.with-sidebar .hero-actions .btn.light,.with-sidebar .btn.secondary,.with-sidebar .feed-page-btn{
  border:1.5px solid rgba(22,34,58,.18)!important;background:#fff!important;color:var(--ink)!important;
}
.with-sidebar .btn.light:hover,.with-sidebar .hero-actions .btn.light:hover{border-color:rgba(22,34,58,.34)!important;background:#fff!important}

/* Значения метрик: число — крупно; текстовая фраза — компактно и с переносом */
.with-sidebar .metric .value-text{font-size:20px!important;line-height:1.18!important;letter-spacing:0!important;max-width:none!important;overflow-wrap:anywhere!important;word-break:normal!important}
.with-sidebar .metric .value-long{font-size:16px!important;line-height:1.2!important;font-weight:760!important}

/* Подсказки «?» в панели сбора не должны обрезаться — разрешаем выход за панель,
   а верхние углы шапки скругляем, чтобы фон не торчал за рамкой панели */
.with-sidebar .collect-panel{overflow:visible!important}
.with-sidebar .collect-panel .source-picker-head{border-top-left-radius:var(--r-card)!important;border-top-right-radius:var(--r-card)!important}
.help-dot:hover:after{z-index:60!important}
"""

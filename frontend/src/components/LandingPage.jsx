import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ShieldCheck, Cpu, FileText, GitBranch, Lock, Eye,
  ArrowRight, ChevronDown, CheckCircle2, Zap, Database,
  Network, Server, AlertTriangle, BarChart3, FileCode2,
  Bot, Layers, Terminal, Search, Shield, Activity
} from 'lucide-react';

/* ─── Animated Counter ─────────────────────────────────────────── */
function useCounter(target, duration = 1800, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    let t0 = null;
    const tick = (ts) => {
      if (!t0) t0 = ts;
      const p = Math.min((ts - t0) / duration, 1);
      setCount(Math.floor((1 - Math.pow(1 - p, 3)) * target));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [target, duration, start]);
  return count;
}

function useInView(threshold = 0.25) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setInView(true); obs.disconnect(); } },
      { threshold }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, inView];
}

/* ─── Stat item ─────────────────────────────────────────────────── */
function StatItem({ value, suffix, label, inView }) {
  const count = useCounter(value, 1800, inView);
  return (
    <div className="lp-stat-item">
      <span className="lp-stat-num">{count}{suffix}</span>
      <span className="lp-stat-lbl">{label}</span>
    </div>
  );
}

/* ─── SVG Flowchart ─────────────────────────────────────────────── */
function Flowchart({ activeStep, onStepClick }) {
  const steps = [
    { id: 0, x: 380, y: 30, w: 180, h: 56, label: 'Query / Upload', sub: 'Text · PDF · Image', icon: Search, shape: 'rounded' },
    { id: 1, x: 380, y: 140, w: 180, h: 56, label: 'Task Classifier', sub: 'Keyword + Embedding', icon: GitBranch, shape: 'rounded' },
    { id: 2, x: 100, y: 260, w: 180, h: 56, label: 'RAG Retrieval', sub: 'BM25 + Dense · ChromaDB', icon: Database, shape: 'rounded' },
    { id: 3, x: 660, y: 260, w: 180, h: 56, label: 'Model Router', sub: 'Code · Vision · Text', icon: Layers, shape: 'rounded' },
    { id: 4, x: 380, y: 380, w: 180, h: 68, label: 'Agentic Planner', sub: 'LangGraph · Multi-step', icon: Bot, shape: 'diamond' },
    { id: 5, x: 380, y: 510, w: 180, h: 56, label: 'Docker Sandbox', sub: 'Isolated Execution', icon: Terminal, shape: 'rounded' },
    { id: 6, x: 380, y: 622, w: 180, h: 68, label: 'Risk Engine', sub: '4-Stage Validation', icon: Shield, shape: 'diamond' },
    { id: 7, x: 100, y: 754, w: 180, h: 56, label: 'HITL Approval', sub: 'Human reviews output', icon: Eye, shape: 'rounded' },
    { id: 8, x: 660, y: 754, w: 180, h: 56, label: 'Auto-Retry', sub: 'Agent self-corrects', icon: Activity, shape: 'rounded' },
    { id: 9, x: 380, y: 870, w: 180, h: 56, label: 'Cited Deliverable', sub: '.docx · .pptx · .xlsx', icon: FileText, shape: 'rounded' },
  ];

  const edges = [
    { from: 0, to: 1, type: 'straight' },
    { from: 1, to: 2, type: 'branch-left', label: 'RAG Task' },
    { from: 1, to: 3, type: 'branch-right', label: 'LLM Task' },
    { from: 2, to: 4, type: 'merge-left' },
    { from: 3, to: 4, type: 'merge-right' },
    { from: 4, to: 5, type: 'straight' },
    { from: 5, to: 6, type: 'straight' },
    { from: 6, to: 7, type: 'branch-left', label: 'Critical' },
    { from: 6, to: 8, type: 'branch-right', label: 'Failed' },
    { from: 7, to: 9, type: 'merge-left' },
    { from: 8, to: 4, type: 'loop-right' },
    { from: 6, to: 9, type: 'pass', label: 'Pass ✓' },
  ];

  const getNode = (id) => steps.find(s => s.id === id);
  const cx = (n) => n.x + n.w / 2;
  const cy = (n) => n.y + n.h / 2;
  const OCHRE = '#BD7035'; const YELLOW = '#F3B250'; const COFFEE = '#512D18';
  const GRAY = '#F0F0F0'; const GRAY_DIM = '#5A5A5A'; const BLACK = '#0E0C0E';

  return (
    <svg viewBox="0 0 940 980" className="lp-flow-svg" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill={OCHRE} />
        </marker>
        <marker id="arr-y" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill={YELLOW} />
        </marker>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <linearGradient id="card-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1e1418" />
          <stop offset="100%" stopColor="#130f12" />
        </linearGradient>
        <linearGradient id="card-active" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#2a1c0e" />
          <stop offset="100%" stopColor="#1a1208" />
        </linearGradient>
        <linearGradient id="line-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={OCHRE} />
          <stop offset="100%" stopColor={COFFEE} />
        </linearGradient>
      </defs>

      {/* ── Edge Lines ── */}
      {/* 0→1 */}
      <line x1={cx(steps[0])} y1={steps[0].y + steps[0].h} x2={cx(steps[1])} y2={steps[1].y} stroke="url(#line-grad)" strokeWidth="1.5" markerEnd="url(#arr)" />
      {/* 1→2 branch left */}
      <path d={`M${cx(steps[1])},${steps[1].y + steps[1].h} L${cx(steps[1])},${steps[1].y + steps[1].h + 28} L${cx(steps[2])},${steps[1].y + steps[1].h + 28} L${cx(steps[2])},${steps[2].y}`} stroke={OCHRE} strokeWidth="1.5" fill="none" strokeDasharray="5,4" markerEnd="url(#arr)" />
      <text x={cx(steps[1]) - 80} y={steps[1].y + steps[1].h + 22} fill={OCHRE} fontSize="9" fontWeight="700">RAG Task</text>
      {/* 1→3 branch right */}
      <path d={`M${cx(steps[1])},${steps[1].y + steps[1].h} L${cx(steps[1])},${steps[1].y + steps[1].h + 28} L${cx(steps[3])},${steps[1].y + steps[1].h + 28} L${cx(steps[3])},${steps[3].y}`} stroke={OCHRE} strokeWidth="1.5" fill="none" strokeDasharray="5,4" markerEnd="url(#arr)" />
      <text x={cx(steps[3]) - 18} y={steps[1].y + steps[1].h + 22} fill={OCHRE} fontSize="9" fontWeight="700">LLM Task</text>
      {/* 2→4 merge left */}
      <path d={`M${cx(steps[2])},${steps[2].y + steps[2].h} L${cx(steps[2])},${steps[2].y + steps[2].h + 30} L${cx(steps[4])},${steps[2].y + steps[2].h + 30} L${cx(steps[4])},${steps[4].y}`} stroke={COFFEE} strokeWidth="1.5" fill="none" markerEnd="url(#arr)" />
      {/* 3→4 merge right */}
      <path d={`M${cx(steps[3])},${steps[3].y + steps[3].h} L${cx(steps[3])},${steps[3].y + steps[3].h + 30} L${cx(steps[4])},${steps[3].y + steps[3].h + 30} L${cx(steps[4])},${steps[4].y}`} stroke={COFFEE} strokeWidth="1.5" fill="none" markerEnd="url(#arr)" />
      {/* 4→5 */}
      <line x1={cx(steps[4])} y1={steps[4].y + steps[4].h} x2={cx(steps[5])} y2={steps[5].y} stroke="url(#line-grad)" strokeWidth="1.5" markerEnd="url(#arr)" />
      {/* 5→6 */}
      <line x1={cx(steps[5])} y1={steps[5].y + steps[5].h} x2={cx(steps[6])} y2={steps[6].y} stroke="url(#line-grad)" strokeWidth="1.5" markerEnd="url(#arr)" />
      {/* 6→7 HITL (pass critical) */}
      <path d={`M${steps[6].x},${cy(steps[6])} L${steps[6].x - 40},${cy(steps[6])} L${steps[6].x - 40},${cy(steps[7])} L${steps[7].x + steps[7].w},${cy(steps[7])}`} stroke={YELLOW} strokeWidth="1.5" fill="none" strokeDasharray="4,3" markerEnd="url(#arr-y)" />
      <text x={steps[6].x - 90} y={cy(steps[6]) - 8} fill={YELLOW} fontSize="9" fontWeight="700">Critical</text>
      {/* 6→8 retry */}
      <path d={`M${steps[6].x + steps[6].w},${cy(steps[6])} L${steps[6].x + steps[6].w + 40},${cy(steps[6])} L${steps[6].x + steps[6].w + 40},${cy(steps[8])} L${steps[8].x},${cy(steps[8])}`} stroke="#fc6464" strokeWidth="1.5" fill="none" strokeDasharray="4,3" markerEnd="url(#arr)" />
      <text x={steps[6].x + steps[6].w + 6} y={cy(steps[6]) - 8} fill="#fc6464" fontSize="9" fontWeight="700">Failed</text>
      {/* 8→4 loop back */}
      <path d={`M${cx(steps[8])},${steps[8].y + steps[8].h} L${cx(steps[8])},${steps[8].y + steps[8].h + 30} L870,${steps[8].y + steps[8].h + 30} L870,${cy(steps[4])} L${steps[4].x + steps[4].w},${cy(steps[4])}`} stroke="#fc6464" strokeWidth="1.2" fill="none" strokeDasharray="3,4" markerEnd="url(#arr)" />
      {/* 6→9 pass */}
      <line x1={cx(steps[6])} y1={steps[6].y + steps[6].h} x2={cx(steps[9])} y2={steps[9].y} stroke={YELLOW} strokeWidth="2" markerEnd="url(#arr-y)" />
      <text x={cx(steps[6]) + 8} y={(steps[6].y + steps[6].h + steps[9].y) / 2} fill={YELLOW} fontSize="10" fontWeight="800">Pass ✓</text>
      {/* 7→9 */}
      <path d={`M${cx(steps[7])},${steps[7].y + steps[7].h} L${cx(steps[7])},${steps[7].y + steps[7].h + 28} L${cx(steps[9])},${steps[7].y + steps[7].h + 28} L${cx(steps[9])},${steps[9].y}`} stroke={YELLOW} strokeWidth="1.5" fill="none" markerEnd="url(#arr-y)" />

      {/* ── Nodes ── */}
      {steps.map((s) => {
        const active = activeStep === s.id;
        const Icon = s.icon;
        if (s.shape === 'diamond') {
          return (
            <g key={s.id} style={{ cursor: 'pointer' }} onClick={() => onStepClick(s.id)}>
              <polygon
                points={`${cx(s)},${s.y} ${s.x + s.w},${cy(s)} ${cx(s)},${s.y + s.h} ${s.x},${cy(s)}`}
                fill={active ? 'url(#card-active)' : 'url(#card-grad)'}
                stroke={active ? YELLOW : OCHRE}
                strokeWidth={active ? 2 : 1.5}
                filter={active ? 'url(#glow)' : undefined}
              />
              <text x={cx(s)} y={cy(s) - 8} textAnchor="middle" fill={active ? YELLOW : GRAY} fontSize="11" fontWeight="800">{s.label}</text>
              <text x={cx(s)} y={cy(s) + 8} textAnchor="middle" fill={GRAY_DIM} fontSize="9">{s.sub}</text>
              <circle cx={s.x + 6} cy={s.y + 6} r="9" fill={YELLOW} />
              <text x={s.x + 6} y={s.y + 10} textAnchor="middle" fill={BLACK} fontSize="9" fontWeight="900">{s.id + 1}</text>
            </g>
          );
        }
        return (
          <g key={s.id} style={{ cursor: 'pointer' }} onClick={() => onStepClick(s.id)}>
            <rect x={s.x} y={s.y} width={s.w} height={s.h} rx="12"
              fill={active ? 'url(#card-active)' : 'url(#card-grad)'}
              stroke={active ? YELLOW : 'rgba(189,112,53,0.35)'}
              strokeWidth={active ? 2 : 1.2}
              filter={active ? 'url(#glow)' : undefined}
            />
            <text x={cx(s)} y={cy(s) - 7} textAnchor="middle" fill={active ? YELLOW : GRAY} fontSize="11" fontWeight="800">{s.label}</text>
            <text x={cx(s)} y={cy(s) + 8} textAnchor="middle" fill={GRAY_DIM} fontSize="9">{s.sub}</text>
            <circle cx={s.x + 10} cy={s.y + 10} r="9" fill={active ? YELLOW : COFFEE} />
            <text x={s.x + 10} y={s.y + 14} textAnchor="middle" fill={active ? BLACK : GRAY} fontSize="9" fontWeight="900">{s.id + 1}</text>
          </g>
        );
      })}

      {/* Legend */}
      <rect x="20" y="920" width="900" height="1" fill="rgba(189,112,53,0.15)" />
      <circle cx="40" cy="950" r="4" fill={YELLOW} />
      <text x="52" y="954" fill={GRAY_DIM} fontSize="9">Active / Pass path</text>
      <line x1="150" y1="950" x2="175" y2="950" stroke={OCHRE} strokeWidth="1.5" strokeDasharray="4,3" />
      <text x="182" y="954" fill={GRAY_DIM} fontSize="9">Branch path</text>
      <line x1="270" y1="950" x2="295" y2="950" stroke="#fc6464" strokeWidth="1.2" strokeDasharray="3,4" />
      <text x="302" y="954" fill={GRAY_DIM} fontSize="9">Retry / loop</text>
    </svg>
  );
}

/* ─── Main ──────────────────────────────────────────────────────── */
export default function LandingPage({ onEnter }) {
  const [scrolled, setScrolled] = useState(false);
  const [activeFlowStep, setActiveFlowStep] = useState(0);
  const [statsRef, statsInView] = useInView(0.3);

  const heroBgRef = useRef(null);

  useEffect(() => {
    const h = () => {
      const y = window.scrollY;
      setScrolled(y > 30);
      // Parallax — move bg at 40% of scroll speed
      if (heroBgRef.current) {
        heroBgRef.current.style.transform = `translateY(${y * 0.4}px)`;
      }
    };
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, []);

  useEffect(() => {
    const t = setInterval(() => setActiveFlowStep(s => (s + 1) % 10), 1800);
    return () => clearInterval(t);
  }, []);

  const features = [
    { cls: 'c1', icon: ShieldCheck, title: 'Zero External API Calls', desc: 'Provably air-gapped. Real-time network egress monitor confirms zero outbound packets — sovereignty is measurable, not just claimed.', badge: 'SOVEREIGN' },
    { cls: 'c2', icon: Bot, title: 'Agentic Plan → Execute → Verify', desc: 'LangGraph orchestrates a full reasoning loop: the agent plans, selects tools (RAG, OCR, Sandbox, Calculator), executes, then re-reads its own output to catch errors before delivery.', badge: 'CORE ENGINE' },
    { cls: 'c3', icon: FileText, title: 'Citation-Level RAG', desc: 'Hybrid BM25 + dense retrieval. Every answer is linked to the exact document and page number.', badge: 'GROUNDED' },
    { cls: 'c4', icon: Eye, title: 'Multimodal Vision', desc: 'Qwen2-VL + Surya OCR parses P&IDs, scans, handwritten logs — all offline.', badge: 'VISION' },
    { cls: 'c5', icon: Layers, title: 'Industrial Risk Engine', desc: '4-stage safety check. HITL gates block unsafe actions from reaching production.', badge: 'SAFETY' },
    { cls: 'c6', icon: GitBranch, title: 'Intelligent Model Routing', desc: 'A hybrid keyword + embedding classifier picks the optimal local model per task: Qwen-Coder for code, Qwen-VL for vision, Qwen2.5 for text reasoning — automatically, every time.', badge: 'ROUTING' },
    { cls: 'c7', icon: Lock, title: 'RBAC & Cryptographic Audit', desc: 'Every query, export, and approval event is signed and written to an immutable audit ledger.', badge: 'COMPLIANCE' },
    { cls: 'c8', icon: FileCode2, title: 'Downloadable Deliverables — not just chat', desc: 'Agent produces .docx, .pptx, .xlsx, and .py files with inline page citations. Full industrial knowledge work, not just a chatbot reply.', badge: 'OUTPUT', wide: true },
  ];

  const techStack = [
    { name: 'React + Vite', category: 'Frontend' },
    { name: 'FastAPI', category: 'Backend' },
    { name: 'LangGraph', category: 'Agent' },
    { name: 'ChromaDB', category: 'Vector DB' },
    { name: 'Ollama', category: 'LLM Runner' },
    { name: 'Qwen2.5', category: 'Language' },
    { name: 'Qwen2-VL', category: 'Vision' },
    { name: 'Surya OCR', category: 'OCR' },
    { name: 'Docker', category: 'Sandbox' },
    { name: 'python-docx', category: 'Output' },
    { name: 'structlog', category: 'Logging' },
    { name: 'BM25 + SBERT', category: 'Retrieval' },
  ];

  const flowStepInfo = [
    { title: 'Query & Upload', desc: 'User submits a text prompt or uploads a file (PDF, image, scanned doc). The system accepts multimodal input types.' },
    { title: 'Task Classifier', desc: 'Hybrid keyword + embedding similarity routing detects task type and selects the best pipeline path automatically.' },
    { title: 'RAG Retrieval', desc: 'ChromaDB performs BM25 + dense vector search across the internal knowledge base with page-level citation matching.' },
    { title: 'Model Router', desc: 'Selects optimal local model: Qwen-Coder for code tasks, Qwen2-VL for visual/OCR, Qwen2.5 for text reasoning.' },
    { title: 'Agentic Planner', desc: 'LangGraph breaks the task into sub-steps, picks tools, and orchestrates the full multi-step execution plan.' },
    { title: 'Docker Sandbox', desc: 'All code and tool calls run in an isolated Docker container — no escapes, no side-effects, completely safe.' },
    { title: 'Risk Engine', desc: '4-stage industrial risk check validates safety, sanity, and regulatory compliance before the output is delivered.' },
    { title: 'HITL Approval', desc: 'For critical outputs, execution pauses and the human operator reviews and approves before the agent finalises.' },
    { title: 'Auto-Retry', desc: 'If the risk engine flags a failure, the agent self-corrects and loops back to re-plan with the error context.' },
    { title: 'Cited Deliverable', desc: 'Final output (.docx / .pptx / .xlsx / code) is generated with inline page citations and a classification tag.' },
  ];

  return (
    <div className="lp-root">

      {/* ── Navbar ─────────────────────────────────────────────── */}
      <nav className={`lp-nav${scrolled ? ' scrolled' : ''}`}>
        <div className="lp-nav-inner">
          <div className="lp-nav-brand">
            <div className="lp-nav-logo"><ShieldCheck size={19} /></div>
            <div>
              <div className="lp-nav-name">AegisAI</div>
              <div className="lp-nav-tag">Sovereign Workbench</div>
            </div>
          </div>
          <div className="lp-nav-links">
            <a href="#features">Features</a>
            <a href="#pipeline">Pipeline</a>
            <a href="#tech">Stack</a>
            <a href="#team">Team</a>
          </div>
          <div className="lp-nav-actions">
            <span className="lp-airgap-badge"><span className="lp-airgap-dot" /> Air-Gapped</span>
            <button className="lp-nav-cta" onClick={onEnter}>
              Sign In<ArrowRight size={14} />
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className="lp-hero">
        {/* Parallax industrial background */}
        <div className="lp-hero-bg" ref={heroBgRef} />
        <div className="lp-hero-overlay" />
        <div className="lp-hero-grid" />
        <div className="lp-hero-glow1" />
        <div className="lp-hero-glow2" />

        <div className="lp-hero-inner">
          <div className="lp-hero-kicker">
            <span className="lp-hero-kicker-dot" />
            Smart India Hackathon 2026 &nbsp;·&nbsp; Team GLITCH &nbsp;·&nbsp; SIH26117
          </div>

          <h1 className="lp-hero-title">
            Sovereign Agentic AI<br />
            for <em>Confidential</em><br />
            Industrial Workflows
          </h1>
          <span className="lp-hero-accent-line" />

          <p className="lp-hero-sub">
            AegisAI runs <strong>entirely on-premise</strong> — zero external API calls, zero data leakage.
            Multi-model orchestration, citation-backed RAG, autonomous multi-step execution,
            and enterprise governance built for PSU and defense environments.
          </p>

          <div className="lp-hero-cta-row">
            <button className="lp-btn-primary" onClick={onEnter}>
              <Zap size={17} /> Open Workbench
            </button>
            <a href="#features" className="lp-btn-outline">
              Explore Features <ChevronDown size={15} />
            </a>
          </div>

          <div className="lp-terminal-wrap">
            <div className="lp-term-bar">
              <div className="lp-term-dots">
                <span className="lp-td lp-td-r" />
                <span className="lp-td lp-td-a" />
                <span className="lp-td lp-td-g" />
              </div>
              <span className="lp-term-label">aegisai@onpremise:~$ bash</span>
            </div>
            <div className="lp-term-body">
              <p><span className="tp">$</span><span className="tc"> git clone</span> &lt;repo-url&gt;</p>
              <p><span className="tp">$</span><span className="tc"> cd</span> ageis-ai <span className="tc">&amp;&amp; docker compose up</span> --build</p>
              <p className="to">✓ ChromaDB vector store  <span className="tg">● READY</span></p>
              <p className="to">✓ Ollama models loaded   <span className="tg">● READY</span></p>
              <p className="to">✓ FastAPI backend        <span className="tg">● READY</span></p>
              <p className="to">✓ Egress monitor active  <span className="tg">0 external calls</span></p>
              <p><span className="tp">$</span> <span className="tb">▌</span></p>
            </div>
          </div>
        </div>

        <div className="lp-scroll-hint">
          <ChevronDown size={20} />
          <span>Scroll</span>
        </div>
      </section>

      {/* ── Stats Band ─────────────────────────────────────────── */}
      <div className="lp-stats-band" ref={statsRef}>
        <div className="lp-stats-inner">
          <StatItem value={0} suffix=" ext. calls" label="Sovereignty — guaranteed" inView={statsInView} />
          <StatItem value={10} suffix="+" label="Unique innovations" inView={statsInView} />
          <StatItem value={4} suffix="-stage" label="Risk validation engine" inView={statsInView} />
          <StatItem value={5} suffix=" models" label="Auto-routed locally" inView={statsInView} />
          <StatItem value={100} suffix="%" label="On-premise — no vendor" inView={statsInView} />
        </div>
      </div>

      {/* ── Features Bento ─────────────────────────────────────── */}
      <section className="lp-features-section" id="features">
        <div className="lp-sec-inner">
          <div className="lp-sec-header">
            <div className="lp-eyebrow">Core Capabilities</div>
            <h2 className="lp-sec-title">
              Built for environments where data<br /><em>cannot leave the premises</em>
            </h2>
            <p className="lp-sec-sub">
              AegisAI replaces the impossible choice between manual work and unauthorized cloud AI
              with a provably sovereign, agentic workbench.
            </p>
          </div>

          <div className="lp-bento">
            {features.map((f, i) => (
              <div key={i} className={`lp-bento-card ${f.cls}${f.wide ? ' lp-bento-wide' : ''}`}>
                <div className="lp-bento-icon"><f.icon size={22} /></div>
                <span className="lp-bento-badge">{f.badge}</span>
                {f.wide ? (
                  <div className="lp-bento-wide-content">
                    <div className="lp-bento-wide-text">
                      <h3 className="lp-bento-title">{f.title}</h3>
                      <p className="lp-bento-desc">{f.desc}</p>
                    </div>
                    <div className="lp-bento-wide-tag">
                      <FileCode2 size={16} /> .docx &nbsp; .pptx &nbsp; .xlsx &nbsp; .py
                    </div>
                  </div>
                ) : (
                  <>
                    <h3 className="lp-bento-title">{f.title}</h3>
                    <p className="lp-bento-desc">{f.desc}</p>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pipeline Flowchart ──────────────────────────────────── */}
      <section className="lp-flow-section" id="pipeline">
        <div className="lp-sec-inner">
          <div className="lp-sec-header">
            <div className="lp-eyebrow">Execution Pipeline</div>
            <h2 className="lp-sec-title">From query to <em>cited deliverable</em><br />— fully on-premise</h2>
            <p className="lp-sec-sub">Click any node to explore the step. The loop self-heals on failure — no human retry needed.</p>
          </div>

          <div className="lp-flow-layout">
            {/* Left: interactive step detail */}
            <div className="lp-flow-detail">
              <div className="lp-flow-step-num">Step {activeFlowStep + 1} / 10</div>
              <h3 className="lp-flow-step-title">{flowStepInfo[activeFlowStep].title}</h3>
              <p className="lp-flow-step-desc">{flowStepInfo[activeFlowStep].desc}</p>
              <div className="lp-flow-progress">
                {flowStepInfo.map((_, i) => (
                  <button
                    key={i}
                    className={`lp-fpb${i === activeFlowStep ? ' active' : ''}${i < activeFlowStep ? ' done' : ''}`}
                    onClick={() => setActiveFlowStep(i)}
                  />
                ))}
              </div>
              <div className="lp-flow-tags">
                {['LangGraph', 'ChromaDB', 'Docker', 'HITL', 'Audit Log'].map(t => (
                  <span key={t} className="lp-flow-tag">{t}</span>
                ))}
              </div>
            </div>

            {/* Right: SVG flowchart */}
            <div className="lp-flow-chart-wrap">
              <Flowchart activeStep={activeFlowStep} onStepClick={setActiveFlowStep} />
            </div>
          </div>
        </div>
      </section>

      {/* ── Governance ─────────────────────────────────────────── */}
      <section className="lp-gov-section" id="governance">
        <div className="lp-sec-inner">
          <div className="lp-sec-header">
            <div className="lp-eyebrow">Output Governance</div>
            <h2 className="lp-sec-title">Every answer carries its<br /><em>classification tag</em> — enforced, not cosmetic</h2>
          </div>
          <div className="lp-classify-grid">
            <div className="lp-classify-card lp-cc-conf">
              <div className="lp-cc-header">
                <div className="lp-cc-icon"><Lock size={18} /></div>
                <span className="lp-cc-tag">CONFIDENTIAL</span>
              </div>
              <p className="lp-cc-desc">Sourced from restricted-access documents. Requires HITL approval before export. Watermarked in Word, PPT headers &amp; footers.</p>
              <ul className="lp-cc-list">
                <li><CheckCircle2 size={13} /> HITL approval gate before every export</li>
                <li><CheckCircle2 size={13} /> Watermarked in all output headers</li>
                <li><CheckCircle2 size={13} /> Audit ledger entry with document hash + timestamp</li>
              </ul>
            </div>
            <div className="lp-classify-card lp-cc-rest">
              <div className="lp-cc-header">
                <div className="lp-cc-icon"><ShieldCheck size={18} /></div>
                <span className="lp-cc-tag">RESTRICTED</span>
              </div>
              <p className="lp-cc-desc">Role-limited documents — visible only to matching RBAC users. Every view is timestamped and logged automatically.</p>
              <ul className="lp-cc-list">
                <li><CheckCircle2 size={13} /> RBAC role-matching enforced at query time</li>
                <li><CheckCircle2 size={13} /> All views logged with user + timestamp</li>
                <li><CheckCircle2 size={13} /> Inherits highest tag of all cited sources</li>
              </ul>
            </div>
            <div className="lp-classify-card lp-cc-int">
              <div className="lp-cc-header">
                <div className="lp-cc-icon"><Shield size={18} /></div>
                <span className="lp-cc-tag">INTERNAL</span>
              </div>
              <p className="lp-cc-desc">General internal knowledge base — standard citation display with no export restriction, still fully audited and traceable.</p>
              <ul className="lp-cc-list">
                <li><CheckCircle2 size={13} /> Standard citation display, no restriction</li>
                <li><CheckCircle2 size={13} /> Audit trail maintained end-to-end</li>
                <li><CheckCircle2 size={13} /> Page-level source attribution always shown</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── Tech Stack ─────────────────────────────────────────── */}
      <section className="lp-tech-section" id="tech">
        <div className="lp-sec-inner" style={{ position: 'relative', zIndex: 1 }}>
          <div className="lp-sec-header">
            <div className="lp-eyebrow" style={{ color: 'var(--yellow)' }}>Technology</div>
            <h2 className="lp-sec-title" style={{ color: 'var(--gray)' }}>
              Open-source stack —<br /><em>no vendor lock-in</em>
            </h2>
          </div>
          <div className="lp-tech-chips">
            {techStack.map((t, i) => (
              <div className="lp-chip" key={i}>
                <span className="lp-chip-cat">{t.category}</span>
                <span className="lp-chip-name">{t.name}</span>
              </div>
            ))}
          </div>
          <div className="lp-sys-box">
            <div className="lp-sys-box-title">System Requirements</div>
            <div className="lp-sys-grid">
              <div className="lp-sys-item"><Cpu size={18} className="lp-sys-ico" /><div><span className="lp-sys-lbl">GPU (Min)</span><span className="lp-sys-val">12 GB VRAM — RTX 3060 or better</span></div></div>
              <div className="lp-sys-item"><Server size={18} className="lp-sys-ico" /><div><span className="lp-sys-lbl">RAM</span><span className="lp-sys-val">16 GB (32 GB recommended)</span></div></div>
              <div className="lp-sys-item"><Database size={18} className="lp-sys-ico" /><div><span className="lp-sys-lbl">Storage</span><span className="lp-sys-val">50 GB free (150 GB SSD ideal)</span></div></div>
              <div className="lp-sys-item"><Network size={18} className="lp-sys-ico" /><div><span className="lp-sys-lbl">OS</span><span className="lp-sys-val">Ubuntu 22.04 or Windows 11</span></div></div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Team ───────────────────────────────────────────────── */}
      <section className="lp-team-section" id="team">
        <div className="lp-sec-inner">
          <div className="lp-sec-header">
            <div className="lp-eyebrow">The Team</div>
            <h2 className="lp-sec-title">Team <em>GLITCH</em></h2>
            <p className="lp-sec-sub">Smart India Hackathon 2026 · Problem Statement SIH26117</p>
          </div>
          <div className="lp-team-card">
            <div className="lp-team-logo">G</div>
            <div className="lp-team-info">
              <div className="lp-team-name">Team GLITCH</div>
              <div className="lp-team-sub">
                Building AegisAI — a Sovereign Agentic AI Workbench for secure industrial
                environments where data cannot leave the premises.
              </div>
              <div className="lp-team-tags">
                <span className="lp-team-tag"><ShieldCheck size={12} /> Smart Automation</span>
                <span className="lp-team-tag"><BarChart3 size={12} /> Software Category</span>
                <span className="lp-team-tag"><Layers size={12} /> SIH26117</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────────── */}
      <section className="lp-cta-section">
        <div className="lp-cta-inner">
          <h2 className="lp-cta-title">
            Ready to keep your data <em>sovereign</em>?
          </h2>
          <p className="lp-cta-sub">
            Launch AegisAI and experience true on-premise agentic intelligence — provably air-gapped, citation-grounded, and fully audited.
          </p>
          <button className="lp-btn-primary lp-btn-lg" onClick={onEnter}>
            <Zap size={18} /> Open Workbench Now
          </button>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="lp-footer">
        <div className="lp-footer-inner">
          <div className="lp-footer-brand">
            <div className="lp-nav-logo" style={{ width: 34, height: 34 }}><ShieldCheck size={16} /></div>
            <span className="lp-footer-name">AegisAI</span>
          </div>
          <p className="lp-footer-copy">
            Proprietary — Smart India Hackathon 2026 submission by Team GLITCH.
            Not licensed for external use or distribution pending evaluation outcome.
          </p>
          <div className="lp-footer-pills">
            <span className="lp-footer-pill"><span className="lp-fpd" /> Sovereign</span>
            <span className="lp-footer-pill"><span className="lp-fpd" /> Air-Gapped</span>
            <span className="lp-footer-pill"><span className="lp-fpd" /> CERT-In Aligned</span>
            <span className="lp-footer-pill"><span className="lp-fpd" /> NCIIPC Compliant</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

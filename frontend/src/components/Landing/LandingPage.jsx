import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot, Phone, Zap, Shield, Clock, ArrowRight, CheckCircle, Star,
  Play, TrendingUp, PhoneCall, BarChart3, Users, Globe, ChevronRight,
  Headphones
} from 'lucide-react';

/* ── Static data ─────────────────────────────────────────── */
const STATS = [
  { value: '<500ms', label: 'Response Latency' },
  { value: '$0.03', label: 'All-In Per Minute' },
  { value: '99.9%', label: 'Platform Uptime' },
  { value: '24/7', label: 'AI Never Sleeps' },
];

const FEATURES = [
  {
    icon: Zap,
    title: 'Sub-500ms Latency',
    body: 'Conversations flow naturally. Edge-optimized voice pipeline means zero awkward pauses — indistinguishable from a live agent.',
    color: 'text-violet-400 bg-violet-500/10',
  },
  {
    icon: PhoneCall,
    title: 'Inbound-First Architecture',
    body: 'Built for customer support, reception, and helpdesk. Every call is answered, classified, and resolved within seconds.',
    color: 'text-emerald-400 bg-emerald-500/10',
  },
  {
    icon: BarChart3,
    title: 'Real-Time Analytics',
    body: 'Resolution rate, avg handle time, call deflection — know exactly how your AI workforce is performing at all times.',
    color: 'text-sky-400 bg-sky-500/10',
  },
  {
    icon: Shield,
    title: 'Enterprise-Grade Security',
    body: 'SOC-2 ready architecture, JWT auth, webhook signature verification. Your conversations stay private.',
    color: 'text-amber-400 bg-amber-500/10',
  },
  {
    icon: Globe,
    title: 'Bring Your Own Carrier',
    body: 'Have Twilio numbers already? Paste one webhook URL and your existing numbers instantly gain AI superpowers.',
    color: 'text-rose-400 bg-rose-500/10',
  },
  {
    icon: Users,
    title: 'Unlimited AI Agents',
    body: 'Deploy specialized agents per department — support, billing, scheduling. Each with its own voice, prompt, and number.',
    color: 'text-violet-400 bg-violet-500/10',
  },
];

const COMPARISON = [
  { feature: 'All-In Price / Min', us: '$0.03', them: '$0.15 – $0.40' },
  { feature: 'Telephony Included', us: '✓ Yes', them: '✗ Extra Charge' },
  { feature: 'STT + LLM + TTS Bundle', us: '✓ Bundled', them: '✗ Separate Billing' },
  { feature: 'Response Latency', us: '< 500ms', them: '1,500ms+' },
  { feature: 'Instant Setup', us: '✓ < 1 min', them: '✗ Days / Dev Work' },
  { feature: 'Inbound Focus', us: '✓ Native', them: '✗ Generic' },
];

const TESTIMONIALS = [
  {
    avatar: 'JK',
    name: 'James K.',
    role: 'Customer Success Director, TechCorp',
    text: "We went from 40% missed calls to 0% overnight. Our CSAT jumped 18 points in the first month.",
  },
  {
    avatar: 'SR',
    name: 'Sara R.',
    role: 'Founder, Reliant Plumbing',
    text: "I run a 3-person shop. VoiceRender answers my phones 24/7. I stopped losing jobs to voicemail.",
  },
  {
    avatar: 'MP',
    name: 'Marcus P.',
    role: 'VP Operations, HealthFirst',
    text: '$0.03 a minute — all in. We were paying $0.28 with our previous vendor for the same quality.',
  },
];

const PRICING = [
  {
    name: 'Free Tier',
    price: '$0',
    period: '',
    note: '100 minutes, no card required',
    features: ['100 minutes included', 'Unlimited AI agents', 'SignalWire numbers', 'Full platform access'],
    cta: 'Start Free',
    to: '/register',
    highlight: false,
  },
  {
    name: 'Growth',
    price: '$0.03',
    period: '/ min',
    note: 'STT + LLM + TTS + Telephony — all in',
    features: ['Pay as you go', 'No contracts, cancel anytime', 'Bring your own Twilio number', 'Priority call routing'],
    cta: 'Get Started',
    to: '/register',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    note: 'Volume pricing + dedicated infra',
    features: ['Dedicated GPU hosting', 'CRM integrations', 'Voice cloning + multilingual', '99.99% SLA + white-glove support'],
    cta: 'Contact Sales',
    to: '/register',
    highlight: false,
  },
];

/* ── Component ───────────────────────────────────────────── */
const LandingPage = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#09090B] text-white overflow-hidden">
      {/* ── Nav ── */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-6 lg:px-12 ${scrolled ? 'py-3 bg-[#09090B]/90 border-b border-white/[0.05] backdrop-blur-xl' : 'py-5'}`}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center shadow-glow-violet">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading font-bold text-white text-lg">VoiceRender</span>
            <span className="hidden sm:block text-[9px] font-bold uppercase tracking-[0.2em] text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded-full border border-violet-500/20">AI Platform</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-500">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <a href="#compare" className="hover:text-white transition-colors">Compare</a>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-semibold text-zinc-500 hover:text-white transition-colors">Sign in</Link>
            <Link to="/register" className="btn-primary h-9 px-4 text-sm">
              Start Free <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative pt-36 pb-24 px-6 lg:px-12 text-center overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[600px] bg-violet-600/10 rounded-full blur-[120px]" />
          <div className="absolute top-32 left-1/4 w-64 h-64 bg-violet-500/5 rounded-full blur-[80px]" />
          <div className="dot-grid absolute inset-0 opacity-[0.12]" />
        </div>

        <div className="relative max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-violet-500/20 bg-violet-500/[0.07] text-violet-300 text-xs font-semibold mb-8 animate-reveal">
            <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-pulse" />
            Inbound AI Voice Infrastructure · Now Live
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-heading font-bold tracking-tight leading-[1.05] mb-7 animate-reveal" style={{ animationDelay: '100ms' }}>
            Your Phones, Answered
            <br />
            <span className="bg-gradient-to-r from-violet-400 via-violet-300 to-fuchsia-400 bg-clip-text text-transparent">
              By AI — 24/7
            </span>
          </h1>

          <p className="text-lg text-zinc-400 max-w-2xl mx-auto mb-10 leading-relaxed font-medium animate-reveal" style={{ animationDelay: '180ms' }}>
            Deploy inbound AI agents that answer calls, resolve issues, and never put customers on hold —
            for <strong className="text-white">$0.03/min, all-in.</strong> STT + LLM + TTS + Telephony. No hidden fees.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-reveal" style={{ animationDelay: '250ms' }}>
            <Link to="/register" className="btn-primary h-12 px-7 text-base shadow-[0_8px_30px_rgba(124,58,237,0.45)]">
              Start Free — No Card Required <ArrowRight className="w-4 h-4" />
            </Link>
            <button
              onClick={() => { setIsPlaying(true); setTimeout(() => setIsPlaying(false), 3000); }}
              className="flex items-center gap-2.5 h-12 px-6 rounded-xl border border-white/[0.1] bg-white/[0.04] hover:bg-white/[0.07] text-white font-semibold transition-all text-sm"
            >
              <div className={`w-7 h-7 rounded-full bg-violet-600 flex items-center justify-center ${isPlaying ? 'animate-pulse' : ''}`}>
                {isPlaying ? <Headphones className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
              </div>
              {isPlaying ? 'Playing demo call…' : 'Hear a Live Demo'}
            </button>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto animate-reveal" style={{ animationDelay: '320ms' }}>
            {STATS.map((s, i) => (
              <div key={i} className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] text-center">
                <p className="text-2xl font-heading font-bold text-white">{s.value}</p>
                <p className="text-[10px] text-zinc-600 font-semibold uppercase tracking-[0.12em] mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="py-24 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-400 mb-4">Platform Capabilities</p>
            <h2 className="text-4xl font-heading font-bold text-white tracking-tight">Built for Inbound Excellence</h2>
            <p className="text-zinc-500 mt-3 max-w-xl mx-auto">Six core capabilities that make VoiceRender the complete inbound AI stack.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <div key={i} className="card-surface p-6 hover-glow-violet transition-all group" style={{ animationDelay: `${i * 60}ms` }}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110 ${f.color}`}>
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="font-heading font-bold text-white mb-2">{f.title}</h3>
                <p className="text-[13px] text-zinc-500 leading-relaxed">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Comparison ── */}
      <section id="compare" className="py-24 px-6 lg:px-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-400 mb-4">Why VoiceRender</p>
            <h2 className="text-4xl font-heading font-bold text-white tracking-tight">We Built What Others Charge Extra For</h2>
          </div>
          <div className="card-surface overflow-hidden">
            <div className="grid grid-cols-3 px-6 py-3 border-b border-white/[0.06]">
              <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-600">Feature</span>
              <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-violet-400 text-center">VoiceRender</span>
              <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-600 text-right">Others</span>
            </div>
            {COMPARISON.map((row, i) => (
              <div key={i} className={`grid grid-cols-3 px-6 py-4 ${i < COMPARISON.length - 1 ? 'border-b border-white/[0.04]' : ''} hover:bg-white/[0.02] transition-colors`}>
                <span className="text-sm text-zinc-500 font-medium">{row.feature}</span>
                <span className="text-sm font-bold text-emerald-400 text-center">{row.us}</span>
                <span className="text-sm text-zinc-700 text-right">{row.them}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ── */}
      <section className="py-24 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-400 mb-4">Customer Stories</p>
            <h2 className="text-4xl font-heading font-bold text-white tracking-tight">Real Results, Real Businesses</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {TESTIMONIALS.map((t, i) => (
              <div key={i} className="card-surface p-6 space-y-4">
                <div className="flex gap-0.5">
                  {[...Array(5)].map((_, s) => <Star key={s} className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />)}
                </div>
                <p className="text-sm text-zinc-400 leading-relaxed">"{t.text}"</p>
                <div className="flex items-center gap-3 pt-2 border-t border-white/[0.05]">
                  <div className="w-9 h-9 rounded-xl bg-violet-500/15 flex items-center justify-center text-[11px] font-black text-violet-400">{t.avatar}</div>
                  <div>
                    <p className="text-sm font-bold text-white">{t.name}</p>
                    <p className="text-[10px] text-zinc-600">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ── */}
      <section id="pricing" className="py-24 px-6 lg:px-12">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-400 mb-4">Pricing</p>
            <h2 className="text-4xl font-heading font-bold text-white tracking-tight">Simple, Transparent, All-In</h2>
            <p className="text-zinc-500 mt-3">No per-vendor billing. No hidden telephony fees. One price covers everything.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {PRICING.map((plan, i) => (
              <div key={i} className={`card-surface p-7 flex flex-col gap-5 relative transition-all ${plan.highlight ? 'border-violet-500/40 shadow-[0_0_40px_rgba(124,58,237,0.15)]' : ''}`}>
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-violet-600 text-[10px] font-bold uppercase tracking-[0.1em] text-white whitespace-nowrap shadow-glow-violet">
                    Most Popular
                  </div>
                )}
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-600 mb-2">{plan.name}</p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-heading font-bold text-white">{plan.price}</span>
                    {plan.period && <span className="text-zinc-600 font-medium">{plan.period}</span>}
                  </div>
                  <p className="text-[11px] text-zinc-600 mt-1">{plan.note}</p>
                </div>
                <ul className="space-y-2.5 flex-1">
                  {plan.features.map((feat, fi) => (
                    <li key={fi} className="flex items-center gap-2.5 text-[13px] text-zinc-400">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      {feat}
                    </li>
                  ))}
                </ul>
                <Link
                  to={plan.to}
                  className={plan.highlight
                    ? 'btn-primary justify-center h-11'
                    : 'flex items-center justify-center gap-2 h-11 rounded-xl border border-white/[0.08] bg-white/[0.04] hover:bg-white/[0.07] text-white text-sm font-semibold transition-all'
                  }
                >
                  {plan.cta} <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-24 px-6 lg:px-12">
        <div className="max-w-3xl mx-auto text-center">
          <div className="relative p-12 rounded-3xl border border-violet-500/20 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-violet-900/20 to-transparent pointer-events-none" />
            <div className="relative">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-400 mb-4">Get Started Today</p>
              <h2 className="text-4xl font-heading font-bold text-white tracking-tight mb-4">
                Your First 100 Minutes Are Free
              </h2>
              <p className="text-zinc-500 mb-8">No credit card. No setup fee. Just sign up, connect a number, and your AI answers the first call within minutes.</p>
              <Link to="/register" className="btn-primary h-12 px-8 text-base inline-flex shadow-[0_8px_30px_rgba(124,58,237,0.45)]">
                Create Free Account <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/[0.05] px-6 lg:px-12 py-10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center">
              <Zap className="w-3 h-3 text-white" />
            </div>
            <span className="font-heading font-bold text-white text-sm">VoiceRender</span>
          </div>
          <p className="text-[11px] text-zinc-700">© {new Date().getFullYear()} VoiceRender AI. Built for businesses that can't afford to miss a call.</p>
          <div className="flex items-center gap-5 text-[11px] text-zinc-600">
            <Link to="/login" className="hover:text-white transition-colors">Sign In</Link>
            <Link to="/register" className="hover:text-white transition-colors">Get Started</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
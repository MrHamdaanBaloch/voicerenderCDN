import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  Bot,
  Phone,
  BarChart3,
  Zap,
  Shield,
  Clock,
  ArrowRight,
  CheckCircle,
  Star,
  Play,
  TrendingUp,
  Infinity,
  ZapOff
} from 'lucide-react';

const LandingPage = () => {
  const [isPlaying, setIsPlaying] = useState(false);

  const handlePlayDemo = () => {
    setIsPlaying(true);
    // In a real app, this would play an audio sample
    setTimeout(() => setIsPlaying(false), 3000);
  };

  const features = [
    {
      icon: Zap,
      title: 'Sub-500ms Latency',
      description: 'Conversations flow naturally without awkward pauses. Our edge-optimized infrastructure ensures lightning-fast responses.'
    },
    {
      icon: Bot,
      title: 'Humanlike Voices',
      description: 'Advanced neural TTS creates voices so realistic, your customers won\'t believe they\'re talking to an AI.'
    },
    {
      icon: TrendingUp,
      title: 'Built to Close',
      description: 'Unlike generic bots, our AI is trained on high-converting sales scripts to handle objections and close deals.'
    }
  ];

  const comparisons = [
    { feature: 'Price per Minute', us: '$0.03', others: '$0.15+' },
    { feature: 'Telephony Included', us: 'Yes', others: 'Extra Charge' },
    { feature: 'Setup Time', us: '1 Second', others: 'Days/Weeks' },
    { feature: 'Latencey', us: '<500ms', others: '1500ms+' },
  ];

  const pricingTiers = [
    {
      name: 'Enterprise Conversion+',
      price: 'Custom',
      period: '',
      description: 'Turn every inbound call into revenue. Enterprise-grade AI voice agents 24/7.',
      features: [
        'Dedicated GPU hosting',
        'API integrations with CRM',
        'Voice cloning + Multilingual',
        '99.99% uptime SLA',
        'Priority support & onboarding'
      ],
      popular: false,
      cta: 'Contact Sales',
      outcome: 'AI Handles Calls. You Handle Growth.'
    },
    {
      name: 'Growth Plan',
      price: '$0.03',
      period: '/min',
      description: 'Scale sales and support affordably. No hidden costs. Competitors charge extra for telephony — we don’t.',
      features: [
        'Pay as you go',
        'STT + Brain + TTS + Telephony',
        'Sub-500ms latency',
        'Unlimited team members',
        'Analytics (conversion, outcomes)'
      ],
      popular: true,
      cta: 'Only $0.03/min. Includes Everything.',
      outcome: 'Scale sales and support affordably.'
    },
    {
      name: 'Free Trial',
      price: '$0',
      period: '/forever',
      description: 'Test AI calls in real conversations. No risk, no card. 100 minutes free.',
      features: [
        '100 free minutes included',
        'STT + Brain + TTS + Telephony',
        'Access to all premium voices',
        'Unlimited concurrent calls',
        'Live dashboard + transcripts'
      ],
      popular: false,
      cta: 'Try 100 Minutes Free — No Card Needed.',
      outcome: 'Test AI calls in real conversations.'
    }
  ];

  return (
    <div className="min-h-screen bg-brand-black text-brand-white selection:bg-brand-violet selection:text-white">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 glass-dark border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3 group cursor-pointer">
              <div className="w-10 h-10 bg-brand-violet rounded-xl flex items-center justify-center shadow-[0_0_15px_rgba(108,99,255,0.5)] group-hover:scale-110 transition-transform">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold tracking-tight">VoiceRender</span>
            </div>

            <div className="hidden md:flex items-center space-x-8">
              <a href="#demo" className="text-gray-300 hover:text-brand-violet transition-colors font-medium">Try Demo</a>
              <a href="#pricing" className="text-gray-300 hover:text-brand-violet transition-colors font-medium">Pricing</a>
              <Link to="/login" className="text-gray-300 hover:text-brand-violet transition-colors font-medium">Login</Link>
              <Button asChild className="bg-brand-violet hover:bg-brand-violet/90 text-white shadow-[0_0_20px_rgba(108,99,255,0.3)] hover:shadow-[0_0_25px_rgba(108,99,255,0.5)] transition-all scale-100 hover:scale-105">
                <Link to="/register">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden bg-gradient-hero">
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center animate-reveal">
            <Badge className="mb-6 bg-brand-violet/20 text-brand-violet border-brand-violet/30 px-4 py-1 animate-pulse">
              Early Bird Pricing • Limited Slots Available
            </Badge>

            <h1 className="text-6xl md:text-8xl font-bold mb-8 tracking-tighter leading-none">
              AI Voices So Real, <br />
              <span className="text-brand-violet text-glow">They Close Deals For You.</span>
            </h1>

            <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-3xl mx-auto font-body">
              From call to customer in seconds. <span className="text-white font-semibold">Zero setup</span>, humanlike voices.
              "Your AI Voice Agent, Ready in 1 Second."
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <Button
                onClick={handlePlayDemo}
                size="lg"
                className={`h-16 px-8 text-lg bg-brand-violet hover:bg-brand-violet/90 text-white rounded-full transition-all group ${isPlaying ? 'scale-95' : 'hover:scale-105 hover:glow'}`}
              >
                {isPlaying ? (
                  <span className="flex items-center"><Zap className="mr-2 animate-spin" /> Generating...</span>
                ) : (
                  <span className="flex items-center"><Play className="mr-2 fill-current" /> Hear the Demo</span>
                )}
              </Button>

              <Button variant="ghost" size="lg" asChild className="h-16 px-8 text-lg text-white hover:bg-white/5 border border-white/10 rounded-full">
                <Link to="/register">
                  Try 100 Minutes Free
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Link>
              </Button>
            </div>

            <div className="mt-16 flex justify-center items-center space-x-12 opacity-50 grayscale hover:grayscale-0 transition-all">
              <div className="flex items-center space-x-2"><Shield className="w-5 h-5" /> <span>Secure by Design</span></div>
              <div className="flex items-center space-x-2"><Clock className="w-5 h-5" /> <span>99.9% Uptime</span></div>
              <div className="flex items-center space-x-2"><Zap className="w-5 h-5" /> <span>&lt;500ms Latency</span></div>
            </div>
          </div>
        </div>

        {/* Background glow effects */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-violet/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-brand-violet/5 blur-[100px] rounded-full"></div>
      </section>

      {/* USP Banner */}
      <section className="py-12 bg-brand-black border-y border-white/10">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h2 className="text-2xl md:text-4xl font-bold text-white">
            One Transparent Price: <span className="text-brand-violet">$0.03/min.</span> Includes Everything.
          </h2>
        </div>
      </section>

      {/* USP Details & Comparison */}
      <section className="py-24 bg-brand-black px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold mb-8 leading-tight">
                Stop losing leads. <br />
                <span className="text-gray-500">Let AI close them for you.</span>
              </h2>
              <div className="space-y-6">
                {features.map((f, i) => (
                  <div key={i} className="flex items-start space-x-4 p-4 rounded-2xl border border-white/5 hover:bg-white/5 transition-colors group">
                    <div className="w-12 h-12 bg-brand-violet/10 rounded-xl flex items-center justify-center group-hover:bg-brand-violet group-hover:text-white transition-all text-brand-violet">
                      <f.icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold mb-1">{f.title}</h3>
                      <p className="text-gray-400">{f.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-dark rounded-3xl p-8 border-white/10 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4">
                <Badge className="bg-brand-violet text-white">Why Us?</Badge>
              </div>
              <h3 className="text-2xl font-bold mb-8 italic">The Competition vs. VoiceRender</h3>
              <div className="space-y-4">
                {comparisons.map((c, i) => (
                  <div key={i} className="grid grid-cols-3 py-4 border-b border-white/10 last:border-0">
                    <span className="text-gray-400 font-medium">{c.feature}</span>
                    <span className="text-center text-red-400 opacity-50">{c.others}</span>
                    <span className="text-right text-brand-violet font-bold">{c.us}</span>
                  </div>
                ))}
              </div>
              <div className="mt-8 p-4 bg-brand-violet/10 rounded-xl border border-brand-violet/20 flex items-center space-x-3">
                <ZapOff className="text-brand-violet w-5 h-5" />
                <p className="text-sm font-medium">Others charge extra for telephony. We don’t.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-32 px-4 relative overflow-hidden">
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-20 animate-reveal">
            <h2 className="text-5xl md:text-6xl font-bold mb-6 tracking-tight">Outcome-Driven Pricing</h2>
            <p className="text-xl text-gray-400">Scale without limits. No hidden fees. Pay only for performance.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
            {pricingTiers.map((tier, index) => (
              <div
                key={index}
                className={`relative flex flex-col p-8 rounded-[2rem] transition-all duration-500 hover:scale-[1.02] ${tier.popular
                  ? 'bg-brand-white text-brand-black shadow-[0_0_50px_rgba(108,99,255,0.2)] z-20'
                  : 'glass-dark border border-white/10 hover:border-brand-violet/50 z-10'
                  }`}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-brand-violet text-white px-6 py-1 rounded-full text-sm font-bold tracking-widest uppercase">
                    Recommended
                  </div>
                )}

                <div className="mb-8">
                  <h3 className="text-xl font-bold mb-4 opacity-50 uppercase tracking-widest">{tier.name}</h3>
                  <div className="flex items-baseline space-x-1">
                    <span className="text-5xl font-bold">{tier.price}</span>
                    <span className="text-lg opacity-60">{tier.period}</span>
                  </div>
                  <p className={`mt-4 ${tier.popular ? 'text-gray-600' : 'text-gray-400'}`}>{tier.description}</p>
                </div>

                <div className="flex-grow space-y-4 mb-8">
                  {tier.features.map((feature, i) => (
                    <div key={i} className="flex items-center space-x-3">
                      <CheckCircle className={`w-5 h-5 flex-shrink-0 ${tier.popular ? 'text-brand-violet' : 'text-brand-violet'}`} />
                      <span className="font-medium">{feature}</span>
                    </div>
                  ))}
                </div>

                <div className={`mt-auto pt-8 border-t ${tier.popular ? 'border-gray-200' : 'border-white/10'}`}>
                  <p className="text-sm font-bold mb-6 italic opacity-80 leading-snug">"{tier.outcome}"</p>
                  <Button
                    className={`w-full h-14 text-lg font-bold rounded-2xl shadow-lg transition-transform hover:scale-105 active:scale-95 ${tier.popular
                      ? 'bg-brand-black text-white hover:bg-brand-black/90'
                      : 'bg-brand-violet text-white hover:bg-brand-violet/90'
                      }`}
                    asChild
                  >
                    <Link to="/register">{tier.cta}</Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-32 bg-brand-black">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-end mb-16 gap-8 text-center md:text-left">
            <div>
              <h2 className="text-5xl md:text-6xl font-bold tracking-tight mb-4 text-white">Loved by Founders.</h2>
              <p className="text-xl text-gray-400">Join 500+ teams scaling their outreach with VoiceRender.</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="flex -space-x-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="w-12 h-12 bg-white/10 rounded-full border-4 border-brand-black"></div>
                ))}
              </div>
              <span className="font-bold text-white">+492 others</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[1, 2, 3].map((_, i) => (
              <div key={i} className="p-8 rounded-3xl bg-white/5 border border-white/10 hover:border-brand-violet/30 transition-colors group">
                <div className="flex mb-6 text-brand-violet">
                  {[1, 2, 3, 4, 5].map(j => <Star key={j} className="w-5 h-5 fill-current" />)}
                </div>
                <p className="text-lg mb-8 leading-relaxed font-medium text-gray-300">
                  "{i === 0 ? "VoiceRender transformed our lead qualification process. We're now handling 3x more prospects with better conversion rates." :
                    i === 1 ? "The setup was incredibly easy and the results immediate. Our customer support is now available 24/7 without additional staff." :
                      "The analytics insights help us understand our customers better than ever. It's like having a conversation analyst for every call."}"
                </p>
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-white/10 rounded-full"></div>
                  <div>
                    <h4 className="font-bold text-white">{i === 0 ? "Sarah Chen" : i === 1 ? "Marcus Johnson" : "Elena Rodriguez"}</h4>
                    <p className="text-sm text-gray-500">{i === 0 ? "VP of Sales, TechFlow" : i === 1 ? "Ops Director, ServicePro" : "Founder, GrowthLabs"}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-32 bg-brand-violet text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-10"></div>
        <div className="max-w-4xl mx-auto text-center px-4 relative z-10">
          <h2 className="text-5xl md:text-7xl font-bold mb-8 tracking-tighter">
            Ready to let AI <br />close your deals?
          </h2>
          <p className="text-xl md:text-2xl text-white/80 mb-12">
            Try 100 Minutes Free. No Credit Card Needed. Setup in 1 Second.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="h-16 px-10 text-xl bg-white text-brand-violet hover:bg-white/90 rounded-2xl font-bold shadow-2xl transition-transform hover:scale-105 active:scale-95" asChild>
              <Link to="/register">Get Started Now</Link>
            </Button>
            <Button size="lg" variant="outline" className="h-16 px-10 text-xl border-white/30 text-white hover:bg-white/10 rounded-2xl font-bold transition-transform hover:scale-105 active:scale-95">
              Talk to Enterprise AI
            </Button>
          </div>
        </div>
        {/* Animated circles */}
        <div className="absolute -top-24 -left-24 w-64 h-64 border-[40px] border-white/10 rounded-full animate-[spin_10s_linear_infinite]"></div>
        <div className="absolute -bottom-24 -right-24 w-64 h-64 border-[40px] border-white/10 rounded-full animate-[spin_15s_linear_infinite_reverse]"></div>
      </section>

      {/* Footer */}
      <footer className="bg-brand-black text-white py-20 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            <div>
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-8 h-8 bg-brand-violet rounded-lg flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold">VoiceRender</span>
              </div>
              <p className="text-gray-400 leading-relaxed">
                The future of business phone calls, powered by AI. Humanlike voices, sub-500ms latency.
              </p>
            </div>

            {[
              { title: 'Product', links: ['Features', 'Pricing', 'API Docs', 'Integrations'] },
              { title: 'Company', links: ['About', 'Blog', 'Careers', 'Contact'] },
              { title: 'Support', links: ['Help Center', 'Status', 'Privacy', 'Terms'] }
            ].map((col, i) => (
              <div key={i}>
                <h4 className="font-bold mb-6 text-brand-violet uppercase tracking-widest text-sm">{col.title}</h4>
                <ul className="space-y-4 text-gray-400">
                  {col.links.map((link, j) => (
                    <li key={j}><a href="#" className="hover:text-white transition-colors">{link}</a></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="border-t border-white/5 mt-20 pt-10 text-center text-gray-500 text-sm">
            <p>&copy; 2026 VoiceRender AI. All rights reserved. Premium AI Phone Agents.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
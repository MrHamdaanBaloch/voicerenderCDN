import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  ArrowLeft, Save, Bot, Mic, Brain, Phone, Settings as SettingsIcon,
  TestTube, Zap, Cpu, ShieldCheck, ChevronLeft, ChevronRight, Check, Hash, Loader2
} from 'lucide-react';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';
import { getErrorMessage } from '../../lib/utils';

const AgentForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    llm_model: 'llama3-8b-8192',
    tts_model: 'playai-tts',
    tts_voice: 'Fritz-PlayAI',
    deepgram_model: 'nova-2-phonecall',
    system_prompt: 'You are a helpful, professional, and concise AI assistant. Respond naturally, keeping responses under 20 words. Maintain a positive and engaging tone.',
    deepgram_config: { utterance_end_ms: '1000', endpointing: '1500', filler_words: true },
    silence_timeout_seconds: 7,
    silence_prompt_text: 'Are you still there? How can I help?',
    is_active: false,
    signalwire_phone_number: '',
  });

  const [isSaving, setIsSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('basic');
  const [phoneNumbers, setPhoneNumbers] = useState([]);

  const tabOrder = ['basic', 'voice', 'advanced', 'phone'];
  const tabMeta = {
    basic: { label: 'Identity', icon: Bot },
    voice: { label: 'Vocal/AI', icon: Mic },
    advanced: { label: 'Neural', icon: SettingsIcon },
    phone: { label: 'Gateway', icon: Phone },
  };
  const idx = tabOrder.indexOf(activeTab);
  const isFirst = idx === 0;
  const isLast = idx === tabOrder.length - 1;

  const llmModels = [
    { value: 'llama3-8b-8192', label: 'Llama 3 8B (Fast)' },
    { value: 'llama3-70b-8192', label: 'Llama 3 70B (Advanced)' },
    { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B' },
  ];
  const ttsVoices = [
    { value: 'Fritz-PlayAI', label: 'Fritz (Male · PlayAI)' },
    { value: 'Sarah-PlayAI', label: 'Sarah (Female · PlayAI)' },
    { value: 'Mike-PlayAI', label: 'Mike (Professional Male)' },
    { value: 'Emma-PlayAI', label: 'Emma (Friendly Female)' },
    { value: 'James-PlayAI', label: 'James (Authoritative Male)' },
  ];
  const deepgramModels = [
    { value: 'nova-2-phonecall', label: 'Nova 2 Phone Call (Optimized)' },
    { value: 'nova-2-general', label: 'Nova 2 General (High accuracy)' },
    { value: 'enhanced', label: 'Enhanced (Legacy)' },
  ];

  useEffect(() => {
    const load = async () => {
      if (isEditing) {
        try {
          const res = await api.agents.getAgent(id);
          const a = res.data;
          setFormData({
            name: a.name, description: a.description || '',
            llm_model: a.llm_model, tts_model: a.tts_model,
            tts_voice: a.tts_voice, deepgram_model: a.deepgram_model,
            system_prompt: a.system_prompt,
            deepgram_config: a.deepgram_config || { utterance_end_ms: '1000', endpointing: '1500', filler_words: true },
            silence_timeout_seconds: a.silence_timeout_seconds,
            silence_prompt_text: a.silence_prompt_text || '',
            is_active: a.is_active,
            signalwire_phone_number: a.signalwire_phone_number || '',
          });
        } catch (err) {
          setError('Failed to load agent.');
          toast({ title: 'Error', description: 'Failed to load agent.', variant: 'destructive' });
        }
      }
      setLoading(false);
    };
    load();
  }, [id, isEditing, toast]);

  useEffect(() => {
    api.billing.getPhoneNumbers().then(r => setPhoneNumbers(r.data)).catch(() => { });
  }, []);

  const set = (field, val) => setFormData(p => ({ ...p, [field]: val }));
  const setDg = (field, val) => setFormData(p => ({ ...p, deepgram_config: { ...p.deepgram_config, [field]: val } }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      if (isEditing) await api.agents.updateAgent(id, formData);
      else await api.agents.createAgent(formData);
      toast({ title: isEditing ? 'Agent Updated' : 'Agent Deployed', description: 'Configuration saved.' });
      navigate('/agents');
    } catch (err) {
      const msg = getErrorMessage(err, 'Failed to save agent.');
      setError(msg);
      toast({ title: 'Error', description: msg, variant: 'destructive' });
    } finally {
      setIsSaving(false);
    }
  };

  /* ── Shared input class ── */
  const inp = 'form-input h-11 w-full';
  const sel = 'h-11 border-white/[0.06] bg-white/[0.04] text-white rounded-xl font-semibold';
  const selContent = 'rounded-xl border-white/[0.1] bg-[#18181b] text-white';
  const selItem = 'py-2.5 focus:bg-violet-500/10 focus:text-violet-300';
  const lbl = 'text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-600';

  if (loading && isEditing) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <div className="w-12 h-12 rounded-2xl bg-violet-500/10 flex items-center justify-center animate-pulse-slow">
          <Cpu className="w-6 h-6 text-violet-400" />
        </div>
        <p className="text-sm font-semibold text-zinc-500">Loading agent…</p>
      </div>
    );
  }

  return (
    <div className="space-y-7 animate-reveal max-w-5xl mx-auto">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link to="/agents" className="p-2.5 rounded-xl border border-white/[0.08] bg-white/[0.04] text-zinc-600 hover:text-white hover:bg-white/[0.07] transition-all">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-heading font-bold text-white tracking-tight">
              {isEditing ? 'Edit Agent' : 'New Agent'}
            </h1>
            <p className="text-xs text-zinc-600 mt-0.5">
              {isEditing ? `Editing: ${formData.name}` : 'Configure your inbound AI agent.'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="submit" form="agent-form"
            disabled={isSaving || !formData.name}
            className="btn-primary h-10 px-5 disabled:opacity-60"
          >
            {isSaving ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</> : <><Save className="w-4 h-4" /> {isEditing ? 'Save' : 'Deploy Agent'}</>}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-400 text-sm">{error}</div>
      )}

      <form id="agent-form" onSubmit={handleSubmit}>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          {/* Tab bar */}
          <TabsList className="grid w-full grid-cols-4 h-auto p-1 rounded-xl border border-white/[0.07] bg-white/[0.03] gap-1">
            {tabOrder.map(tab => {
              const Icon = tabMeta[tab].icon;
              const active = activeTab === tab;
              return (
                <TabsTrigger
                  key={tab}
                  value={tab}
                  className={`rounded-lg py-2.5 text-xs font-bold transition-all flex items-center gap-1.5
                    ${active ? 'bg-violet-600 text-white shadow-glow-violet' : 'text-zinc-600 hover:text-zinc-300'}`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tabMeta[tab].label}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {/* Step progress */}
          <div className="mt-4 mb-6">
            <div className="flex gap-1.5">
              {tabOrder.map((tab, i) => (
                <div key={tab} className={`h-1 flex-1 rounded-full transition-all duration-500 ${i <= idx ? 'bg-violet-600' : 'bg-white/[0.07]'}`} />
              ))}
            </div>
          </div>

          {/* ── Tab: Identity ── */}
          <TabsContent value="basic">
            <div className="card-surface p-6 space-y-6">
              <div className="flex items-center gap-2.5 pb-4 border-b border-white/[0.06]">
                <Bot className="w-4 h-4 text-violet-400" />
                <h3 className="font-heading font-bold text-white text-sm">Agent Identity</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <Label htmlFor="name" className={lbl}>Agent Name *</Label>
                  <input
                    id="name" placeholder="e.g., Support AI — Sarah"
                    value={formData.name}
                    onChange={e => set('name', e.target.value)}
                    className={inp} required
                  />
                </div>
                <div className="space-y-2">
                  <Label className={lbl}>Deployment Status</Label>
                  <div className="flex items-center justify-between h-11 px-4 rounded-xl border border-white/[0.06] bg-white/[0.04]">
                    <div className="flex items-center gap-2.5">
                      <Switch
                        checked={formData.is_active}
                        onCheckedChange={v => set('is_active', v)}
                        className="data-[state=checked]:bg-violet-600"
                      />
                      <span className="text-sm font-semibold text-white">{formData.is_active ? 'Active' : 'Standby'}</span>
                    </div>
                    <span className={formData.is_active ? 'badge-active' : 'badge-inactive'}>
                      {formData.is_active ? 'Live' : 'Off'}
                    </span>
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description" className={lbl}>Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe this agent's role, tone, and objectives…"
                  value={formData.description}
                  onChange={e => set('description', e.target.value)}
                  rows={3} className="form-input w-full resize-none"
                />
              </div>
            </div>
          </TabsContent>

          {/* ── Tab: Vocal/AI ── */}
          <TabsContent value="voice">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="card-surface p-6 space-y-5">
                <div className="flex items-center gap-2.5 pb-4 border-b border-white/[0.06]">
                  <Brain className="w-4 h-4 text-violet-400" />
                  <h3 className="font-heading font-bold text-white text-sm">Intelligence Lattice</h3>
                </div>
                <div className="space-y-2">
                  <Label className={lbl}>Logical Engine (LLM)</Label>
                  <Select value={formData.llm_model} onValueChange={v => set('llm_model', v)}>
                    <SelectTrigger className={sel}><SelectValue /></SelectTrigger>
                    <SelectContent className={selContent}>
                      {llmModels.map(m => <SelectItem key={m.value} value={m.value} className={selItem}>{m.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className={lbl}>Vocal Synthesizer (TTS)</Label>
                  <Select value={formData.tts_voice} onValueChange={v => set('tts_voice', v)}>
                    <SelectTrigger className={sel}><SelectValue /></SelectTrigger>
                    <SelectContent className={selContent}>
                      {ttsVoices.map(v => <SelectItem key={v.value} value={v.value} className={selItem}>{v.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className={lbl}>Auditory Processor (STT)</Label>
                  <Select value={formData.deepgram_model} onValueChange={v => set('deepgram_model', v)}>
                    <SelectTrigger className={sel}><SelectValue /></SelectTrigger>
                    <SelectContent className={selContent}>
                      {deepgramModels.map(m => <SelectItem key={m.value} value={m.value} className={selItem}>{m.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="card-surface p-6 space-y-4">
                <div className="flex items-center gap-2.5 pb-4 border-b border-white/[0.06]">
                  <Brain className="w-4 h-4 text-violet-400" />
                  <h3 className="font-heading font-bold text-white text-sm">Behavioral Directives</h3>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="system_prompt" className={lbl}>System Instructions</Label>
                  <Textarea
                    id="system_prompt"
                    placeholder="You are a professional inbound AI assistant…"
                    value={formData.system_prompt}
                    onChange={e => set('system_prompt', e.target.value)}
                    rows={10} className="form-input w-full font-mono-ui text-xs resize-none"
                  />
                  <div className="flex items-center gap-1.5 text-[11px] text-zinc-700 mt-1">
                    <Zap className="w-3 h-3 text-violet-700" />
                    Prompt optimized for latency &amp; clarity.
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* ── Tab: Neural ── */}
          <TabsContent value="advanced">
            <div className="card-surface p-6 space-y-7">
              <div className="pb-4 border-b border-white/[0.06]">
                <h3 className="font-heading font-bold text-white">Neural Fine-Tuning</h3>
                <p className="text-xs text-zinc-600 mt-0.5">Calibrate timing and recognition for low-latency calls.</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div className="space-y-5">
                  <h4 className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.12em] text-violet-400">
                    <Mic className="w-3.5 h-3.5" /> Acoustic Thresholds
                  </h4>
                  <div className="space-y-2">
                    <Label htmlFor="utterance_end" className={lbl}>Utterance End (ms)</Label>
                    <input id="utterance_end" type="number"
                      value={formData.deepgram_config.utterance_end_ms}
                      onChange={e => setDg('utterance_end_ms', e.target.value)}
                      className="form-input h-10 w-full"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="endpointing" className={lbl}>Neural Endpointing (ms)</Label>
                    <input id="endpointing" type="number"
                      value={formData.deepgram_config.endpointing}
                      onChange={e => setDg('endpointing', e.target.value)}
                      className="form-input h-10 w-full"
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-xl border border-white/[0.06] bg-white/[0.03]">
                    <Label className="text-sm font-semibold text-white">Syntactic Fillers</Label>
                    <Switch
                      checked={formData.deepgram_config.filler_words}
                      onCheckedChange={v => setDg('filler_words', v)}
                      className="data-[state=checked]:bg-violet-600"
                    />
                  </div>
                </div>
                <div className="space-y-5">
                  <h4 className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.12em] text-violet-400">
                    <ShieldCheck className="w-3.5 h-3.5" /> Engagement Failsafe
                  </h4>
                  <div className="space-y-2">
                    <Label htmlFor="silence_timeout" className={lbl}>Silence Timeout (seconds)</Label>
                    <input id="silence_timeout" type="number"
                      value={formData.silence_timeout_seconds}
                      onChange={e => set('silence_timeout_seconds', parseInt(e.target.value) || 7)}
                      className="form-input h-10 w-full"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="silence_prompt" className={lbl}>Re-engagement Prompt</Label>
                    <Textarea
                      id="silence_prompt"
                      placeholder="Are you still there?"
                      value={formData.silence_prompt_text}
                      onChange={e => set('silence_prompt_text', e.target.value)}
                      rows={3} className="form-input w-full resize-none"
                    />
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* ── Tab: Gateway ── */}
          <TabsContent value="phone">
            <div className="card-surface p-6 space-y-6">
              <div className="flex items-center gap-2.5 pb-4 border-b border-white/[0.06]">
                <Phone className="w-4 h-4 text-violet-400" />
                <h3 className="font-heading font-bold text-white text-sm">Connectivity Gateway</h3>
                <p className="text-xs text-zinc-600 ml-1">— Link to an inbound number.</p>
              </div>
              <div className="max-w-lg space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="phone_number" className={lbl}>Assigned Inbound Number</Label>
                  <Select
                    value={formData.signalwire_phone_number || 'none'}
                    onValueChange={v => set('signalwire_phone_number', v === 'none' ? '' : v)}
                  >
                    <SelectTrigger className={sel}>
                      <SelectValue placeholder="Select a phone number…" />
                    </SelectTrigger>
                    <SelectContent className={selContent}>
                      <SelectItem value="none" className={selItem}>None — manual test only</SelectItem>
                      {phoneNumbers.map(n => (
                        <SelectItem key={n.id} value={n.phone_number} className={selItem}>
                          {n.phone_number}{n.friendly_name ? ` (${n.friendly_name})` : ''} — {n.provider}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Link
                  to="/phone-numbers"
                  className="flex items-center justify-between p-4 rounded-xl border border-violet-500/20 bg-violet-500/[0.06] hover:bg-violet-500/10 transition-colors group"
                >
                  <div>
                    <p className="text-sm font-semibold text-white group-hover:text-violet-300 transition-colors">Manage Phone Numbers</p>
                    <p className="text-[11px] text-zinc-600">Buy SignalWire or import your own Twilio number</p>
                  </div>
                  <Hash className="w-4 h-4 text-violet-500 shrink-0 group-hover:text-violet-300" />
                </Link>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-white/[0.05]">
                {[['1', 'Provision', 'Buy a number or import Twilio on the Numbers page.'],
                ['2', 'Select', 'Choose that number above.'],
                ['3', 'Test', 'Run a unit test before going live.']].map(([n, title, desc]) => (
                  <div key={n} className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                    <div className="w-6 h-6 rounded-lg bg-violet-600 flex items-center justify-center text-[10px] text-white font-bold mb-2">{n}</div>
                    <p className="text-sm font-bold text-white mb-1">{title}</p>
                    <p className="text-[11px] text-zinc-600 leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* ── Prev / Next nav ── */}
        <div className="flex items-center justify-between mt-6 pt-5 border-t border-white/[0.05]">
          <button
            type="button" onClick={() => !isFirst && setActiveTab(tabOrder[idx - 1])}
            disabled={isFirst}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${isFirst
                ? 'opacity-20 cursor-not-allowed text-zinc-600 bg-transparent'
                : 'text-zinc-400 hover:text-white border border-white/[0.07] bg-white/[0.03] hover:bg-white/[0.07]'
              }`}
          >
            <ChevronLeft className="w-4 h-4" />
            {!isFirst ? tabMeta[tabOrder[idx - 1]].label : 'Back'}
          </button>

          {isLast ? (
            <Button
              type="submit"
              disabled={isSaving || !formData.name}
              className="btn-primary h-10 px-6 disabled:opacity-60"
            >
              {isSaving
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Deploying…</>
                : <><Check className="w-4 h-4" /> {isEditing ? 'Save Changes' : 'Deploy Agent'}</>
              }
            </Button>
          ) : (
            <button
              type="button"
              onClick={() => setActiveTab(tabOrder[idx + 1])}
              className="btn-primary flex items-center gap-2 h-10 px-5"
            >
              {tabMeta[tabOrder[idx + 1]].label} <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default AgentForm;

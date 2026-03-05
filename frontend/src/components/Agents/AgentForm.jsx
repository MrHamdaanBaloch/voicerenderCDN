import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  ArrowLeft,
  Save,
  Play,
  Bot,
  Mic,
  Brain,
  Phone,
  Settings as SettingsIcon,
  TestTube,
  Zap,
  Cpu,
  ShieldCheck,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Check
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
    system_prompt: 'You are a helpful, professional, and concise AI assistant. Respond naturally, like a human, keeping your responses under 20 words. Maintain a positive and engaging tone, and always strive to provide value to the user.',
    deepgram_config: {
      utterance_end_ms: '1000',
      endpointing: '1500',
      filler_words: true
    },
    silence_timeout_seconds: 7,
    silence_prompt_text: "Are you still there? How can I help?",
    is_active: false,
    signalwire_phone_number: ''
  });

  const [isSaving, setIsSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('basic');

  const tabOrder = ['basic', 'voice', 'advanced', 'phone'];
  const tabLabels = { basic: 'Identity', voice: 'Vocal/AI', advanced: 'Neural', phone: 'Gateway' };
  const tabIcons = { basic: Bot, voice: Mic, advanced: SettingsIcon, phone: Phone };
  const currentStepIndex = tabOrder.indexOf(activeTab);
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === tabOrder.length - 1;
  const goNext = () => !isLastStep && setActiveTab(tabOrder[currentStepIndex + 1]);
  const goPrev = () => !isFirstStep && setActiveTab(tabOrder[currentStepIndex - 1]);

  const llmModels = [
    { value: 'llama3-8b-8192', label: 'Llama 3 8B (Fast)' },
    { value: 'llama3-70b-8192', label: 'Llama 3 70B (Advanced)' },
    { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B' },
  ];

  const ttsVoices = [
    { value: 'Fritz-PlayAI', label: 'Fritz (PlayAI Male)' },
    { value: 'Sarah-PlayAI', label: 'Sarah (PlayAI Female)' },
    { value: 'Mike-PlayAI', label: 'Mike (Professional Male)' },
    { value: 'Emma-PlayAI', label: 'Emma (Friendly Female)' },
    { value: 'James-PlayAI', label: 'James (Authoritative Male)' },
  ];

  const deepgramModels = [
    { value: 'nova-2-phonecall', label: 'Nova 2 Phone Call (Optimized for calls)' },
    { value: 'nova-2-general', label: 'Nova 2 General (High accuracy)' },
    { value: 'enhanced', label: 'Enhanced (Legacy)' },
  ];

  useEffect(() => {
    const fetchAgent = async () => {
      if (isEditing) {
        setLoading(true);
        setError(null);
        try {
          const response = await api.agents.getAgent(id);
          const agent = response.data;
          setFormData({
            name: agent.name,
            description: agent.description || '',
            llm_model: agent.llm_model,
            tts_model: agent.tts_model,
            tts_voice: agent.tts_voice,
            deepgram_model: agent.deepgram_model,
            system_prompt: agent.system_prompt,
            deepgram_config: agent.deepgram_config || {
              utterance_end_ms: '1000',
              endpointing: '1500',
              filler_words: true
            },
            silence_timeout_seconds: agent.silence_timeout_seconds,
            silence_prompt_text: agent.silence_prompt_text || '',
            is_active: agent.is_active,
            signalwire_phone_number: agent.signalwire_phone_number || ''
          });
        } catch (err) {
          console.error("Failed to fetch agent:", err);
          setError("Failed to load agent details. Please try again.");
          toast({
            title: "Error",
            description: "Failed to load agent details.",
            variant: "destructive",
          });
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };
    fetchAgent();
  }, [id, isEditing, toast]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDeepgramConfigChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      deepgram_config: {
        ...prev.deepgram_config,
        [field]: value
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      if (isEditing) {
        await api.agents.updateAgent(id, formData);
        toast({
          title: "Agent Updated",
          description: "Agent configuration has been saved successfully.",
        });
      } else {
        await api.agents.createAgent(formData);
        toast({
          title: "Agent Created",
          description: "New agent has been created successfully.",
        });
      }
      navigate('/agents');
    } catch (err) {
      console.error("Failed to save agent:", err);
      const errorMessage = getErrorMessage(err, "Failed to save agent details.");
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = () => {
    alert('Test call functionality would be implemented here. This would simulate a call with the current agent configuration.');
  };

  if (loading && isEditing) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-[60vh]">
        <div className="w-16 h-16 bg-brand-violet/10 rounded-3xl flex items-center justify-center animate-pulse mb-4">
          <Cpu className="w-8 h-8 text-brand-violet animate-spin" />
        </div>
        <p className="text-white font-bold tracking-tight animate-pulse underline decoration-brand-violet decoration-2 underline-offset-4">Accessing Agent Core...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-reveal max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="flex items-center space-x-6">
          <Button variant="ghost" size="icon" className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl text-gray-400 hover:text-white hover:bg-white/10 transition-all" asChild>
            <Link to="/agents">
              <ArrowLeft className="w-6 h-6" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              {isEditing ? 'Agent Tuning' : 'Agent Initialization'}
            </h1>
            <p className="text-gray-400 font-medium">
              {isEditing ? `Refining ${formData.name}'s performance parameters.` : 'Architecting a new high-performance AI entity.'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={handleTest} disabled={!formData.name} className="h-12 px-6 rounded-2xl border-white/10 text-white bg-white/5 hover:bg-white/10 hover:border-brand-violet/50 font-bold transition-all">
            <TestTube className="w-5 h-5 mr-3 text-brand-violet" />
            Unit Test
          </Button>
          <Button
            type="submit"
            form="agent-form"
            disabled={isSaving || !formData.name}
            className="h-12 px-8 bg-brand-violet hover:bg-brand-violet/90 text-white rounded-2xl shadow-lg shadow-brand-violet/20 font-bold transition-all active:scale-[0.98]"
          >
            {isSaving ? (
              <>
                <div className="w-5 h-5 mr-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-3" />
                {isEditing ? 'Save Parameters' : 'Deploy Agent'}
              </>
            )}
          </Button>
        </div>
      </div>

      <form id="agent-form" onSubmit={handleSubmit}>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 h-auto p-1.5 bg-white/5 border border-white/10 rounded-[2rem] gap-2">
            <TabsTrigger value="basic" className="rounded-3xl py-3 font-bold transition-all data-[state=active]:bg-white data-[state=active]:text-brand-black shadow-lg">
              <Bot className="w-4 h-4 mr-2" />
              Identity
            </TabsTrigger>
            <TabsTrigger value="voice" className="rounded-3xl py-3 font-bold transition-all data-[state=active]:bg-brand-violet data-[state=active]:text-white shadow-lg">
              <Mic className="w-4 h-4 mr-2" />
              Vocal/AI
            </TabsTrigger>
            <TabsTrigger value="advanced" className="rounded-3xl py-3 font-bold transition-all data-[state=active]:bg-white data-[state=active]:text-brand-black shadow-lg">
              <SettingsIcon className="w-4 h-4 mr-2" />
              Neural
            </TabsTrigger>
            <TabsTrigger value="phone" className="rounded-3xl py-3 font-bold transition-all data-[state=active]:bg-white data-[state=active]:text-brand-black shadow-lg">
              <Phone className="w-4 h-4 mr-2" />
              Gateway
            </TabsTrigger>
          </TabsList>

          {/* Step Progress Indicator */}
          <div className="mt-6 mb-2">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                Step {currentStepIndex + 1} of {tabOrder.length}
              </span>
              <span className="text-[10px] font-bold text-brand-violet uppercase tracking-widest">
                {tabLabels[activeTab]}
              </span>
            </div>
            <div className="flex gap-2">
              {tabOrder.map((tab, i) => (
                <div
                  key={tab}
                  className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${i <= currentStepIndex
                      ? 'bg-brand-violet shadow-[0_0_8px_rgba(108,99,255,0.4)]'
                      : 'bg-white/10'
                    }`}
                />
              ))}
            </div>
          </div>

          <TabsContent value="basic" className="mt-8">
            <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden">
              <CardHeader className="p-10 pb-6">
                <CardTitle className="flex items-center space-x-3 text-2xl font-bold text-brand-black">
                  <Bot className="w-8 h-8 text-brand-violet" />
                  <span>Agent Core Identity</span>
                </CardTitle>
                <CardDescription className="text-base font-medium">
                  Establish the public face and status of your AI workforce.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-10 pt-0 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <Label htmlFor="name" className="text-xs font-bold uppercase tracking-widest text-gray-400">Registry Name *</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Senior Account Executive Sarah"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      className="h-14 border-gray-100 bg-gray-50 focus:bg-white rounded-2xl focus:border-brand-violet focus:ring-brand-violet font-bold transition-all"
                      required
                    />
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="status" className="text-xs font-bold uppercase tracking-widest text-gray-400">Deployment Status</Label>
                    <div className="flex items-center justify-between h-14 px-6 bg-gray-50 border border-gray-100 rounded-2xl">
                      <div className="flex items-center space-x-3">
                        <Switch
                          checked={formData.is_active}
                          onCheckedChange={(checked) => handleInputChange('is_active', checked)}
                          className="data-[state=checked]:bg-brand-violet"
                        />
                        <span className="font-bold text-sm text-brand-black">
                          Agent is {formData.is_active ? 'Active' : 'Standby'}
                        </span>
                      </div>
                      <Badge className={`border-0 uppercase tracking-widest text-[10px] h-6 px-3 font-bold ${formData.is_active ? 'bg-emerald-500/10 text-emerald-600' : 'bg-gray-200 text-gray-500'}`}>
                        {formData.is_active ? 'Deployed' : 'Parked'}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="description" className="text-xs font-bold uppercase tracking-widest text-gray-400">Operational Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe the specialized function, personality traits, and primary objectives of this agent..."
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    rows={4}
                    className="border-gray-100 bg-gray-50 focus:bg-white rounded-2xl focus:border-brand-violet focus:ring-brand-violet font-medium transition-all"
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="voice" className="mt-8 space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden">
                <CardHeader className="p-8">
                  <CardTitle className="flex items-center space-x-3 text-xl font-bold text-brand-black">
                    <Brain className="w-6 h-6 text-brand-violet" />
                    <span>Intelligence Lattice</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-8 pt-0 space-y-6">
                  <div className="space-y-3">
                    <Label className="text-xs font-bold uppercase tracking-widest text-gray-400">Logical Engine (LLM)</Label>
                    <Select value={formData.llm_model} onValueChange={(value) => handleInputChange('llm_model', value)}>
                      <SelectTrigger className="h-14 border-gray-100 bg-gray-50 rounded-2xl font-bold">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="rounded-2xl border-gray-100 shadow-xl">
                        {llmModels.map((model) => (
                          <SelectItem key={model.value} value={model.value} className="py-3 rounded-xl focus:bg-brand-violet/5">
                            {model.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-3">
                    <Label className="text-xs font-bold uppercase tracking-widest text-gray-400">Vocal Synthesizer (TTS)</Label>
                    <Select value={formData.tts_voice} onValueChange={(value) => handleInputChange('tts_voice', value)}>
                      <SelectTrigger className="h-14 border-gray-100 bg-gray-50 rounded-2xl font-bold">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="rounded-2xl border-gray-100 shadow-xl">
                        {ttsVoices.map((voice) => (
                          <SelectItem key={voice.value} value={voice.value} className="py-3 rounded-xl focus:bg-brand-violet/5">
                            {voice.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-3">
                    <Label className="text-xs font-bold uppercase tracking-widest text-gray-400">Auditory Processor (STT)</Label>
                    <Select value={formData.deepgram_model} onValueChange={(value) => handleInputChange('deepgram_model', value)}>
                      <SelectTrigger className="h-14 border-gray-100 bg-gray-50 rounded-2xl font-bold">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="rounded-2xl border-gray-100 shadow-xl">
                        {deepgramModels.map((model) => (
                          <SelectItem key={model.value} value={model.value} className="py-3 rounded-xl focus:bg-brand-violet/5">
                            {model.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden">
                <CardHeader className="p-8">
                  <CardTitle className="text-xl font-bold text-brand-black">Behavioral Directives</CardTitle>
                </CardHeader>
                <CardContent className="p-8 pt-0">
                  <div className="space-y-3">
                    <Label htmlFor="system_prompt" className="text-xs font-bold uppercase tracking-widest text-gray-400">System Instructions</Label>
                    <Textarea
                      id="system_prompt"
                      placeholder="You are a professional sales assistant..."
                      value={formData.system_prompt}
                      onChange={(e) => handleInputChange('system_prompt', e.target.value)}
                      rows={10}
                      className="border-gray-100 bg-gray-50 rounded-2xl font-mono text-xs p-5 focus:bg-white focus:border-brand-violet focus:ring-brand-violet transition-all"
                    />
                    <div className="flex items-center text-xs text-gray-400 bg-gray-50 p-3 rounded-xl mt-4">
                      <Zap className="w-4 h-4 mr-2 text-brand-violet" />
                      Prompt optimized for latency & semantic clarity.
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="advanced" className="mt-8">
            <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden">
              <CardHeader className="p-10 pb-6">
                <CardTitle className="text-2xl font-bold text-brand-black">Neural Fine-Tuning</CardTitle>
                <CardDescription className="text-base font-medium"> Calibrate timing and recognition for low-latency humanlike interaction.</CardDescription>
              </CardHeader>
              <CardContent className="p-10 pt-0 space-y-10">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                  <div className="space-y-6">
                    <h4 className="flex items-center text-sm font-bold uppercase tracking-wider text-brand-violet">
                      <Mic className="w-4 h-4 mr-2" />
                      Acoustic Thresholds
                    </h4>

                    <div className="space-y-2">
                      <Label htmlFor="utterance_end" className="text-xs font-bold text-gray-500 uppercase">Utterance End (ms)</Label>
                      <Input
                        id="utterance_end"
                        type="number"
                        value={formData.deepgram_config.utterance_end_ms}
                        onChange={(e) => handleDeepgramConfigChange('utterance_end_ms', e.target.value)}
                        className="h-12 border-gray-100 rounded-xl font-bold"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="endpointing" className="text-xs font-bold text-gray-500 uppercase">Neural Endpointing (ms)</Label>
                      <Input
                        id="endpointing"
                        type="number"
                        value={formData.deepgram_config.endpointing}
                        onChange={(e) => handleDeepgramConfigChange('endpointing', e.target.value)}
                        className="h-12 border-gray-100 rounded-xl font-bold"
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl border border-gray-100">
                      <Label className="font-bold text-sm text-brand-black">Syntactic Fillers</Label>
                      <Switch
                        checked={formData.deepgram_config.filler_words}
                        onCheckedChange={(checked) => handleDeepgramConfigChange('filler_words', checked)}
                        className="data-[state=checked]:bg-brand-violet"
                      />
                    </div>
                  </div>

                  <div className="space-y-6">
                    <h4 className="flex items-center text-sm font-bold uppercase tracking-wider text-brand-violet">
                      <ShieldCheck className="w-4 h-4 mr-2" />
                      Engagement Failsafe
                    </h4>

                    <div className="space-y-2">
                      <Label htmlFor="silence_timeout" className="text-xs font-bold text-gray-500 uppercase">Silence Deadline (seconds)</Label>
                      <Input
                        id="silence_timeout"
                        type="number"
                        value={formData.silence_timeout_seconds}
                        onChange={(e) => handleInputChange('silence_timeout_seconds', parseInt(e.target.value) || 7)}
                        className="h-12 border-gray-100 rounded-xl font-bold"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="silence_prompt" className="text-xs font-bold text-gray-500 uppercase">Re-engagement Prompt</Label>
                      <Textarea
                        id="silence_prompt"
                        placeholder="I'm still here if you have any questions!"
                        value={formData.silence_prompt_text}
                        onChange={(e) => handleInputChange('silence_prompt_text', e.target.value)}
                        rows={3}
                        className="border-gray-100 rounded-xl font-medium"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="phone" className="mt-8">
            <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden">
              <CardHeader className="p-10 pb-6">
                <CardTitle className="flex items-center space-x-3 text-2xl font-bold text-brand-black">
                  <Phone className="w-8 h-8 text-brand-violet" />
                  <span>Connectivity Gateway</span>
                </CardTitle>
                <CardDescription className="text-base font-medium">Link this agent to your global communication infrastructure.</CardDescription>
              </CardHeader>
              <CardContent className="p-10 pt-0 space-y-8">
                <div className="space-y-3 max-w-xl">
                  <Label htmlFor="phone_number" className="text-xs font-bold uppercase tracking-widest text-gray-400">Assigned Inbound Number</Label>
                  <Input
                    id="phone_number"
                    placeholder="+1 (888) VOICE-AI"
                    value={formData.signalwire_phone_number}
                    onChange={(e) => handleInputChange('signalwire_phone_number', e.target.value)}
                    className="h-14 border-gray-100 bg-gray-50 rounded-2xl font-bold text-lg"
                  />
                  <p className="text-sm text-gray-500 font-medium">
                    Numbers can be dynamically routed through the SignalWire provisioning system.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
                  <div className="p-6 bg-brand-violet/5 rounded-3xl border border-brand-violet/10">
                    <h4 className="font-bold text-brand-black mb-2 flex items-center">
                      <div className="w-6 h-6 bg-brand-violet text-white rounded-full flex items-center justify-center text-[10px] mr-2">1</div>
                      Provision
                    </h4>
                    <p className="text-xs text-gray-500 font-medium leading-relaxed">Secure numbers through your cloud dashboard.</p>
                  </div>
                  <div className="p-6 bg-brand-violet/5 rounded-3xl border border-brand-violet/10">
                    <h4 className="font-bold text-brand-black mb-2 flex items-center">
                      <div className="w-6 h-6 bg-brand-violet text-white rounded-full flex items-center justify-center text-[10px] mr-2">2</div>
                      Redirect
                    </h4>
                    <p className="text-xs text-gray-500 font-medium leading-relaxed">Point webhooks to the neural interface endpoint.</p>
                  </div>
                  <div className="p-6 bg-brand-violet/5 rounded-3xl border border-brand-violet/10">
                    <h4 className="font-bold text-brand-black mb-2 flex items-center">
                      <div className="w-6 h-6 bg-brand-violet text-white rounded-full flex items-center justify-center text-[10px] mr-2">3</div>
                      Execute
                    </h4>
                    <p className="text-xs text-gray-500 font-medium leading-relaxed">Run a diagnostic unit test before scaling to production.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Next / Previous Navigation */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/5">
          <Button
            type="button"
            variant="ghost"
            onClick={goPrev}
            disabled={isFirstStep}
            className={`h-14 px-8 rounded-2xl font-bold text-sm transition-all ${isFirstStep
                ? 'opacity-30 cursor-not-allowed text-gray-600'
                : 'text-white bg-white/5 border border-white/10 hover:bg-white/10 hover:border-brand-violet/50'
              }`}
          >
            <ChevronLeft className="w-5 h-5 mr-2" />
            Previous: {!isFirstStep ? tabLabels[tabOrder[currentStepIndex - 1]] : ''}
          </Button>

          {isLastStep ? (
            <Button
              type="submit"
              disabled={isSaving || !formData.name}
              className="h-14 px-10 bg-brand-violet hover:bg-brand-violet/90 text-white rounded-2xl shadow-lg shadow-brand-violet/20 font-bold text-sm transition-all active:scale-[0.98]"
            >
              {isSaving ? (
                <>
                  <div className="w-5 h-5 mr-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Deploying...
                </>
              ) : (
                <>
                  <Check className="w-5 h-5 mr-2" />
                  {isEditing ? 'Save Parameters' : 'Deploy Agent'}
                </>
              )}
            </Button>
          ) : (
            <Button
              type="button"
              onClick={goNext}
              className="h-14 px-8 bg-brand-violet hover:bg-brand-violet/90 text-white rounded-2xl shadow-lg shadow-brand-violet/20 font-bold text-sm transition-all active:scale-[0.98]"
            >
              Next: {tabLabels[tabOrder[currentStepIndex + 1]]}
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          )}
        </div>
      </form>
    </div>
  );
};

export default AgentForm;

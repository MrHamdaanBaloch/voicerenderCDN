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
  TestTube
} from 'lucide-react';
import api from '../../services/api'; // Import the API service
import { useToast } from '../../hooks/use-toast'; // Import useToast

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
    tts_voice: 'Fritz-PlayAI', // Changed default voice to match backend
    deepgram_model: 'nova-2-phonecall',
    system_prompt: 'You are a helpful, professional, and concise AI assistant. Respond naturally, like a human, keeping your responses under 20 words. Maintain a positive and engaging tone, and always strive to provide value to the user.', // Updated default prompt
    deepgram_config: {
      utterance_end_ms: '1000',
      endpointing: '1500',
      filler_words: true
    },
    silence_timeout_seconds: 7, // Changed default timeout
    silence_prompt_text: "Are you still there? How can I help?", // Updated default prompt
    is_active: false,
    signalwire_phone_number: ''
  });

  const [isSaving, setIsSaving] = useState(false);
  const [loading, setLoading] = useState(true); // Add loading state
  const [error, setError] = useState(null); // Add error state
  const [activeTab, setActiveTab] = useState('basic');

  // Data for dropdowns (can be fetched from API if dynamic)
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
        setLoading(false); // No loading needed for new agent form
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
    
    // Mock save delay
    setTimeout(() => {
      console.log('Saving agent:', formData);
      setIsSaving(false);
      navigate('/agents');
    }, 1500);
  };

  const handleTest = () => {
    alert('Test call functionality would be implemented here. This would simulate a call with the current agent configuration.');
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/agents">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Agents
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isEditing ? 'Edit Agent' : 'Create New Agent'}
            </h1>
            <p className="text-gray-500">
              {isEditing ? 'Update your AI agent configuration' : 'Configure your new AI calling agent'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={handleTest} disabled={!formData.name}>
            <TestTube className="w-4 h-4 mr-2" />
            Test Agent
          </Button>
          <Button 
            type="submit" 
            form="agent-form"
            disabled={isSaving || !formData.name}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {isEditing ? 'Update Agent' : 'Create Agent'}
              </>
            )}
          </Button>
        </div>
      </div>

      <form id="agent-form" onSubmit={handleSubmit}>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="basic" className="flex items-center space-x-2">
              <Bot className="w-4 h-4" />
              <span>Basic Info</span>
            </TabsTrigger>
            <TabsTrigger value="voice" className="flex items-center space-x-2">
              <Mic className="w-4 h-4" />
              <span>Voice & AI</span>
            </TabsTrigger>
            <TabsTrigger value="advanced" className="flex items-center space-x-2">
              <SettingsIcon className="w-4 h-4" />
              <span>Advanced</span>
            </TabsTrigger>
            <TabsTrigger value="phone" className="flex items-center space-x-2">
              <Phone className="w-4 h-4" />
              <span>Phone Setup</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Bot className="w-5 h-5" />
                  <span>Agent Information</span>
                </CardTitle>
                <CardDescription>
                  Basic details about your AI calling agent
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Agent Name *</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Sales Assistant Sarah"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="status">Status</Label>
                    <div className="flex items-center space-x-2 pt-2">
                      <Switch
                        checked={formData.is_active}
                        onCheckedChange={(checked) => handleInputChange('is_active', checked)}
                      />
                      <Label className="text-sm">
                        Agent is {formData.is_active ? 'Active' : 'Inactive'}
                      </Label>
                      <Badge variant={formData.is_active ? 'default' : 'secondary'}>
                        {formData.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe what this agent does, its personality, and use cases..."
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    rows={4}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="voice" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Brain className="w-5 h-5" />
                    <span>AI Model Configuration</span>
                  </CardTitle>
                  <CardDescription>
                    Choose the AI models for speech and language processing
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="llm_model">Language Model</Label>
                    <Select value={formData.llm_model} onValueChange={(value) => handleInputChange('llm_model', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {llmModels.map((model) => (
                          <SelectItem key={model.value} value={model.value}>
                            {model.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="deepgram_model">Speech Recognition</Label>
                    <Select value={formData.deepgram_model} onValueChange={(value) => handleInputChange('deepgram_model', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {deepgramModels.map((model) => (
                          <SelectItem key={model.value} value={model.value}>
                            {model.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="tts_voice">Voice</Label>
                    <Select value={formData.tts_voice} onValueChange={(value) => handleInputChange('tts_voice', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ttsVoices.map((voice) => (
                          <SelectItem key={voice.value} value={voice.value}>
                            {voice.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>System Prompt</CardTitle>
                  <CardDescription>
                    Define your agent's personality and behavior
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Label htmlFor="system_prompt">Instructions</Label>
                    <Textarea
                      id="system_prompt"
                      placeholder="You are a professional sales assistant. Be friendly, helpful, and always try to..."
                      value={formData.system_prompt}
                      onChange={(e) => handleInputChange('system_prompt', e.target.value)}
                      rows={8}
                      className="font-mono text-sm"
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Advanced Settings</CardTitle>
                <CardDescription>
                  Fine-tune speech recognition and silence handling
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">Speech Recognition Settings</h4>
                    
                    <div className="space-y-2">
                      <Label htmlFor="utterance_end">Utterance End (ms)</Label>
                      <Input
                        id="utterance_end"
                        type="number"
                        placeholder="1000"
                        value={formData.deepgram_config.utterance_end_ms}
                        onChange={(e) => handleDeepgramConfigChange('utterance_end_ms', e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="endpointing">Endpointing (ms)</Label>
                      <Input
                        id="endpointing"
                        type="number"
                        placeholder="1500"
                        value={formData.deepgram_config.endpointing}
                        onChange={(e) => handleDeepgramConfigChange('endpointing', e.target.value)}
                      />
                    </div>

                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={formData.deepgram_config.filler_words}
                        onCheckedChange={(checked) => handleDeepgramConfigChange('filler_words', checked)}
                      />
                      <Label className="text-sm">Process filler words (um, uh, etc.)</Label>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">Silence Handling</h4>
                    
                    <div className="space-y-2">
                      <Label htmlFor="silence_timeout">Silence Timeout (seconds)</Label>
                      <Input
                        id="silence_timeout"
                        type="number"
                        placeholder="30"
                        value={formData.silence_timeout_seconds}
                        onChange={(e) => handleInputChange('silence_timeout_seconds', parseInt(e.target.value) || 30)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="silence_prompt">Silence Prompt Text</Label>
                      <Textarea
                        id="silence_prompt"
                        placeholder="I'm still here if you have any questions!"
                        value={formData.silence_prompt_text}
                        onChange={(e) => handleInputChange('silence_prompt_text', e.target.value)}
                        rows={3}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="phone" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Phone className="w-5 h-5" />
                  <span>Phone Number Configuration</span>
                </CardTitle>
                <CardDescription>
                  Assign a phone number for incoming calls (optional)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="phone_number">SignalWire Phone Number</Label>
                  <Input
                    id="phone_number"
                    placeholder="+1-555-0123"
                    value={formData.signalwire_phone_number}
                    onChange={(e) => handleInputChange('signalwire_phone_number', e.target.value)}
                  />
                  <p className="text-sm text-gray-500">
                    Leave empty if this agent will only make outbound calls
                  </p>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Phone Number Setup</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Purchase numbers through your SignalWire dashboard</li>
                    <li>• Configure webhooks to point to your AI Caller endpoint</li>
                    <li>• Test the setup with a test call before going live</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </form>
    </div>
  );
};

export default AgentForm;

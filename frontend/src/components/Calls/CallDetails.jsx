import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  ArrowLeft,
  PhoneCall,
  Clock,
  CalendarDays,
  Bot,
  User,
  MessageSquareText,
  Download,
  Activity,
  Zap,
  ShieldCheck,
  Globe
} from 'lucide-react';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';

const CallDetails = () => {
  const { id } = useParams();
  const [call, setCall] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { toast } = useToast();

  const fetchCallDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.calls.getCallDetails(id);
      setCall(response.data);
    } catch (err) {
      console.error("Failed to fetch call details:", err);
      setError("Failed to access secure transmission logs.");
      toast({
        title: "Security Alert",
        description: "Failed to load call details.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [id, toast]);

  useEffect(() => {
    fetchCallDetails();
  }, [fetchCallDetails]);

  const formatDuration = (seconds) => {
    if (seconds === null || seconds === undefined) return '0s';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`;
  };

  if (loading) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-[60vh]">
        <div className="w-16 h-16 bg-white/5 rounded-3xl flex items-center justify-center animate-pulse mb-4 border border-white/10">
          <Activity className="w-8 h-8 text-brand-violet animate-pulse" />
        </div>
        <p className="text-white font-bold tracking-tight animate-pulse underline decoration-brand-violet decoration-2 underline-offset-4">Decrypting Transmission...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-6">
          <ShieldCheck className="w-10 h-10 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Access Denied</h1>
        <p className="text-gray-400 mb-8 max-w-md">{error}</p>
        <Button onClick={fetchCallDetails} className="bg-brand-violet hover:bg-brand-violet/90 rounded-xl px-8 h-12 font-bold">
          Re-authenticate
        </Button>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mb-6">
          <PhoneCall className="w-10 h-10 text-gray-500" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Null Stream</h1>
        <p className="text-gray-400 mb-8 max-w-sm">The requested transmission packet could not be located in the archive.</p>
        <Button asChild className="bg-white text-brand-black hover:bg-gray-100 rounded-xl px-8 h-12 font-bold">
          <Link to="/calls">Back to Archive</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-reveal max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="flex items-center space-x-6">
          <Button variant="ghost" size="icon" className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl text-gray-400 hover:text-white hover:bg-white/10 transition-all" asChild>
            <Link to="/calls">
              <ArrowLeft className="w-6 h-6" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Transmission Analysis</h1>
            <p className="text-gray-400 font-medium font-mono text-sm">Sequence ID: {call.id?.slice(0, 12)}...</p>
          </div>
        </div>
        {call.audio_url && (
          <Button asChild className="h-12 px-6 bg-brand-violet hover:bg-brand-violet/90 text-white rounded-2xl shadow-lg shadow-brand-violet/20 font-bold transition-all active:scale-[0.98]">
            <a href={call.audio_url} download>
              <Download className="w-5 h-5 mr-3" />
              Export Audio
            </a>
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Side: Metadata Card */}
        <div className="lg:col-span-1 space-y-8">
          <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden">
            <CardHeader className="p-8 pb-4">
              <CardTitle className="flex items-center space-x-3 text-xl font-bold text-brand-black">
                <Zap className="w-6 h-6 text-brand-violet" />
                <span>Packet Meta</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-8 pt-0 space-y-6">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Operator</p>
                <p className="text-sm font-bold text-brand-black flex items-center">
                  <Bot className="w-4 h-4 mr-2 text-brand-violet" />
                  {call.agent?.name || 'Unknown Unit'}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Status</p>
                  <Badge className={`border-0 uppercase tracking-widest text-[9px] h-5 px-2 font-bold ${call.status === 'completed' ? 'bg-emerald-500/10 text-emerald-600' :
                      call.status === 'in_progress' ? 'bg-brand-violet/10 text-brand-violet' :
                        'bg-gray-200 text-gray-500'
                    }`}>
                    {call.status?.replace('_', ' ')}
                  </Badge>
                </div>
                <div className="space-y-1 text-right">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Runtime</p>
                  <p className="text-sm font-bold text-brand-black">{formatDuration(call.duration_seconds)}</p>
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-gray-100 text-xs">
                <div className="flex justify-between items-center bg-gray-50 p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 font-bold uppercase tracking-tighter flex items-center"><Globe className="w-3 h-3 mr-1.5" /> Origin</span>
                  <span className="font-bold text-brand-black">{call.from_number || 'Secure'}</span>
                </div>
                <div className="flex justify-between items-center bg-gray-50 p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-400 font-bold uppercase tracking-tighter flex items-center"><User className="w-3 h-3 mr-1.5" /> Destination</span>
                  <span className="font-bold text-brand-black">{call.to_number || 'Secure'}</span>
                </div>
              </div>

              <div className="pt-4 text-[10px] font-medium text-gray-400 leading-relaxed italic bg-blue-50/50 p-4 rounded-2xl">
                Checksum verified. Audio packet stored with AES-256 encryption.
              </div>
            </CardContent>
          </Card>

          <div className="p-8 bg-white/5 border border-white/10 rounded-[2.5rem]">
            <h4 className="text-sm font-bold text-white mb-4 flex items-center">
              <Activity className="w-4 h-4 mr-2 text-brand-violet" />
              Timeline Evolution
            </h4>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-violet mt-1.5 shadow-[0_0_10px_rgba(108,99,255,0.8)]"></div>
                <div>
                  <p className="text-[10px] font-bold text-gray-500 uppercase">Initialization</p>
                  <p className="text-xs text-white font-medium">{new Date(call.start_time).toLocaleTimeString()}</p>
                </div>
              </div>
              {call.end_time && (
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5"></div>
                  <div>
                    <p className="text-[10px] font-bold text-gray-500 uppercase">Termination</p>
                    <p className="text-xs text-white font-medium">{new Date(call.end_time).toLocaleTimeString()}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Transcript Card */}
        <div className="lg:col-span-2">
          <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden flex flex-col h-full min-h-[600px]">
            <CardHeader className="p-10 pb-6 border-b border-gray-100">
              <CardTitle className="flex items-center space-x-3 text-2xl font-bold text-brand-black">
                <MessageSquareText className="w-8 h-8 text-brand-violet" />
                <span>Signal Transcript</span>
              </CardTitle>
              <CardDescription className="text-base font-medium">Real-time reconstruction of the voice stream dialog.</CardDescription>
            </CardHeader>
            <CardContent className="p-10 pt-8 flex-1 overflow-y-auto max-h-[700px] scrollbar-hide">
              {call.transcripts && call.transcripts.length > 0 ? (
                <div className="space-y-8">
                  {call.transcripts.map((transcript, index) => (
                    <div key={transcript.id || index} className={`flex ${transcript.speaker === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] group`}>
                        <div className={`flex items-center mb-2 px-1 ${transcript.speaker === 'user' ? 'justify-end' : 'justify-start'}`}>
                          {transcript.speaker !== 'user' && <Bot className="w-3 h-3 mr-2 text-brand-violet" />}
                          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                            {transcript.speaker === 'user' ? 'Human Contact' : (call.agent?.name || 'AI Operative')}
                          </span>
                          {transcript.speaker === 'user' && <User className="w-3 h-3 ml-2 text-gray-400" />}
                        </div>
                        <div className={`p-5 rounded-3xl shadow-sm transition-all hover:shadow-md ${transcript.speaker === 'user'
                            ? 'bg-brand-black text-white rounded-tr-none'
                            : 'bg-gray-50 text-brand-black border border-gray-100 rounded-tl-none'
                          }`}>
                          <p className="text-sm font-medium leading-relaxed">{transcript.text}</p>
                        </div>
                        <p className="text-[9px] font-bold text-gray-300 mt-2 px-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          SENT AT {new Date(transcript.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                    <Activity className="w-8 h-8 text-gray-300" />
                  </div>
                  <p className="text-gray-400 font-bold">Waiting for transcript propagation...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CallDetails;

// Mock data for AI Calling Agent SaaS Platform

export const mockOrganization = {
  id: "org-123e4567-e89b-12d3-a456-426614174000",
  name: "TechCorp Solutions",
  slug: "techcorp-solutions",
  plan_id: "plan-pro-001",
  stripe_customer_id: "cus_NffrFeUfNV2Hib",
  created_at: "2024-01-15T08:30:00Z",
  updated_at: "2024-07-01T14:20:00Z"
};

export const mockPlan = {
  id: "plan-pro-001",
  name: "Pro Plan",
  description: "Advanced AI calling features for growing businesses",
  price_monthly: 99.99,
  price_annual: 999.99,
  features: {
    max_agents: 10,
    max_calls_per_month: 5000,
    custom_voices: true,
    api_access: true,
    analytics: true
  },
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-06-01T00:00:00Z"
};

export const mockUser = {
  id: "user-123e4567-e89b-12d3-a456-426614174001",
  email: "john.doe@techcorp.com",
  first_name: "John",
  last_name: "Doe",
  organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
  role: "admin",
  is_active: true,
  created_at: "2024-01-15T08:30:00Z",
  updated_at: "2024-07-01T14:20:00Z"
};

export const mockAgents = [
  {
    id: "agent-001",
    organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
    name: "Sales Assistant Sarah",
    description: "Friendly and professional sales agent specialized in lead qualification and appointment setting. Trained on company product knowledge and pricing.",
    llm_model: "llama3-8b-8192",
    tts_model: "playai-tts",
    tts_voice: "Sarah-PlayAI",
    deepgram_model: "nova-2-phonecall",
    system_prompt: "You are Sarah, a professional sales assistant for TechCorp Solutions. You help qualify leads, answer product questions, and schedule appointments with our sales team. Be friendly, helpful, and knowledgeable about our software solutions.",
    deepgram_config: {
      utterance_end_ms: "1000",
      endpointing: "1500",
      filler_words: true
    },
    silence_timeout_seconds: 30,
    silence_prompt_text: "I'm still here if you have any questions!",
    is_active: true,
    signalwire_phone_number: "+1-555-0101",
    created_at: "2024-02-01T10:00:00Z",
    updated_at: "2024-07-15T16:30:00Z"
  },
  {
    id: "agent-002",
    organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
    name: "Support Specialist Mike",
    description: "Technical support agent for customer service inquiries, troubleshooting, and account assistance. Patient and detail-oriented.",
    llm_model: "llama3-8b-8192",
    tts_model: "playai-tts",
    tts_voice: "Mike-PlayAI",
    deepgram_model: "nova-2-phonecall",
    system_prompt: "You are Mike, a technical support specialist for TechCorp Solutions. Help customers with technical issues, account problems, and general inquiries. Be patient, thorough, and always try to resolve issues completely.",
    deepgram_config: {
      utterance_end_ms: "1200",
      endpointing: "1800",
      filler_words: true
    },
    silence_timeout_seconds: 45,
    silence_prompt_text: "Take your time, I'm here to help with any questions.",
    is_active: true,
    signalwire_phone_number: "+1-555-0102",
    created_at: "2024-02-15T14:00:00Z",
    updated_at: "2024-07-10T11:45:00Z"
  },
  {
    id: "agent-003",
    organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
    name: "Appointment Scheduler Emma",
    description: "Specialized agent for booking appointments, managing calendars, and handling scheduling conflicts. Efficient and organized.",
    llm_model: "llama3-8b-8192",
    tts_model: "playai-tts",
    tts_voice: "Emma-PlayAI",
    deepgram_model: "nova-2-phonecall",
    system_prompt: "You are Emma, an appointment scheduling specialist. Help customers book appointments, check availability, and manage scheduling requests. Be organized and always confirm details clearly.",
    deepgram_config: {
      utterance_end_ms: "900",
      endpointing: "1200",
      filler_words: false
    },
    silence_timeout_seconds: 25,
    silence_prompt_text: "Let me check the calendar for you.",
    is_active: false,
    signalwire_phone_number: null,
    created_at: "2024-03-01T09:30:00Z",
    updated_at: "2024-07-05T13:15:00Z"
  }
];

export const mockCalls = [
  {
    id: "call-001",
    agent_id: "agent-001",
    user_id: "user-123e4567-e89b-12d3-a456-426614174001",
    organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
    call_sid: "CA1234567890abcdef1234567890abcdef",
    from_number: "+1-555-0199",
    to_number: "+1-555-0101",
    start_time: "2024-07-20T14:30:00Z",
    end_time: "2024-07-20T14:35:30Z",
    duration_seconds: 330,
    status: "completed",
    transcript_url: "https://s3.amazonaws.com/transcripts/call-001.txt",
    audio_url: "https://s3.amazonaws.com/audio/call-001.mp3",
    cost: 2.45,
    call_metadata: {
      outcome: "qualified_lead",
      sentiment: "positive",
      appointment_scheduled: true
    }
  },
  {
    id: "call-002",
    agent_id: "agent-002",
    user_id: "user-123e4567-e89b-12d3-a456-426614174001",
    organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
    call_sid: "CA1234567890abcdef1234567890abcde2",
    from_number: "+1-555-0288",
    to_number: "+1-555-0102",
    start_time: "2024-07-20T15:45:00Z",
    end_time: "2024-07-20T16:02:15Z",
    duration_seconds: 1035,
    status: "completed",
    transcript_url: "https://s3.amazonaws.com/transcripts/call-002.txt",
    audio_url: "https://s3.amazonaws.com/audio/call-002.mp3",
    cost: 4.20,
    call_metadata: {
      outcome: "issue_resolved",
      sentiment: "neutral",
      ticket_created: false
    }
  },
  {
    id: "call-003",
    agent_id: "agent-001",
    user_id: "user-123e4567-e89b-12d3-a456-426614174001",
    organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
    call_sid: "CA1234567890abcdef1234567890abcde3",
    from_number: "+1-555-0377",
    to_number: "+1-555-0101",
    start_time: "2024-07-20T16:20:00Z",
    end_time: null,
    duration_seconds: null,
    status: "in_progress",
    transcript_url: null,
    audio_url: null,
    cost: null,
    call_metadata: {
      outcome: null,
      sentiment: "positive"
    }
  }
];

export const mockTranscripts = [
  {
    id: "transcript-001-001",
    call_id: "call-001",
    speaker: "agent",
    text: "Hello! This is Sarah from TechCorp Solutions. How are you doing today?",
    timestamp: "2024-07-20T14:30:05Z",
    duration: 3.2,
    confidence: 0.98
  },
  {
    id: "transcript-001-002",
    call_id: "call-001",
    speaker: "user",
    text: "Hi Sarah! I'm good, thanks. I received your call about the software demo?",
    timestamp: "2024-07-20T14:30:08Z",
    duration: 4.1,
    confidence: 0.95
  },
  {
    id: "transcript-001-003",
    call_id: "call-001",
    speaker: "agent",
    text: "Yes, exactly! I wanted to follow up on your interest in our CRM solution. Do you have a few minutes to discuss your current needs?",
    timestamp: "2024-07-20T14:30:12Z",
    duration: 5.8,
    confidence: 0.97
  }
];

export const mockAPIKeys = [
  {
    id: "key-001",
    organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
    key_hash: "sk_live_51H...",
    name: "Production API Key",
    created_at: "2024-06-01T10:00:00Z",
    expires_at: "2025-06-01T10:00:00Z",
    is_active: true,
    permissions: ["create_call", "read_calls", "read_agents", "update_agents"]
  },
  {
    id: "key-002",
    organization_id: "org-123e4567-e89b-12d3-a456-426614174000",
    key_hash: "sk_test_51H...",
    name: "Development API Key",
    created_at: "2024-07-01T15:30:00Z",
    expires_at: null,
    is_active: true,
    permissions: ["read_calls", "read_agents"]
  }
];

// Dashboard statistics mock data
export const mockDashboardStats = {
  totalCalls: 1247,
  successRate: 92.3,
  avgCallDuration: "4:23",
  activeCalls: 3,
  monthlyCallVolume: [
    { month: "Jan", calls: 180 },
    { month: "Feb", calls: 220 },
    { month: "Mar", calls: 185 },
    { month: "Apr", calls: 240 },
    { month: "May", calls: 200 },
    { month: "Jun", calls: 280 },
    { month: "Jul", calls: 142 }
  ],
  recentCalls: mockCalls.slice(0, 5)
};
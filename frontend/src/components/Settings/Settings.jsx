import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';
import {
    Settings as SettingsIcon, CreditCard, Zap, AlertTriangle,
    CheckCircle2, Loader2, Phone, Copy, TrendingUp, Globe
} from 'lucide-react';

const Settings = () => {
    const { user, refreshUser } = useAuth();
    const location = useLocation();
    const { toast } = useToast();
    const [isRecharging, setIsRecharging] = useState(false);
    const [rechargeAmount, setRechargeAmount] = useState(5);

    const totalFreeSeconds = 6000;
    const balanceSeconds = user?.balance_seconds ?? 0;
    const usedSeconds = Math.max(0, Math.min(totalFreeSeconds, totalFreeSeconds - balanceSeconds));
    const percentUsed = Math.min(100, (usedSeconds / totalFreeSeconds) * 100);
    const minutesLeft = (balanceSeconds / 60).toFixed(1);
    const dollarEquivalent = (balanceSeconds / 60 * 0.03).toFixed(2);

    useEffect(() => {
        const p = new URLSearchParams(location.search);
        if (p.get('recharge_success') === 'true') {
            toast({ title: 'Top Up Successful! ⚡', description: `$${p.get('amount')} added to your VoiceRender wallet.` });
            refreshUser?.();
            window.history.replaceState({}, '', window.location.pathname);
        } else if (p.get('recharge_cancelled') === 'true') {
            toast({ title: 'Cancelled', description: 'Payment was not processed.', variant: 'destructive' });
            window.history.replaceState({}, '', window.location.pathname);
        }
    }, [location, toast, refreshUser]);

    const handleRecharge = async () => {
        setIsRecharging(true);
        try {
            const res = await api.billing.createRechargeSession(rechargeAmount);
            if (res.data?.url) window.location.href = res.data.url;
        } catch {
            toast({ title: 'Checkout Failed', description: 'Could not initiate payment session.', variant: 'destructive' });
            setIsRecharging(false);
        }
    };

    const webhookUrl = `${process.env.REACT_APP_BACKEND_URL?.replace('/api/v1', '') || 'https://your-backend.com'}/incoming_twilio`;

    const copyWebhook = () => {
        navigator.clipboard.writeText(webhookUrl);
        toast({ title: 'Copied!', description: 'Webhook URL copied to clipboard.' });
    };

    return (
        <div className="space-y-8 animate-reveal max-w-4xl">
            {/* ── Page Header ── */}
            <div>
                <h1 className="text-2xl font-heading font-bold text-white tracking-tight">Billing & Settings</h1>
                <p className="text-sm text-zinc-600 mt-0.5">Manage your AI compute balance and carrier integrations.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* ── Wallet Card ── */}
                <div className="card-surface p-6 space-y-6">
                    <div className="flex items-center gap-3 pb-5 border-b border-white/[0.06]">
                        <div className="w-9 h-9 rounded-xl bg-violet-500/10 flex items-center justify-center">
                            <Zap className="w-4.5 h-4.5 text-violet-400" />
                        </div>
                        <div>
                            <p className="font-heading font-bold text-white text-sm">Compute Wallet</p>
                            <p className="text-[11px] text-zinc-600">Billed at $0.03/min — STT + LLM + TTS + Telephony</p>
                        </div>
                    </div>

                    {/* Balance Display */}
                    <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.05] space-y-4">
                        <div className="flex items-end justify-between">
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-600 mb-1">Available Balance</p>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-4xl font-heading font-bold text-white tracking-tight">{minutesLeft}</span>
                                    <span className="text-base font-semibold text-zinc-500">minutes</span>
                                </div>
                                <p className="text-[11px] text-zinc-700 mt-0.5">≈ ${dollarEquivalent} equivalent</p>
                            </div>
                            {balanceSeconds <= 0 && (
                                <div className="flex items-center gap-1 text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded-full text-[11px] font-bold">
                                    <AlertTriangle className="w-3 h-3" /> Empty
                                </div>
                            )}
                        </div>

                        {/* Progress bar */}
                        <div className="space-y-1.5">
                            <div className="flex justify-between text-[10px] font-semibold text-zinc-600">
                                <span>Free allocation used</span>
                                <span>{percentUsed.toFixed(0)}%</span>
                            </div>
                            <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                                <div
                                    className="h-full rounded-full transition-all duration-700"
                                    style={{
                                        width: `${percentUsed}%`,
                                        background: balanceSeconds <= 300
                                            ? 'linear-gradient(90deg, #F43F5E, #FB7185)'
                                            : 'linear-gradient(90deg, #7C3AED, #A78BFA)'
                                    }}
                                />
                            </div>
                            <p className="text-[10px] text-zinc-700">
                                {balanceSeconds > totalFreeSeconds
                                    ? 'Currently drawing from prepaid funds.'
                                    : 'Using your 100 free minutes allocation.'}
                            </p>
                        </div>
                    </div>

                    {/* Top-up amounts */}
                    <div className="space-y-3">
                        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-600">Add Prepaid Funds</p>
                        <div className="grid grid-cols-3 gap-2">
                            {[5, 10, 50].map((amount) => (
                                <button
                                    key={amount}
                                    onClick={() => setRechargeAmount(amount)}
                                    className={`h-12 rounded-xl font-bold text-sm border transition-all ${rechargeAmount === amount
                                            ? 'bg-violet-600 text-white border-violet-500 shadow-glow-violet'
                                            : 'border-white/[0.08] bg-white/[0.04] text-zinc-400 hover:text-white hover:bg-white/[0.07]'
                                        }`}
                                >
                                    ${amount}
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={handleRecharge}
                            disabled={isRecharging}
                            className="btn-primary w-full h-12 justify-center disabled:opacity-60"
                        >
                            {isRecharging
                                ? <><Loader2 className="w-4 h-4 animate-spin" /> Processing...</>
                                : <><CreditCard className="w-4 h-4" /> Secure Checkout (Stripe)</>
                            }
                        </button>
                    </div>
                </div>

                {/* ── BYOC Card ── */}
                <div className="card-surface p-6 space-y-6">
                    <div className="flex items-center gap-3 pb-5 border-b border-white/[0.06]">
                        <div className="w-9 h-9 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                            <Globe className="w-4.5 h-4.5 text-emerald-400" />
                        </div>
                        <div>
                            <p className="font-heading font-bold text-white text-sm">Bring Your Own Carrier</p>
                            <p className="text-[11px] text-zinc-600">Use existing Twilio numbers with VoiceRender AI</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <p className="text-[11px] text-zinc-500 leading-relaxed">
                            Paste this webhook URL into your <strong className="text-white">Twilio Console</strong> → Phone Numbers → Voice Configuration.
                        </p>

                        <div className="relative p-4 rounded-xl bg-black/30 border border-white/[0.07] group">
                            <p className="text-[9px] font-bold uppercase tracking-[0.15em] text-violet-400 mb-1.5">Twilio Webhook URL (POST)</p>
                            <code className="text-[11px] text-emerald-400 font-mono-ui break-all leading-relaxed">{webhookUrl}</code>
                            <button
                                onClick={copyWebhook}
                                className="absolute top-3 right-3 flex items-center gap-1 px-2 py-1 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-zinc-500 hover:text-white text-[10px] font-bold transition-all"
                            >
                                <Copy className="w-3 h-3" /> Copy
                            </button>
                        </div>

                        <ul className="space-y-3">
                            <li className="flex items-start gap-2.5 text-[12px] text-zinc-500">
                                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                                You pay Twilio directly for the number (~$1.15/mo) and minutes (~$0.0085/min inbound).
                            </li>
                            <li className="flex items-start gap-2.5 text-[12px] text-zinc-500">
                                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                                VoiceRender charges $0.03/min from your wallet — covers STT + LLM + TTS.
                            </li>
                            <li className="flex items-start gap-2.5 text-[12px] text-zinc-500">
                                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                                You can also import and manage Twilio numbers from the Numbers dashboard.
                            </li>
                        </ul>

                        <Link to="/phone-numbers" className="btn-ghost w-full justify-center h-10">
                            <Phone className="w-3.5 h-3.5" /> Go to Phone Numbers
                        </Link>
                    </div>
                </div>
            </div>

            {/* Plan info */}
            <div className="card-surface p-6">
                <div className="flex items-center gap-3 mb-5">
                    <TrendingUp className="w-4 h-4 text-violet-400" />
                    <h3 className="font-heading font-bold text-white text-sm">Current Plan</h3>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                        ['Free Tier', '100 min free', 'Active'],
                        ['Growth Plan', '$0.03 / min', 'Pay-as-you-go'],
                        ['Agents', 'Unlimited', 'All plans'],
                        ['Numbers', 'Unlimited', 'Buy or import'],
                    ].map(([title, value, note]) => (
                        <div key={title} className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.04]">
                            <p className="text-[9px] font-bold uppercase tracking-[0.15em] text-zinc-700 mb-1">{title}</p>
                            <p className="text-sm font-bold text-white">{value}</p>
                            <p className="text-[10px] text-zinc-600 mt-0.5">{note}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Settings;

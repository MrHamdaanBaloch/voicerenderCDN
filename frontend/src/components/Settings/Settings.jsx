import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';
import { Settings as SettingsIcon, CreditCard, Zap, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';

const Settings = () => {
    const { user, refreshUser } = useAuth();
    const location = useLocation();
    const { toast } = useToast();
    const [isRecharging, setIsRecharging] = useState(false);
    const [rechargeAmount, setRechargeAmount] = useState(5);

    // 6000 seconds = 100 minutes.
    const totalFreeSeconds = 6000;
    const balanceSeconds = user?.balance_seconds ?? 0;
    const usedSeconds = Math.max(0, totalFreeSeconds - balanceSeconds);
    const percentUsed = Math.min(100, (usedSeconds / totalFreeSeconds) * 100);

    const formattedMinutesLeft = (balanceSeconds / 60).toFixed(1);

    useEffect(() => {
        // Handle Stripe redirect params
        const searchParams = new URLSearchParams(location.search);
        const rechargeSuccess = searchParams.get('recharge_success');
        const rechargeCancelled = searchParams.get('recharge_cancelled');
        const amount = searchParams.get('amount');

        if (rechargeSuccess === 'true') {
            toast({
                title: "Recharge Successful! ⚡",
                description: `$${amount} has been added to your VoiceRender AI wallet.`,
            });
            // Refresh the user data to get the new balance
            if (refreshUser) refreshUser();

            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
        } else if (rechargeCancelled === 'true') {
            toast({
                title: "Recharge Cancelled",
                description: "Your payment was not processed.",
                variant: "destructive",
            });
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }, [location, toast, refreshUser]);

    const handleRecharge = async () => {
        setIsRecharging(true);
        try {
            const response = await api.billing.createRechargeSession(rechargeAmount);
            if (response.data && response.data.url) {
                window.location.href = response.data.url;
            }
        } catch (err) {
            toast({
                title: "Checkout Failed",
                description: "Could not initiate secure checkout session.",
                variant: "destructive",
            });
            setIsRecharging(false);
        }
    };

    return (
        <div className="p-8 max-w-5xl mx-auto space-y-8 animate-reveal">
            <div className="flex items-center space-x-4 mb-8">
                <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center">
                    <SettingsIcon className="w-6 h-6 text-brand-violet" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Account & Billing</h1>
                    <p className="text-gray-400 font-medium">Manage your VoiceRender AI compute usage and top up your wallet.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <Card className="border-0 shadow-2xl bg-white rounded-[2rem] overflow-hidden">
                    <CardHeader className="p-8 pb-4">
                        <CardTitle className="flex items-center space-x-3 text-xl font-bold text-brand-black">
                            <Zap className="w-6 h-6 text-brand-violet" />
                            <span>Compute Wallet</span>
                        </CardTitle>
                        <CardDescription className="text-base font-medium">
                            Your real-time AI conversation balance. Calls are billed at $0.03/min.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="p-8 pt-0 space-y-6">
                        <div className="bg-gray-50 border border-gray-100 p-6 rounded-2xl">
                            <div className="flex justify-between items-end mb-4">
                                <div>
                                    <p className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-1">Available Balance</p>
                                    <div className="flex items-baseline space-x-2">
                                        <span className="text-4xl font-extrabold text-brand-black">{formattedMinutesLeft}</span>
                                        <span className="text-lg font-bold text-gray-500">minutes</span>
                                    </div>
                                </div>
                                {balanceSeconds <= 0 && (
                                    <div className="flex items-center text-red-500 bg-red-50 px-3 py-1 rounded-full text-xs font-bold">
                                        <AlertTriangle className="w-3 h-3 mr-1" />
                                        Empty
                                    </div>
                                )}
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between text-xs font-bold text-gray-500">
                                    <span>Usage Progress</span>
                                    {balanceSeconds > totalFreeSeconds ? (
                                        <span className="text-brand-violet">+ {((balanceSeconds - totalFreeSeconds) / 60).toFixed(0)} prepaid mins</span>
                                    ) : (
                                        <span>{percentUsed.toFixed(0)}% used</span>
                                    )}
                                </div>
                                <Progress
                                    value={percentUsed}
                                    className="h-3 bg-gray-200"
                                    indicatorClassName={balanceSeconds <= 300 ? "bg-red-500" : "bg-brand-violet"}
                                />
                                <p className="text-xs text-gray-400 mt-2 font-medium">
                                    {balanceSeconds > totalFreeSeconds
                                        ? "You are currently using Prepaid Funds."
                                        : "You are currently using your 100 Free Minutes allocation."}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                    <CardFooter className="p-8 pt-0 flex flex-col items-stretch space-y-4">
                        <h4 className="text-sm font-bold text-brand-black uppercase tracking-wider">Add Prepaid Funds</h4>
                        <div className="grid grid-cols-3 gap-3">
                            {[5, 10, 50].map((amount) => (
                                <Button
                                    key={amount}
                                    type="button"
                                    variant={rechargeAmount === amount ? "default" : "outline"}
                                    onClick={() => setRechargeAmount(amount)}
                                    className={`h-12 rounded-xl font-bold text-lg ${rechargeAmount === amount
                                            ? "bg-brand-violet hover:bg-brand-violet/90 text-white border-transparent"
                                            : "bg-white border-gray-200 text-gray-600 hover:border-brand-violet hover:text-brand-violet"
                                        }`}
                                >
                                    ${amount}
                                </Button>
                            ))}
                        </div>
                        <Button
                            onClick={handleRecharge}
                            disabled={isRecharging}
                            className="w-full h-14 mt-4 bg-brand-black hover:bg-gray-800 text-white rounded-xl font-bold text-lg shadow-xl translate-y-2 hover:translate-y-1 transition-all"
                        >
                            {isRecharging ? (
                                <><Loader2 className="w-5 h-5 mr-3 animate-spin" /> Processing...</>
                            ) : (
                                <><CreditCard className="w-5 h-5 mr-3" /> Secure Checkout (Stripe)</>
                            )}
                        </Button>
                    </CardFooter>
                </Card>

                {/* Bring Your Own Carrier (BYOC) Information Card */}
                <Card className="border-0 shadow-lg bg-white/5 border border-white/10 rounded-[2rem] overflow-hidden text-white backdrop-blur-md">
                    <CardHeader className="p-8 pb-4">
                        <CardTitle className="flex items-center space-x-3 text-xl font-bold text-white">
                            <Phone className="w-6 h-6 text-brand-violet" />
                            <span>Bring Your Own Carrier (BYOC)</span>
                        </CardTitle>
                        <CardDescription className="text-gray-400 font-medium">
                            Want to use your own Twilio numbers? Paste this Webhook URL into your Twilio Console.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="p-8 pt-0 space-y-6">
                        <div className="bg-black/30 p-5 rounded-2xl border border-white/10 relative group">
                            <div className="text-[10px] font-bold text-brand-violet uppercase tracking-widest mb-2">Twilio Webhook URL (POST)</div>
                            <code className="text-sm text-green-400 font-mono break-all line-clamp-2">
                                https://{process.env.REACT_APP_API_BASE_URL?.replace('/api/v1', '') || 'voicerender.vercel.app'}/incoming_twilio
                            </code>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="absolute top-4 right-4 text-gray-400 hover:text-white glass-dark"
                                onClick={() => {
                                    navigator.clipboard.writeText(`https://${process.env.REACT_APP_API_BASE_URL?.replace('/api/v1', '') || 'voicerender.vercel.app'}/incoming_twilio`);
                                    toast({ title: "Copied to clipboard" });
                                }}
                            >
                                Copy
                            </Button>
                        </div>

                        <ul className="space-y-3">
                            <li className="flex items-start text-sm text-gray-300">
                                <CheckCircle2 className="w-5 h-5 text-emerald-400 mr-3 shrink-0" />
                                <span>You pay Twilio directly for the phone number ($1.15/mo) and inbound minutes ($0.0085/min).</span>
                            </li>
                            <li className="flex items-start text-sm text-gray-300">
                                <CheckCircle2 className="w-5 h-5 text-emerald-400 mr-3 shrink-0" />
                                <span>VoiceRender still charges $0.03/min against your Wallet Balance for AI processing.</span>
                            </li>
                        </ul>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Settings;

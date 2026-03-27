import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';
import { Phone, CheckCircle2, Search, Loader2, CreditCard, Cloud, Signal, Activity } from 'lucide-react';

const PhoneNumbers = () => {
    const { user } = useAuth();
    const location = useLocation();
    const { toast } = useToast();

    const [numbers, setNumbers] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    // Modals
    const [showSearchModal, setShowSearchModal] = useState(false);
    const [showTwilioModal, setShowTwilioModal] = useState(false);

    // Search State
    const [areaCodeSearch, setAreaCodeSearch] = useState('');
    const [availableNumbers, setAvailableNumbers] = useState([]);
    const [isSearchingNumbers, setIsSearchingNumbers] = useState(false);
    const [isBuyingNumber, setIsBuyingNumber] = useState(null);

    // Twilio State
    const [twilioNumber, setTwilioNumber] = useState('');
    const [twilioName, setTwilioName] = useState('');
    const [isImportingTwilio, setIsImportingTwilio] = useState(false);

    useEffect(() => {
        fetchNumbers();

        // Check for success from Stripe
        const searchParams = new URLSearchParams(location.search);
        if (searchParams.get('checkout_success') === 'true') {
            toast({
                title: "Number Purchased!",
                description: `Successfully procured ${searchParams.get('phone_number')}`,
            });
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }, [location, toast]);

    const fetchNumbers = async () => {
        setIsLoading(true);
        try {
            const res = await api.billing.getPhoneNumbers();
            setNumbers(res.data);
        } catch (err) {
            toast({ title: 'Error fetching numbers', variant: 'destructive' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSearchNumbers = async (e) => {
        e.preventDefault();
        setIsSearchingNumbers(true);
        try {
            const response = await api.billing.searchNumbers(areaCodeSearch);
            setAvailableNumbers(response.data);
            if (response.data.length === 0) {
                toast({ title: "No numbers found", description: "Try a different area code." });
            }
        } catch (error) {
            toast({ title: "Search failed", variant: "destructive" });
        } finally {
            setIsSearchingNumbers(false);
        }
    };

    const handleBuyNumber = async (phoneNumber) => {
        setIsBuyingNumber(phoneNumber);
        try {
            const res = await api.billing.createCheckoutSession(null, phoneNumber);
            if (res.data?.url) {
                window.location.href = res.data.url;
            }
        } catch (error) {
            toast({ title: "Checkout failed", variant: "destructive" });
            setIsBuyingNumber(null);
        }
    };

    const handleImportTwilio = async (e) => {
        e.preventDefault();
        if (!twilioNumber) return;

        setIsImportingTwilio(true);
        try {
            await api.billing.importTwilioNumber(twilioNumber, twilioName);
            toast({ title: "Number Imported", description: "Your Twilio number is now available to assign." });
            setShowTwilioModal(false);
            setTwilioNumber('');
            setTwilioName('');
            fetchNumbers();
        } catch (err) {
            toast({
                title: "Import Failed",
                description: err.response?.data?.detail || "Could not save number.",
                variant: "destructive"
            });
        } finally {
            setIsImportingTwilio(false);
        }
    };

    const twilioUrl = `https://${process.env.REACT_APP_BACKEND_URL?.replace('/api/v1', '') || 'voicerender.vercel.app'}/incoming_twilio`;

    return (
        <div className="p-8 max-w-6xl mx-auto space-y-8 animate-reveal">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center">
                        <Phone className="w-6 h-6 text-brand-violet" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight">Phone Numbers</h1>
                        <p className="text-gray-400 font-medium">Manage native inbound numbers or integrate your own.</p>
                    </div>
                </div>
                <div className="flex space-x-3">
                    <Button
                        variant="outline"
                        className="bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white"
                        onClick={() => setShowTwilioModal(true)}
                    >
                        <Cloud className="w-4 h-4 mr-2" />
                        Import Twilio Link
                    </Button>
                    <Button
                        className="bg-brand-violet hover:bg-brand-violet/90 text-white"
                        onClick={() => setShowSearchModal(true)}
                    >
                        <Signal className="w-4 h-4 mr-2" />
                        Buy Native Number
                    </Button>
                </div>
            </div>

            <Card className="border-0 shadow-2xl bg-white/5 border border-white/10 rounded-[2rem] overflow-hidden backdrop-blur-md">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-white/10 bg-black/20 text-xs font-bold text-gray-400 uppercase tracking-widest leading-none">
                                <th className="py-5 px-6 font-medium">Phone Number</th>
                                <th className="py-5 px-6 font-medium">Provider</th>
                                <th className="py-5 px-6 font-medium">Name / Alias</th>
                                <th className="py-5 px-6 font-medium w-[150px] text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {isLoading ? (
                                <tr>
                                    <td colSpan={4} className="p-12 text-center text-gray-400">
                                        <Loader2 className="w-8 h-8 animate-spin text-brand-violet mx-auto mb-4" />
                                        Fetching numbers...
                                    </td>
                                </tr>
                            ) : numbers.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="p-12 text-center text-gray-400">
                                        <Phone className="w-12 h-12 text-gray-600 mx-auto mb-4 opacity-50" />
                                        <p className="font-bold text-lg text-gray-300">No phone numbers yet.</p>
                                        <p className="mt-1">Buy a native number or import your Twilio link to get started.</p>
                                    </td>
                                </tr>
                            ) : (
                                numbers.map((num) => (
                                    <tr key={num.id} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                                        <td className="py-5 px-6">
                                            <div className="text-lg font-bold text-white tracking-widest">{num.phone_number}</div>
                                        </td>
                                        <td className="py-5 px-6">
                                            <div className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold capitalize bg-white/10 text-gray-300">
                                                {num.provider}
                                            </div>
                                        </td>
                                        <td className="py-5 px-6 text-gray-400 font-medium">
                                            {num.friendly_name || '—'}
                                        </td>
                                        <td className="py-5 px-6 text-center">
                                            <div className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold ${num.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-500/10 text-gray-400'
                                                }`}>
                                                <div className={`w-1.5 h-1.5 rounded-full ${num.status === 'active' ? 'bg-emerald-400' : 'bg-gray-400'}`}></div>
                                                <span className="capitalize">{num.status}</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* SEARCH AND BUY NATIVE NUMBER MODAL */}
            <Dialog open={showSearchModal} onOpenChange={setShowSearchModal}>
                <DialogContent className="sm:max-w-[450px] bg-white border-0 glass-dark">
                    <DialogHeader>
                        <DialogTitle className="text-2xl font-bold flex items-center text-brand-black">
                            <Signal className="w-5 h-5 mr-3 text-brand-violet" /> Buy Native Number
                        </DialogTitle>
                        <DialogDescription className="text-gray-500 font-medium">
                            Native numbers cost $5/month. Toll-Free (800, 888) or Local area codes supported.
                        </DialogDescription>
                    </DialogHeader>

                    <form onSubmit={handleSearchNumbers} className="flex gap-2">
                        <Input
                            value={areaCodeSearch}
                            onChange={(e) => setAreaCodeSearch(e.target.value)}
                            placeholder="Area code (e.g. 888 or 415)"
                            maxLength={3}
                            className="font-mono text-center text-brand-black border-gray-300 focus:border-brand-violet focus:ring-brand-violet"
                        />
                        <Button type="submit" disabled={isSearchingNumbers} className="bg-brand-black text-white px-6">
                            {isSearchingNumbers ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                        </Button>
                    </form>

                    {availableNumbers.length > 0 && (
                        <div className="mt-4 max-h-[300px] overflow-y-auto space-y-2 border border-gray-100 rounded-xl p-2 bg-gray-50">
                            {availableNumbers.map((num) => (
                                <div key={num.phone_number} className="flex items-center justify-between p-3 rounded-lg bg-white border border-gray-100 hover:border-brand-violet/30 transition-colors shadow-sm">
                                    <div>
                                        <div className="font-bold text-brand-black tracking-widest">{num.phone_number}</div>
                                        <div className="text-xs text-gray-400 uppercase tracking-wider">{num.region || 'US'} - {num.locality || 'Toll-Free'}</div>
                                    </div>
                                    <Button
                                        size="sm"
                                        onClick={() => handleBuyNumber(num.phone_number)}
                                        disabled={!!isBuyingNumber}
                                        className="bg-brand-violet hover:bg-brand-violet/90 text-white rounded-full px-4"
                                    >
                                        {isBuyingNumber === num.phone_number ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Buy $5/mo'}
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* IMPORT TWILIO MODAL */}
            <Dialog open={showTwilioModal} onOpenChange={setShowTwilioModal}>
                <DialogContent className="sm:max-w-[450px] bg-[#0d1219] border border-white/10 text-white">
                    <DialogHeader>
                        <DialogTitle className="text-2xl font-bold flex items-center text-white">
                            <Cloud className="w-5 h-5 mr-3 text-brand-violet" /> Import Twilio Link
                        </DialogTitle>
                        <DialogDescription className="text-gray-400 font-medium pb-4 border-b border-white/10">
                            Configure your Twilio Webhook to map incoming calls to this Organization.
                        </DialogDescription>
                    </DialogHeader>

                    <form onSubmit={handleImportTwilio} className="space-y-4 pt-2">
                        <div className="space-y-2">
                            <Label className="text-gray-300">Target Twilio Number</Label>
                            <Input
                                value={twilioNumber}
                                onChange={(e) => setTwilioNumber(e.target.value)}
                                placeholder="+18885551234"
                                className="bg-black/50 border-white/10 text-white font-mono placeholder:text-gray-600 focus:border-brand-violet"
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-gray-300">Alias / Name (Optional)</Label>
                            <Input
                                value={twilioName}
                                onChange={(e) => setTwilioName(e.target.value)}
                                placeholder="Main Support Line"
                                className="bg-black/50 border-white/10 text-white focus:border-brand-violet"
                            />
                        </div>

                        <div className="bg-brand-violet/10 border border-brand-violet/20 p-4 rounded-xl mt-4">
                            <p className="text-xs font-bold text-brand-violet uppercase tracking-widest mb-2">Required Twilio Webhook URL (POST)</p>
                            <code className="block text-xs text-emerald-400 font-mono break-all font-bold">
                                {twilioUrl}
                            </code>
                        </div>

                        <Button type="submit" disabled={isImportingTwilio} className="w-full bg-brand-violet hover:bg-brand-violet/90 text-white">
                            {isImportingTwilio ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                            Save Link
                        </Button>
                    </form>
                </DialogContent>
            </Dialog>

        </div>
    );
};

export default PhoneNumbers;

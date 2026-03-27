import React, { useEffect } from 'react';
import { Card, CardContent } from '../ui/card';
import { ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

const TermsOfService = () => {
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    return (
        <div className="min-h-screen bg-[#0d1219] text-gray-300 py-20 px-6 font-sans">
            <div className="max-w-4xl mx-auto">
                <div className="mb-12 text-center">
                    <div className="w-16 h-16 bg-brand-violet/10 border border-brand-violet/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                        <ShieldCheck className="w-8 h-8 text-brand-violet" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">Terms of Service</h1>
                    <p className="text-lg text-gray-400">Last updated: {new Date().toLocaleDateString()}</p>
                </div>

                <Card className="bg-white/5 border-white/10 backdrop-blur-md rounded-3xl overflow-hidden shadow-2xl">
                    <CardContent className="p-8 md:p-12 space-y-8 text-base/relaxed">
                        
                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
                            <p>
                                By accessing and using VoiceRender ("the Service"), you accept and agree to be bound by the terms 
                                and provision of this agreement. Our services are provided primarily for B2B integration, enabling 
                                businesses to deploy AI voice agents seamlessly.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">2. Description of Service</h2>
                            <p>
                                VoiceRender is a SaaS platform providing infrastructure to create, manage, and deploy AI voice agents 
                                over telephonic networks (e.g., SignalWire, Twilio). We provide the software layer connecting Large 
                                Language Models (LLMs) with telecommunications APIs.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">3. Subscriptions and Payments</h2>
                            <p>
                                Some features of the Service are billed on a subscription and usage basis. 
                                By providing a payment method, you expressly authorize us (or our Merchant of Record) to charge the 
                                applicable fees on said payment method as well as taxes and other charges incurred thereto at regular intervals, 
                                all of which depend on your particular subscription and utilized services.
                            </p>
                        </section>

                        <section className="bg-brand-violet/5 -mx-8 sm:-mx-12 px-8 sm:px-12 py-8 border-y border-brand-violet/10">
                            <h2 className="text-2xl font-bold text-brand-violet mb-4">4. Refund Policy</h2>
                            <p className="mb-4">
                                <strong>Subscriptions:</strong> Monthly subscription fees for leased phone numbers or baseline platform access are generally non-refundable once the billing cycle has commenced, as these incur immediate upstream telecommunications costs.
                            </p>
                            <p className="mb-4">
                                <strong>Prepaid Usage Balance:</strong> Funds added to your prepaid digital wallet for "compute minutes" are non-refundable once deposited to your account. We highly recommend testing our service with a small initial deposit.
                            </p>
                            <p>
                                <strong>Exceptions:</strong> If you believe there has been a billing error, please contact our support team within 7 days of the charge. We will review the claim and, at our sole discretion, issue a credit or refund for erroneous charges.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">5. User Conduct and Acceptable Use</h2>
                            <p>
                                You agree not to use the Service to originate illegal robocalls, spam, harassment, or to deceive consumers. 
                                Any violation of these acceptable use policies will result in immediate termination of your account 
                                without refund and possible referral to law enforcement.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">6. Limitation of Liability</h2>
                            <p>
                                VoiceRender shall not be liable for any indirect, incidental, special, consequential or punitive damages,
                                including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from 
                                your access to or use of or inability to access or use the Service.
                            </p>
                        </section>
                    </CardContent>
                </Card>
                
                <div className="mt-8 text-center">
                    <Link to="/landing" className="text-brand-violet hover:text-white font-semibold transition-colors">
                        ← Return to Home
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default TermsOfService;

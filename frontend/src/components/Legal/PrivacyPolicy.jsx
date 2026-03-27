import React, { useEffect } from 'react';
import { Card, CardContent } from '../ui/card';
import { ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

const PrivacyPolicy = () => {
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    return (
        <div className="min-h-screen bg-[#0d1219] text-gray-300 py-20 px-6 font-sans">
            <div className="max-w-4xl mx-auto">
                <div className="mb-12 text-center">
                    <div className="w-16 h-16 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                        <ShieldCheck className="w-8 h-8 text-blue-500" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">Privacy Policy</h1>
                    <p className="text-lg text-gray-400">Last updated: {new Date().toLocaleDateString()}</p>
                </div>

                <Card className="bg-white/5 border-white/10 backdrop-blur-md rounded-3xl overflow-hidden shadow-2xl">
                    <CardContent className="p-8 md:p-12 space-y-8 text-base/relaxed">
                        
                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">1. Information We Collect</h2>
                            <p className="mb-4">
                                <strong>Account Information:</strong> We collect your email address, name, and password when you register for an account.
                            </p>
                            <p className="mb-4">
                                <strong>Payment Information:</strong> We use authorized third-party payment processors (Merchant of Record). We do not store your full credit card details.
                            </p>
                            <p>
                                <strong>Call Data:</strong> To provide our AI agent services, we temporarily process and transcribe audio streams. Call metadata, transcripts, and recordings are retained in your dashboard to help you analyze customer interactions.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">2. How We Use Your Information</h2>
                            <p>
                                We use the information we collect to provide, maintain, and improve our services, to process your transactions,
                                to send you related information such as confirmations and invoices, and to provide customer support.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">3. Data Sharing and Disclosure</h2>
                            <p>
                                We do not sell your personal data. We may share data with trusted third-party service providers (like our cloud hosts, telephony providers, and Large Language Model APIs) strictly for the purpose of operating the Service. 
                                These providers are bound by strict confidentiality requirements.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">4. Security</h2>
                            <p>
                                We implement industry-standard security measures to protect your personal information and call data from unauthorized access, disclosure, or alteration. All data transmissions are encrypted using SSL/TLS.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-bold text-white mb-4">5. Your Data Rights</h2>
                            <p>
                                Depending on your location, you may have the right to access, correct, or delete your personal data. 
                                You can manage your account information directly from your dashboard or contact our support team for assistance with data deletion requests.
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

export default PrivacyPolicy;

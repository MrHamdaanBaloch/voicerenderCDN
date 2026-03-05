import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/card';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { useToast } from '../../hooks/use-toast';
import { getErrorMessage } from '../../lib/utils';
import { Bot, ArrowLeft } from 'lucide-react';

const RegisterPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const { toast } = useToast();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await register({ email, password, first_name: firstName, last_name: lastName });
            toast({
                title: "Registration Successful",
                description: "Welcome! You are now logged in.",
            });
        } catch (error) {
            console.error("Registration error:", error);
            toast({
                title: "Registration Failed",
                description: getErrorMessage(error, "An unexpected error occurred during registration."),
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-brand-black p-4 relative overflow-hidden">
            {/* Background elements */}
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-hero opacity-50"></div>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-violet/5 blur-[120px] rounded-full"></div>

            <div className="w-full max-w-md relative z-10 animate-reveal">
                <div className="mb-6 text-center">
                    <Link to="/landing" className="inline-flex items-center text-gray-400 hover:text-brand-violet transition-colors mb-4 group">
                        <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
                        Back to site
                    </Link>
                    <div className="flex justify-center mb-4">
                        <div className="w-12 h-12 bg-brand-violet rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(108,99,255,0.4)]">
                            <Bot className="w-7 h-7 text-white" />
                        </div>
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Create Account</h1>
                    <p className="text-gray-400 font-body">Scale your sales with humanlike AI.</p>
                </div>

                <Card className="border-0 shadow-2xl bg-white text-brand-black overflow-hidden rounded-[2rem]">
                    <CardHeader className="pt-8 pb-2 px-8">
                        <CardTitle className="text-2xl font-bold tracking-tight text-center">Join VoiceRender</CardTitle>
                        <CardDescription className="text-gray-500 text-center">
                            Start your 100 free minutes today.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="px-8 pb-8 pt-4">
                        <form onSubmit={handleSubmit} className="grid gap-5">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="grid gap-2">
                                    <Label htmlFor="first-name" className="font-bold text-xs uppercase tracking-wider text-gray-500">First Name</Label>
                                    <Input
                                        id="first-name"
                                        type="text"
                                        placeholder="John"
                                        value={firstName}
                                        onChange={(e) => setFirstName(e.target.value)}
                                        className="h-11 border-gray-200 focus:border-brand-violet focus:ring-brand-violet rounded-xl"
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="last-name" className="font-bold text-xs uppercase tracking-wider text-gray-500">Last Name</Label>
                                    <Input
                                        id="last-name"
                                        type="text"
                                        placeholder="Doe"
                                        value={lastName}
                                        onChange={(e) => setLastName(e.target.value)}
                                        className="h-11 border-gray-200 focus:border-brand-violet focus:ring-brand-violet rounded-xl"
                                    />
                                </div>
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="email" className="font-bold text-xs uppercase tracking-wider text-gray-500">Email Address</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="name@company.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="h-11 border-gray-200 focus:border-brand-violet focus:ring-brand-violet rounded-xl"
                                    required
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="password" university className="font-bold text-xs uppercase tracking-wider text-gray-500">Password</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    value={password}
                                    placeholder="••••••••"
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="h-11 border-gray-200 focus:border-brand-violet focus:ring-brand-violet rounded-xl"
                                    required
                                />
                            </div>
                            <Button
                                type="submit"
                                className="w-full h-12 text-lg font-bold bg-brand-black hover:bg-brand-black/90 text-white rounded-xl shadow-lg transition-transform active:scale-[0.98] mt-2"
                                disabled={loading}
                            >
                                {loading ? (
                                    <span className="flex items-center"><Bot className="w-4 h-4 mr-2 animate-bounce" /> Creating...</span>
                                ) : 'Create Free Account'}
                            </Button>
                        </form>
                    </CardContent>
                    <CardFooter className="flex justify-center bg-gray-50 py-6 border-t border-gray-100">
                        <p className="text-sm text-gray-500 font-body">
                            Already have an account?{' '}
                            <Link to="/login" className="font-bold text-brand-violet hover:underline">
                                Log In
                            </Link>
                        </p>
                    </CardFooter>
                </Card>
                <p className="mt-8 text-center text-xs text-gray-500 px-8">
                    By clicking "Create Free Account", you agree to our <Link to="#" className="underline">Terms of Service</Link> and <Link to="#" className="underline">Privacy Policy</Link>.
                </p>
            </div>
        </div>
    );
};

export default RegisterPage;

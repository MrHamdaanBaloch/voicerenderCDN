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

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const { toast } = useToast();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await login(email, password);
            toast({
                title: "Login Successful",
                description: "Welcome back!",
            });
        } catch (error) {
            console.error("Login error:", error);
            toast({
                title: "Login Failed",
                description: getErrorMessage(error, "An unexpected error occurred during login."),
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
            <div className="absolute -top-24 -left-24 w-64 h-64 bg-brand-violet/10 blur-[100px] rounded-full"></div>
            <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-brand-violet/10 blur-[100px] rounded-full"></div>

            <div className="w-full max-w-md relative z-10 animate-reveal">
                <div className="mb-8 text-center">
                    <Link to="/landing" className="inline-flex items-center text-gray-400 hover:text-brand-violet transition-colors mb-6 group">
                        <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
                        Back to site
                    </Link>
                    <div className="flex justify-center mb-4">
                        <div className="w-12 h-12 bg-brand-violet rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(108,99,255,0.4)]">
                            <Bot className="w-7 h-7 text-white" />
                        </div>
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Welcome Back</h1>
                    <p className="text-gray-400 font-body">Scale your sales with humanlike AI.</p>
                </div>

                <Card className="border-0 shadow-2xl bg-white text-brand-black overflow-hidden rounded-[2rem]">
                    <CardHeader className="pt-10 pb-2 px-8">
                        <CardTitle className="text-2xl font-bold tracking-tight">Login</CardTitle>
                        <CardDescription className="text-gray-500">
                            Enter your credentials to manage your AI agents.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="px-8 pb-8">
                        <form onSubmit={handleSubmit} className="grid gap-6">
                            <div className="grid gap-2">
                                <Label htmlFor="email" className="font-bold text-sm">Email Address</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="name@company.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="h-12 border-gray-200 focus:border-brand-violet focus:ring-brand-violet rounded-xl"
                                    required
                                />
                            </div>
                            <div className="grid gap-2">
                                <div className="flex items-center justify-between">
                                    <Label htmlFor="password" university className="font-bold text-sm">Password</Label>
                                    <Link to="#" className="text-xs text-brand-violet hover:underline font-semibold">Forgot password?</Link>
                                </div>
                                <Input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="h-12 border-gray-200 focus:border-brand-violet focus:ring-brand-violet rounded-xl"
                                    required
                                />
                            </div>
                            <Button
                                type="submit"
                                className="w-full h-12 text-lg font-bold bg-brand-black hover:bg-brand-black/90 text-white rounded-xl shadow-lg transition-transform active:scale-[0.98]"
                                disabled={loading}
                            >
                                {loading ? (
                                    <span className="flex items-center"><Bot className="w-4 h-4 mr-2 animate-bounce" /> Authenticating...</span>
                                ) : 'Sign In'}
                            </Button>
                        </form>
                    </CardContent>
                    <CardFooter className="flex justify-center bg-gray-50 py-6 border-t border-gray-100">
                        <p className="text-sm text-gray-500">
                            New here?{' '}
                            <Link to="/register" className="font-bold text-brand-violet hover:underline">
                                Start 100 Free Minutes
                            </Link>
                        </p>
                    </CardFooter>
                </Card>
            </div>
        </div>
    );
};

export default LoginPage;

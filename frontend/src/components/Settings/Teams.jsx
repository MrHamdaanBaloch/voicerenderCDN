import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import {
    Users,
    UserPlus,
    Mail,
    Shield,
    MoreVertical,
    Search,
    ExternalLink,
    Settings2,
    Check,
    ShieldCheck,
    Globe,
    Zap,
    Lock,
    Activity
} from 'lucide-react';

const Teams = () => {
    const [inviteEmail, setInviteEmail] = useState('');

    const members = [
        {
            id: 1,
            name: 'Hamdaan Baloch',
            email: 'hamdaan@example.com',
            role: 'Owner',
            status: 'Active',
            lastActive: 'Just now',
            avatar: 'HB'
        },
        {
            id: 2,
            name: 'Sarah Chen',
            email: 'sarah.c@example.com',
            role: 'Admin',
            status: 'Active',
            lastActive: '2 hours ago',
            avatar: 'SC'
        },
        {
            id: 3,
            name: 'Marcus Wright',
            email: 'm.wright@example.com',
            role: 'Member',
            status: 'Pending',
            lastActive: 'Invited 1 day ago',
            avatar: 'MW'
        }
    ];

    return (
        <div className="space-y-10 animate-reveal max-w-7xl mx-auto">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div className="flex items-center space-x-6">
                    <div className="w-16 h-16 bg-brand-violet/10 rounded-3xl flex items-center justify-center text-brand-violet shadow-lg shadow-brand-violet/10">
                        <Users className="w-8 h-8" />
                    </div>
                    <div>
                        <h1 className="text-4xl font-extrabold text-white tracking-tighter">Command Center</h1>
                        <p className="text-gray-400 font-medium">Coordinate access protocols and operative hierarchies.</p>
                    </div>
                </div>
                <div>
                    <Badge variant="outline" className="px-4 py-2 border-white/10 text-brand-violet bg-white/5 font-black uppercase tracking-widest text-[10px] rounded-xl">
                        {members.length} / 10 Active Seats
                    </Badge>
                </div>
            </div>

            {/* Invite Member Section */}
            <Card className="border-0 shadow-2xl bg-brand-violet rounded-[3rem] overflow-hidden relative group">
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32 blur-3xl group-hover:bg-white/20 transition-all duration-500" />
                <CardContent className="p-12 relative z-10">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                        <div className="text-white">
                            <h2 className="text-3xl font-black mb-4 tracking-tight">Expand the Network</h2>
                            <p className="text-white/80 font-medium text-lg leading-relaxed max-w-md">
                                Provision new tactical access for collaborators. New operatives will receive encrypted invitation packets.
                            </p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-4">
                            <div className="relative flex-1 group">
                                <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50 group-focus-within:text-white transition-colors" />
                                <Input
                                    placeholder="operative@organization.com"
                                    value={inviteEmail}
                                    onChange={(e) => setInviteEmail(e.target.value)}
                                    className="h-16 pl-14 bg-white/10 border-white/20 text-white placeholder:text-white/40 focus:ring-2 focus:ring-white/30 transition-all rounded-2xl font-bold"
                                />
                            </div>
                            <Button className="h-16 bg-white text-brand-black hover:bg-gray-100 px-10 rounded-2xl font-black transition-all shadow-xl active:scale-95 flex items-center group whitespace-nowrap">
                                <UserPlus className="w-5 h-5 mr-3 group-hover:rotate-12 transition-transform" />
                                Deploy Invite
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Team List Table */}
            <Card className="border-0 shadow-2xl bg-white rounded-[3rem] overflow-hidden">
                <CardHeader className="p-10 border-b border-gray-100 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="relative w-full md:w-96 group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-brand-violet transition-colors" />
                        <Input
                            placeholder="Identify operatives..."
                            className="h-12 pl-12 border-gray-100 bg-gray-50/50 rounded-2xl font-bold focus:ring-brand-violet/20 focus:border-brand-violet transition-all"
                        />
                    </div>
                    <div className="flex items-center space-x-3">
                        <Button variant="ghost" className="h-12 px-6 rounded-2xl font-bold text-gray-500 hover:bg-gray-100">
                            <Settings2 className="w-4 h-4 mr-2" />
                            Role Config
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="bg-gray-50/50">
                                    <th className="px-10 py-6 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Operative Profile</th>
                                    <th className="px-10 py-6 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Authority Level</th>
                                    <th className="px-10 py-6 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Status</th>
                                    <th className="px-10 py-6 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Pulse</th>
                                    <th className="px-10 py-6 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {members.map((member) => (
                                    <tr key={member.id} className="hover:bg-brand-violet/[0.02] transition-colors group">
                                        <td className="px-10 py-8">
                                            <div className="flex items-center space-x-5">
                                                <Avatar className="w-14 h-14 rounded-2xl border-4 border-white shadow-xl ring-2 ring-gray-100 group-hover:scale-110 transition-transform">
                                                    <AvatarFallback className="bg-brand-black text-brand-violet font-black text-lg">{member.avatar}</AvatarFallback>
                                                </Avatar>
                                                <div>
                                                    <p className="font-black text-brand-black text-lg leading-tight tracking-tight">{member.name}</p>
                                                    <p className="text-sm text-gray-400 font-bold font-mono">{member.email}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-10 py-8">
                                            <div className="flex items-center text-brand-black font-black text-xs uppercase tracking-widest">
                                                <ShieldCheck className={`w-4 h-4 mr-2 ${member.role === 'Owner' || member.role === 'Admin' ? 'text-brand-violet' : 'text-gray-300'}`} />
                                                {member.role}
                                            </div>
                                        </td>
                                        <td className="px-10 py-8">
                                            <Badge className={`px-4 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-widest ${member.status === 'Active' ? 'bg-emerald-50 text-emerald-600 border-0' : 'bg-amber-50 text-amber-600 border-0'
                                                }`}>
                                                <div className={`w-1.5 h-1.5 rounded-full mr-2 ${member.status === 'Active' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500'} animate-pulse`} />
                                                {member.status}
                                            </Badge>
                                        </td>
                                        <td className="px-10 py-8 text-xs text-gray-400 font-bold uppercase tracking-tighter">
                                            {member.lastActive}
                                        </td>
                                        <td className="px-10 py-8 text-right">
                                            <Button variant="ghost" size="icon" className="w-10 h-10 hover:bg-gray-100 rounded-xl text-gray-300 hover:text-brand-black transition-all">
                                                <MoreVertical className="w-5 h-5" />
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Permissions Guide Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {[
                    { icon: Lock, title: 'Administrators', desc: 'Full-spectrum control over agents, neural data, and financial protocols.', accent: 'brand-violet' },
                    { icon: Activity, title: 'Operators', desc: 'Provisioning and configuration of specialized voice agents.', accent: 'brand-violet' },
                    { icon: Globe, title: 'Observers', desc: 'Restricted analytical access to historical interaction metrics.', accent: 'brand-violet' },
                ].map((role, i) => (
                    <Card key={i} className="border-0 shadow-lg bg-white/5 border-white/5 hover:bg-white/10 transition-all p-2 rounded-[2rem]">
                        <CardContent className="p-8">
                            <div className="w-12 h-12 rounded-2xl bg-brand-violet/20 text-brand-violet flex items-center justify-center mb-6 shadow-lg shadow-brand-violet/10">
                                <role.icon className="w-6 h-6" />
                            </div>
                            <h3 className="font-black text-white text-xl mb-3 tracking-tight">{role.title}</h3>
                            <p className="text-sm text-gray-400 leading-relaxed font-medium">{role.desc}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
};

export default Teams;

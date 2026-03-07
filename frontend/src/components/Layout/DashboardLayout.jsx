import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback } from '../ui/avatar';
import {
  LayoutDashboard,
  Bot,
  Phone,
  BarChart3,
  Settings,
  Users,
  Key,
  LogOut,
  Menu,
  X,
  Sparkles,
  Hash,
  Zap,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const NAV_ITEMS = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, group: 'overview' },
  { name: 'Agents', href: '/agents', icon: Bot, group: 'core' },
  { name: 'Calls', href: '/calls', icon: Phone, group: 'core', live: true },
  { name: 'Numbers', href: '/phone-numbers', icon: Hash, group: 'core' },
  { name: 'Reports', href: '/reports', icon: BarChart3, group: 'analyze' },
  { name: 'Team', href: '/settings/users', icon: Users, group: 'settings' },
  { name: 'API Keys', href: '/settings/api-keys', icon: Key, group: 'settings' },
  { name: 'Settings', href: '/settings', icon: Settings, group: 'settings' },
];

const GROUPS = [
  { key: 'overview', label: 'Overview' },
  { key: 'core', label: 'Workspace' },
  { key: 'analyze', label: 'Analytics' },
  { key: 'settings', label: 'Settings' },
];

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const isActive = (href) =>
    location.pathname === href || location.pathname.startsWith(href + '/');

  const balanceMins = user?.balance_seconds
    ? Math.floor(user.balance_seconds / 60)
    : 0;

  return (
    <div className="flex h-screen bg-brand-black font-body overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ── */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col w-60 border-r border-white/[0.06] bg-[#09090B] transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-white/[0.06] shrink-0">
          <Link to="/landing" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 bg-gradient-to-br from-violet-600 to-violet-800 rounded-lg flex items-center justify-center shadow-glow-violet group-hover:shadow-[0_0_20px_rgba(124,58,237,0.6)] transition-shadow">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-heading font-bold text-white text-sm tracking-tight">VoiceRender</span>
              <span className="block text-[9px] font-bold text-violet-400 uppercase tracking-[0.15em] leading-none">AI Platform</span>
            </div>
          </Link>
          <button
            className="lg:hidden text-zinc-500 hover:text-white transition-colors"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto scrollbar-hide px-3 py-4 space-y-6">
          {GROUPS.map(({ key, label }) => {
            const items = NAV_ITEMS.filter(i => i.group === key);
            return (
              <div key={key}>
                <p className="text-[9px] font-bold uppercase tracking-[0.15em] text-zinc-600 px-3 mb-2">{label}</p>
                <div className="space-y-0.5">
                  {items.map(item => {
                    const Icon = item.icon;
                    const active = isActive(item.href);
                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        onClick={() => setSidebarOpen(false)}
                        className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${active
                            ? 'bg-violet-500/10 text-white border border-violet-500/20'
                            : 'text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.04]'
                          }`}
                      >
                        <Icon
                          className={`w-4 h-4 shrink-0 transition-colors ${active ? 'text-violet-400' : 'text-zinc-600 group-hover:text-zinc-400'
                            }`}
                        />
                        <span className="flex-1 truncate">{item.name}</span>
                        {item.live && (
                          <span className="dot-live w-1.5 h-1.5" />
                        )}
                        {active && (
                          <ChevronRight className="w-3.5 h-3.5 text-violet-500 shrink-0" />
                        )}
                      </Link>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>

        {/* Balance pill */}
        <div className="px-3 mb-3 shrink-0">
          <Link
            to="/settings"
            className="flex items-center gap-2.5 p-3 rounded-xl border border-white/[0.06] bg-white/[0.03] hover:bg-violet-500/10 hover:border-violet-500/20 transition-all group"
          >
            <div className="w-7 h-7 rounded-lg bg-violet-500/15 flex items-center justify-center shrink-0">
              <Sparkles className="w-3.5 h-3.5 text-violet-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[11px] font-bold text-white leading-none mb-1">Balance</p>
              <p className="text-[10px] text-zinc-500 leading-none">{balanceMins} min remaining</p>
            </div>
            <div className="text-[10px] font-bold text-violet-400 group-hover:text-violet-300 transition-colors">Top Up</div>
          </Link>
        </div>

        {/* User footer */}
        <div className="px-3 pb-4 border-t border-white/[0.06] pt-3 shrink-0">
          <div className="flex items-center gap-2.5 mb-3 px-1">
            <Avatar className="w-8 h-8 shrink-0">
              <AvatarFallback className="text-[11px] font-bold text-white bg-gradient-to-br from-violet-600 to-violet-800">
                {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-[12px] font-bold text-white truncate leading-tight">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-[10px] text-zinc-600 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-semibold text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/15 transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main Area ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile topbar */}
        <header className="lg:hidden h-14 flex items-center justify-between px-4 border-b border-white/[0.06] bg-brand-black shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-zinc-400 hover:text-white transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-gradient-to-br from-violet-600 to-violet-800 rounded-lg flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-heading font-bold text-white text-sm">VoiceRender</span>
          </div>
          <Avatar className="w-7 h-7">
            <AvatarFallback className="text-[10px] font-bold text-white bg-violet-700">
              {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
        </header>

        {/* Desktop topbar */}
        <header className="hidden lg:flex h-14 items-center justify-between px-8 border-b border-white/[0.06] bg-brand-black shrink-0">
          <div>
            <p className="text-sm font-semibold text-white leading-tight">
              Good to see you, <span className="text-violet-400">{user?.first_name}</span>
            </p>
            <p className="text-[11px] text-zinc-600 leading-tight mt-0.5">AI inbound infrastructure, running 24/7</p>
          </div>
          <div className="flex items-center gap-3">
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition-all"
              style={{
                background: 'rgba(124,58,237,0.08)',
                borderColor: 'rgba(124,58,237,0.2)',
                color: '#A78BFA'
              }}
            >
              <Sparkles className="w-3.5 h-3.5" />
              {balanceMins} mins left
            </div>
            <Link to="/settings">
              <Button size="sm" className="rounded-lg bg-violet-700 hover:bg-violet-600 text-white text-xs font-bold h-8 px-4 shadow-glow-violet">
                Top Up
              </Button>
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-brand-black relative">
          {/* Ambient violet glow */}
          <div
            className="absolute top-0 right-0 w-[600px] h-[400px] pointer-events-none"
            style={{
              background: 'radial-gradient(ellipse at top right, rgba(124,58,237,0.07) 0%, transparent 60%)',
            }}
          />
          <div className="relative z-10 p-6 lg:p-8 max-w-[1400px] mx-auto animate-reveal">
            <Outlet />
          </div>
          <footer className="border-t border-white/[0.04] py-6 text-center">
            <p className="text-[11px] text-zinc-700">© 2026 VoiceRender AI · Intelligent Inbound Automation</p>
          </footer>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
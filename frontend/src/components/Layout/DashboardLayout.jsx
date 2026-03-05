import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback } from '../ui/avatar';
import { Badge } from '../ui/badge';
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
  Sun,
  Moon
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

// Theme toggle hook
const useTheme = () => {
  const [isDark, setIsDark] = React.useState(() => {
    const saved = localStorage.getItem('vr-theme');
    return saved ? saved === 'dark' : true; // default dark
  });

  React.useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('vr-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  return [isDark, () => setIsDark(prev => !prev)];
};

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [isDark, toggleTheme] = useTheme();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Agents', href: '/agents', icon: Bot },
    { name: 'Calls', href: '/calls', icon: Phone },
    { name: 'Reports', href: '/reports', icon: BarChart3 },
    { name: 'Team', href: '/settings/users', icon: Users },
    { name: 'API Keys', href: '/settings/api-keys', icon: Key },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <div className="flex h-screen bg-brand-black font-body overflow-hidden">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm lg:hidden z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 glass-dark transform transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}>
        <div className="flex items-center justify-between h-20 px-6">
          <Link to="/landing" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 bg-brand-violet rounded-xl flex items-center justify-center shadow-[0_0_15px_rgba(108,99,255,0.4)] group-hover:scale-110 transition-transform">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">VoiceRender</h1>
              <p className="text-[10px] text-brand-violet font-bold uppercase tracking-widest">Premium AI</p>
            </div>
          </Link>
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-6 h-6" />
          </Button>
        </div>

        <nav className="mt-6 px-4 space-y-2 flex-grow overflow-y-auto h-[calc(100vh-160px)]">
          <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest px-4 mb-4">Main Menu</div>
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center px-4 py-3 text-sm font-medium rounded-2xl transition-all ${active
                  ? 'bg-brand-violet text-white shadow-[0_10px_20px_-10px_rgba(108,99,255,0.5)]'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon className={`w-5 h-5 mr-3 transition-colors ${active ? 'text-white' : 'text-gray-500 group-hover:text-brand-violet'
                  }`} />
                {item.name}
                {item.name === 'Calls' && (
                  <div className="ml-auto flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-brand-violet opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-violet"></span>
                  </div>
                )}
                {active && !(item.name === 'Calls') && <div className="ml-auto w-1.5 h-1.5 bg-white rounded-full"></div>}
              </Link>
            );
          })}
        </nav>

        {/* User info at bottom */}
        <div className="px-4 py-6 border-t border-white/5">
          <div className="bg-white/5 rounded-3xl p-4 mb-4 border border-white/5">
            <div className="flex items-center space-x-3">
              <Avatar className="w-10 h-10 border-2 border-brand-violet/20">
                <AvatarFallback className="bg-brand-violet text-white font-bold">
                  {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-white truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <div className="flex items-center">
                  <Badge className="bg-brand-violet/10 text-brand-violet text-[10px] px-2 py-0 h-4 border-brand-violet/20 pointer-events-none">
                    {user?.role || 'Pro Plan'}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-red-400/60 hover:text-red-400 hover:bg-red-400/10 rounded-2xl transition-all font-black uppercase tracking-widest text-[10px] py-6 border border-white/5 hover:border-red-400/20"
            onClick={logout}
          >
            <LogOut className="w-4 h-4 mr-3" />
            Security Sign out
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header for mobile */}
        <header className="bg-brand-black border-b border-white/5 lg:hidden px-4 h-16 flex items-center justify-between shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="text-white"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </Button>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-brand-violet rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-white tracking-tight">VoiceRender</span>
          </div>
          <Avatar className="w-8 h-8">
            <AvatarFallback className="bg-brand-violet text-white text-xs">
              {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
        </header>

        {/* Desktop Header / Breadcrumbs */}
        <header className="hidden lg:flex h-20 items-center justify-between px-10 border-b border-white/5 bg-brand-black shrink-0 relative z-10">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Welcome back, {user?.first_name}! 👋</h2>
            <p className="text-xs text-gray-400">Your AI agents are currently handling 24 active calls.</p>
          </div>
          <div className="flex items-center space-x-6">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="w-10 h-10 rounded-full bg-white/5 border border-white/10 text-white hover:bg-white/10 hover:text-brand-violet transition-all"
              title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
            <div className="flex items-center space-x-2 bg-white/5 px-4 py-2 rounded-full border border-white/5">
              <Sparkles className="w-4 h-4 text-brand-violet" />
              <span className="text-xs font-bold text-white">Growth Plan: 1,240 mins left</span>
            </div>
            <Button className="bg-brand-violet hover:bg-brand-violet/90 text-white rounded-full">
              Upgrade Now
            </Button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-brand-black p-4 lg:p-10 relative">
          {/* Subtle background glow for main area */}
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-violet/5 blur-[120px] rounded-full pointer-events-none"></div>

          <div className="relative z-10 max-w-7xl mx-auto animate-reveal">
            <Outlet />
          </div>

          <footer className="mt-20 py-10 border-t border-white/5 text-center text-gray-500 text-xs">
            <p>&copy; 2026 VoiceRender AI • High-Performance AI Sales Agents</p>
          </footer>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  MessageSquare, 
  Users, 
  BarChart3, 
  Settings, 
  FileText,
  Brain,
  Shield,
  ChevronLeft,
  ChevronRight,
  LogOut
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import useAuthStore from '../../stores/authStore';

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { user, logout, hasRole } = useAuthStore();

  const navigation = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: Home,
      roles: ['user', 'analyst', 'admin']
    },
    {
      name: 'AI Chat',
      href: '/chat',
      icon: MessageSquare,
      roles: ['user', 'analyst', 'admin']
    },
    {
      name: 'LLM Studio',
      href: '/llm-studio',
      icon: Brain,
      roles: ['user', 'analyst', 'admin']
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: BarChart3,
      roles: ['analyst', 'admin']
    },
    {
      name: 'Documents',
      href: '/documents',
      icon: FileText,
      roles: ['user', 'analyst', 'admin']
    },
    {
      name: 'User Management',
      href: '/users',
      icon: Users,
      roles: ['admin']
    },
    {
      name: 'Security',
      href: '/security',
      icon: Shield,
      roles: ['admin']
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      roles: ['user', 'analyst', 'admin']
    },
  ];

  const filteredNavigation = navigation.filter(item => 
    item.roles.some(role => hasRole(role))
  );

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className={`${collapsed ? 'w-16' : 'w-64'} bg-card border-r border-border h-screen flex flex-col transition-all duration-300`}>
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-lg">Enterprise AI</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="p-2"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* User Info */}
      {!collapsed && user && (
        <div className="p-4 border-b border-border">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
              <span className="text-white font-medium">
                {user.first_name?.[0] || user.username?.[0] || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user.first_name && user.last_name 
                  ? `${user.first_name} ${user.last_name}` 
                  : user.username
                }
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user.email}
              </p>
              {user.roles && user.roles.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {user.roles.map(role => (
                    <span 
                      key={role} 
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {filteredNavigation.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;
          
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      <Separator />

      {/* Logout */}
      <div className="p-4">
        <Button
          variant="ghost"
          onClick={handleLogout}
          className={`w-full justify-start ${collapsed ? 'px-2' : 'px-3'}`}
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span className="ml-3">Logout</span>}
        </Button>
      </div>
    </div>
  );
};

export default Sidebar;


import { useState, useEffect } from 'react';
import { 
  Users, 
  MessageSquare, 
  BarChart3, 
  TrendingUp,
  Activity,
  Brain,
  FileText,
  Clock
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import useAuthStore from '../stores/authStore';

const Dashboard = () => {
  const { user, hasRole } = useAuthStore();
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeConversations: 0,
    documentsProcessed: 0,
    systemHealth: 95,
  });

  // Mock data for demonstration
  useEffect(() => {
    // Simulate loading stats
    setTimeout(() => {
      setStats({
        totalUsers: 1247,
        activeConversations: 89,
        documentsProcessed: 3456,
        systemHealth: 98,
      });
    }, 1000);
  }, []);

  const quickActions = [
    {
      title: 'Start AI Chat',
      description: 'Begin a new conversation with our AI assistant',
      icon: MessageSquare,
      href: '/chat',
      color: 'bg-blue-500',
      roles: ['user', 'analyst', 'admin']
    },
    {
      title: 'LLM Studio',
      description: 'Access advanced AI tools and models',
      icon: Brain,
      href: '/llm-studio',
      color: 'bg-purple-500',
      roles: ['user', 'analyst', 'admin']
    },
    {
      title: 'Analytics',
      description: 'View system analytics and insights',
      icon: BarChart3,
      href: '/analytics',
      color: 'bg-green-500',
      roles: ['analyst', 'admin']
    },
    {
      title: 'Process Documents',
      description: 'Upload and analyze documents',
      icon: FileText,
      href: '/documents',
      color: 'bg-orange-500',
      roles: ['user', 'analyst', 'admin']
    },
  ];

  const filteredQuickActions = quickActions.filter(action => 
    action.roles.some(role => hasRole(role))
  );

  const recentActivity = [
    {
      id: 1,
      type: 'chat',
      title: 'AI Conversation completed',
      description: 'Generated marketing strategy analysis',
      time: '2 minutes ago',
      status: 'completed'
    },
    {
      id: 2,
      type: 'document',
      title: 'Document processed',
      description: 'Financial report summarized',
      time: '15 minutes ago',
      status: 'completed'
    },
    {
      id: 3,
      type: 'user',
      title: 'New user registered',
      description: 'john.smith@company.com joined',
      time: '1 hour ago',
      status: 'info'
    },
    {
      id: 4,
      type: 'system',
      title: 'System update',
      description: 'LLM models updated to latest version',
      time: '3 hours ago',
      status: 'info'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome back, {user?.first_name || user?.username || 'User'}!
          </h1>
          <p className="text-muted-foreground">
            Here's what's happening with your Enterprise AI system today.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="text-green-600 border-green-600">
            <Activity className="w-3 h-3 mr-1" />
            System Healthy
          </Badge>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalUsers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+12.5%</span> from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Conversations</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeConversations}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+8.2%</span> from yesterday
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents Processed</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.documentsProcessed.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+23.1%</span> from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.systemHealth}%</div>
            <Progress value={stats.systemHealth} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Get started with common tasks
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {filteredQuickActions.map((action) => {
              const Icon = action.icon;
              return (
                <div key={action.title} className="flex items-center space-x-4 p-3 rounded-lg border hover:bg-accent transition-colors">
                  <div className={`w-10 h-10 ${action.color} rounded-lg flex items-center justify-center`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium">{action.title}</h4>
                    <p className="text-sm text-muted-foreground">{action.description}</p>
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <a href={action.href}>Go</a>
                  </Button>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Latest system events and updates
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-accent transition-colors">
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  activity.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                }`} />
                <div className="flex-1 space-y-1">
                  <h4 className="text-sm font-medium">{activity.title}</h4>
                  <p className="text-sm text-muted-foreground">{activity.description}</p>
                  <div className="flex items-center text-xs text-muted-foreground">
                    <Clock className="w-3 h-3 mr-1" />
                    {activity.time}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* System Status */}
      {hasRole('admin') && (
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>
              Overview of system components and health
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">API Gateway</span>
                  <Badge variant="outline" className="text-green-600 border-green-600">Healthy</Badge>
                </div>
                <Progress value={99} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Database</span>
                  <Badge variant="outline" className="text-green-600 border-green-600">Healthy</Badge>
                </div>
                <Progress value={97} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">LLM Services</span>
                  <Badge variant="outline" className="text-green-600 border-green-600">Healthy</Badge>
                </div>
                <Progress value={98} className="h-2" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;


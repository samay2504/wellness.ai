import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  ChartBarIcon, 
  UserIcon, 
  CogIcon, 
  DocumentTextIcon,
  EyeIcon,
  CalendarIcon,
  BellIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const navigation = [
    {
      name: 'Dashboard',
      href: '/',
      icon: HomeIcon,
      current: location.pathname === '/'
    },
    {
      name: 'Eye Tracker',
      href: '/eye-tracker',
      icon: EyeIcon,
      current: location.pathname === '/eye-tracker'
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: ChartBarIcon,
      current: location.pathname === '/analytics'
    },
    {
      name: 'Eye Tracker',
      href: '/eye-tracker',
      icon: EyeIcon,
      current: location.pathname === '/eye-tracker'
    },
    {
      name: 'Eye Health',
      href: '/eye-health',
      icon: EyeIcon,
      current: location.pathname === '/eye-health'
    },
    {
      name: 'Reports',
      href: '/reports',
      icon: DocumentTextIcon,
      current: location.pathname === '/reports'
    },
    {
      name: 'Calendar',
      href: '/calendar',
      icon: CalendarIcon,
      current: location.pathname === '/calendar'
    },
    {
      name: 'Notifications',
      href: '/notifications',
      icon: BellIcon,
      current: location.pathname === '/notifications'
    },
    {
      name: 'Profile',
      href: '/profile',
      icon: UserIcon,
      current: location.pathname === '/profile'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: CogIcon,
      current: location.pathname === '/settings'
    }
  ];

  const quickStats = [
    {
      name: 'Today\'s Blinks',
      value: '1,247',
      change: '+12%',
      changeType: 'positive'
    },
    {
      name: 'Eye Strain Score',
      value: 'Low',
      change: '-5%',
      changeType: 'positive'
    },
    {
      name: 'Active Hours',
      value: '6.5h',
      change: '+0.5h',
      changeType: 'positive'
    }
  ];

  return (
    <div className={`bg-white border-r border-gray-200 dark:bg-gray-800 dark:border-gray-700 transition-all duration-300 ${
      collapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <EyeIcon className="h-6 w-6 text-blue-600" />
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                WaW
              </span>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {collapsed ? (
              <ChevronRightIcon className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronLeftIcon className="h-4 w-4 text-gray-500" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors ${
                  item.current
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
                }`}
              >
                <Icon className={`mr-3 h-5 w-5 flex-shrink-0 ${
                  item.current ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                }`} />
                {!collapsed && item.name}
              </Link>
            );
          })}
        </nav>

        {/* Quick Stats */}
        {!collapsed && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Quick Stats
            </h3>
            <div className="space-y-3">
              {quickStats.map((stat) => (
                <div key={stat.name} className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{stat.name}</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{stat.value}</p>
                  </div>
                  <span className={`text-xs ${
                    stat.changeType === 'positive' 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {stat.change}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* User Info */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-medium text-sm">U</span>
            </div>
            {!collapsed && (
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900 dark:text-white">User Name</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">user@example.com</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar; 
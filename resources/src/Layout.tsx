import { useState, useEffect } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { FileText, Settings, LayoutDashboard, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from './lib/utils';
import { AthanorIcon } from './components/AthanorIcon';

export function Layout() {
  const location = useLocation();
  const isDocPage = !!location.pathname.match(/^\/documents\/[^/]+/);
  const [collapsed, setCollapsed] = useState(isDocPage);

  useEffect(() => {
    setCollapsed(isDocPage);
  }, [isDocPage]);

  const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Providers', href: '/providers', icon: Settings },
  ];

  const isFullWidthPage = location.pathname.startsWith('/documents/');

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className={cn(
        "bg-white border-r border-gray-200 flex flex-col shrink-0 transition-all duration-200",
        collapsed ? "w-16" : "w-64"
      )}>
        <div className={cn("h-16 flex items-center border-b border-gray-200", collapsed ? "justify-center px-2" : "px-6")}>
          <AthanorIcon className="w-6 h-6 text-indigo-600 shrink-0" />
          {!collapsed && <span className="text-lg font-bold text-gray-900 ml-2">DocAlchemy</span>}
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-3">
            {navItems.map((item) => (
              <li key={item.name}>
                <Link
                  to={item.href}
                  title={collapsed ? item.name : undefined}
                  className={cn(
                    "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                    location.pathname === item.href || (item.href !== '/' && location.pathname.startsWith(item.href))
                      ? "bg-indigo-50 text-indigo-600"
                      : "text-gray-700 hover:bg-gray-100"
                  )}
                >
                  <item.icon
                    className={cn(
                      "flex-shrink-0 h-5 w-5",
                      collapsed ? "" : "mr-3",
                      location.pathname === item.href || (item.href !== '/' && location.pathname.startsWith(item.href))
                        ? "text-indigo-600"
                        : "text-gray-400 group-hover:text-gray-500"
                    )}
                  />
                  {!collapsed && item.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="border-t border-gray-200 p-2">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {!isFullWidthPage && (
          <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm z-10 shrink-0">
            <h1 className="text-xl font-semibold text-gray-800">
              {navItems.find(i => location.pathname === i.href || (i.href !== '/' && location.pathname.startsWith(i.href)))?.name || 'Dashboard'}
            </h1>
          </header>
        )}

        <div className={cn("flex-1 overflow-auto bg-gray-50", isFullWidthPage ? "" : "p-6")}>
          <div className={cn("mx-auto h-full", isFullWidthPage ? "" : "max-w-7xl")}>
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}

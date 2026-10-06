"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, LineChart } from "lucide-react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/leads", label: "Ranked Leads", icon: Users },
    { href: "/analytics", label: "Analytics", icon: LineChart },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-paper-50 text-ink-900">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-paper-100 border-r border-line-200 flex flex-col">
        <div className="p-6 border-b border-line-200">
          <h1 className="text-xl font-bold tracking-tight">CRM Intelligence</h1>
        </div>
        <nav className="flex-1 p-4 flex flex-col gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${
                  isActive 
                    ? "bg-focus-50 text-focus-600 font-medium" 
                    : "text-ink-900/70 hover:bg-paper-200 hover:text-ink-900"
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header */}
        <header className="px-8 py-6 border-b border-line-200 bg-white flex items-center justify-between sticky top-0 z-10">
          <h2 className="text-lg font-medium tracking-tight">
            {navItems.find((item) => pathname.startsWith(item.href))?.label || "Overview"}
          </h2>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

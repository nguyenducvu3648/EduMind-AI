"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  MessageSquare,
  BookOpen,
  UserCircle,
  Plus,
  LogOut,
  GraduationCap,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";
import { listSessions } from "@/lib/sessions";
import type { SessionItem } from "@/types";
import { toast } from "sonner";

const navItems = [
  { href: "/chat", label: "Trò chuyện", icon: MessageSquare },
  { href: "/wiki", label: "Tài liệu", icon: BookOpen },
  { href: "/profile", label: "Hồ sơ", icon: UserCircle },
];

function getInitials(email: string): string {
  if (!email) return "?";
  const name = email.split("@")[0];
  return name.substring(0, 2).toUpperCase();
}

function getGradeLabel(grade: number | null): string {
  if (!grade) return "Chưa cập nhật";
  return `Lớp ${grade}`;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading, logout } = useAuth();
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  const fetchSessions = useCallback(async () => {
    if (!user) return;
    try {
      const data = await listSessions();
      setSessions(data);
    } catch {
      // Silent fail
    }
  }, [user]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Auto-refresh session list every 5s while user is on chat pages
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      // Only poll when on chat pages (user might be chatting actively)
      if (pathname?.startsWith("/chat")) {
        listSessions().then(setSessions).catch(() => {});
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [user, pathname]);

  // Also refresh when navigating back to chat list
  useEffect(() => {
    if (pathname === "/chat") {
      fetchSessions();
    }
  }, [pathname, fetchSessions]);

  const handleNewChat = () => {
    router.push("/chat");
  };

  const handleLogout = () => {
    logout();
    toast.success("Đã đăng xuất");
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!user) return null;

  const currentPath = pathname || "/chat";

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={`flex flex-col border-r border-border bg-sidebar transition-all duration-200 ${
          collapsed ? "w-[60px]" : "w-[280px]"
        }`}
      >
        {/* Logo & Brand */}
        <div className="flex items-center justify-between p-3 border-b border-border">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <GraduationCap className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-semibold text-sm">MathMentor AI</span>
            </div>
          )}
          {collapsed && (
            <div className="w-8 h-8 mx-auto rounded-lg bg-primary flex items-center justify-center">
              <GraduationCap className="w-4 h-4 text-primary-foreground" />
            </div>
          )}
        </div>

        {/* New Chat Button */}
        <div className="p-3" title="Chat mới">
          <Button
            variant="default"
            className={`w-full gap-2 ${collapsed ? "px-0 justify-center" : ""}`}
            onClick={handleNewChat}
          >
            <Plus className="w-4 h-4" />
            {!collapsed && "Chat mới"}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="px-2 space-y-1">
          {navItems.map((item) => {
            const isActive =
              item.href === "/chat"
                ? currentPath.startsWith("/chat")
                : currentPath.startsWith(item.href);
            return (
              <div key={item.href} title={collapsed ? item.label : undefined}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={`w-full justify-start gap-3 ${
                    collapsed ? "px-0 justify-center" : ""
                  }`}
                  onClick={() => router.push(item.href)}
                >
                  <item.icon className="w-4 h-4 shrink-0" />
                  {!collapsed && (
                    <span className="text-sm">{item.label}</span>
                  )}
                </Button>
              </div>
            );
          })}
        </nav>

        <Separator className="my-2" />

        {/* Session History */}
        {!collapsed && (
          <div className="px-3 py-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Lịch sử chat
            </p>
          </div>
        )}
        <ScrollArea className="flex-1 px-2">
          <div className="space-y-1 py-1">
            {sessions.map((s) => (
              <div
                key={s.id}
                title={
                  collapsed
                    ? s.last_message || "Cuộc trò chuyện"
                    : undefined
                }
              >
                <Button
                  variant="ghost"
                  className={`w-full justify-start text-left h-auto py-2 ${
                    collapsed ? "px-0 justify-center" : ""
                  }`}
                  onClick={() => router.push(`/chat/${s.id}`)}
                >
                  <MessageSquare className="w-3.5 h-3.5 shrink-0 text-muted-foreground" />
                  {!collapsed && (
                    <span className="text-xs truncate ml-2">
                      {s.last_message || "Cuộc trò chuyện mới"}
                    </span>
                  )}
                </Button>
              </div>
            ))}
          </div>
        </ScrollArea>

        {/* Collapse Toggle */}
        <div className="p-2 border-t border-border" title={collapsed ? "Mở rộng" : "Thu gọn"}>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-center"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
            {!collapsed && (
              <span className="text-xs ml-2">Thu gọn</span>
            )}
          </Button>
        </div>

        {/* User Info & Logout */}
        <div className="p-3 border-t border-border">
          <div className={`flex items-center gap-3 ${collapsed ? "justify-center" : ""}`}>
            <div title={user.email}>
              <Avatar className="w-8 h-8 cursor-pointer">
                <AvatarFallback className="bg-primary/10 text-primary text-xs">
                  {getInitials(user.email)}
                </AvatarFallback>
              </Avatar>
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {user.email.split("@")[0]}
                </p>
                <p className="text-xs text-muted-foreground">
                  {getGradeLabel(user.grade_level)}
                </p>
              </div>
            )}
            <div className="flex items-center gap-1">
              <div title="Đăng xuất">
                <Button
                  variant="ghost"
                  size="icon"
                  className="shrink-0"
                  onClick={handleLogout}
                >
                  <LogOut className="w-4 h-4 text-muted-foreground" />
                </Button>
            </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {children}
      </main>
    </div>
  );
}

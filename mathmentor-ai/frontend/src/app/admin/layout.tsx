"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shield, ArrowLeft, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [adminUser, setAdminUser] = useState<{ email: string } | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("admin_user");
    if (stored) {
      try {
        setAdminUser(JSON.parse(stored));
      } catch {
        // ignore
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_user");
    setAdminUser(null);
    toast.success("Đã đăng xuất admin");
    router.refresh();
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Admin header bar */}
      <header className="flex items-center justify-between px-4 h-14 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push("/chat")}
            title="Quay lại ứng dụng"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
            <Shield className="w-4 h-5 text-amber-700" />
          </div>
          <div>
            <h1 className="text-sm font-semibold">Admin Dashboard</h1>
            <p className="text-[10px] text-muted-foreground">
              MathMentor AI — Quản trị hệ thống
            </p>
          </div>
        </div>

        {adminUser && (
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">
              {adminUser.email}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-xs"
            >
              <LogOut className="w-3.5 h-3.5 mr-1" />
              Đăng xuất
            </Button>
          </div>
        )}
      </header>

      {/* Content */}
      <ScrollArea className="flex-1">{children}</ScrollArea>
    </div>
  );
}

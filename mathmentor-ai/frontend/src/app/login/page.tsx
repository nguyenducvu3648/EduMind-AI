"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Loader2, GraduationCap, BookOpen, Brain } from "lucide-react";
import { toast } from "sonner";
import { login as apiLogin, register as apiRegister } from "@/lib/auth";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();

  const [loading, setLoading] = useState(false);

  // Login form
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regGrade, setRegGrade] = useState("10");

  const handleLogin = async () => {
    if (!loginEmail || !loginPassword) {
      toast.error("Vui lòng nhập email và mật khẩu");
      return;
    }
    setLoading(true);
    try {
      const result = await apiLogin(loginEmail, loginPassword);
      login(result.user, result.access_token, result.refresh_token);
      toast.success("Đăng nhập thành công!");
    } catch {
      toast.error("Đăng nhập thất bại. Kiểm tra email và mật khẩu.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!regEmail || !regPassword) {
      toast.error("Vui lòng nhập đầy đủ thông tin");
      return;
    }
    if (regPassword.length < 8) {
      toast.error("Mật khẩu phải có ít nhất 8 ký tự");
      return;
    }
    setLoading(true);
    try {
      const result = await apiRegister(regEmail, regPassword, parseInt(regGrade));
      login(result.user, result.access_token, result.refresh_token);
      toast.success("Đăng ký thành công!");
    } catch {
      toast.error("Đăng ký thất bại. Email có thể đã tồn tại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo & Brand */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary shadow-lg shadow-primary/20 mb-2">
            <GraduationCap className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold text-foreground">MathMentor AI</h1>
          <p className="text-muted-foreground text-sm">
            Gia sư Toán THPT cá nhân hóa với AI
          </p>
        </div>

        <Card className="shadow-xl border-border/50">
          <Tabs defaultValue="login" className="w-full">
            <CardHeader className="pb-4">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Đăng nhập</TabsTrigger>
                <TabsTrigger value="register">Đăng ký</TabsTrigger>
              </TabsList>
            </CardHeader>

            <CardContent>
              <TabsContent value="login" className="space-y-4 mt-0">
                <CardTitle className="text-lg">Chào mừng trở lại</CardTitle>
                <CardDescription className="pb-2">
                  Đăng nhập để tiếp tục học tập
                </CardDescription>

                <div className="space-y-2">
                  <Label htmlFor="login-email">Email</Label>
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="student@example.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password">Mật khẩu</Label>
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                  />
                </div>
                <Button
                  className="w-full"
                  onClick={handleLogin}
                  disabled={loading}
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : null}
                  Đăng nhập
                </Button>
              </TabsContent>

              <TabsContent value="register" className="space-y-4 mt-0">
                <CardTitle className="text-lg">Tạo tài khoản mới</CardTitle>
                <CardDescription className="pb-2">
                  Bắt đầu hành trình học Toán thông minh
                </CardDescription>

                <div className="space-y-2">
                  <Label htmlFor="reg-email">Email</Label>
                  <Input
                    id="reg-email"
                    type="email"
                    placeholder="student@example.com"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reg-password">Mật khẩu (tối thiểu 8 ký tự)</Label>
                  <Input
                    id="reg-password"
                    type="password"
                    placeholder="••••••••"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reg-grade">Lớp</Label>
                  <select
                    id="reg-grade"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    value={regGrade}
                    onChange={(e) => setRegGrade(e.target.value)}
                  >
                    <option value="10">Lớp 10</option>
                    <option value="11">Lớp 11</option>
                    <option value="12">Lớp 12</option>
                  </select>
                </div>
                <Button
                  className="w-full"
                  onClick={handleRegister}
                  disabled={loading}
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : null}
                  Đăng ký
                </Button>
              </TabsContent>

              <Separator className="my-4" />

              <div className="flex items-center justify-center gap-6 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5" /> Cá nhân hóa
                </span>
                <span className="flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5" /> RAG Knowledge
                </span>
                <span className="flex items-center gap-1.5">
                  <GraduationCap className="w-3.5 h-3.5" /> Lớp 10–12
                </span>
              </div>
            </CardContent>
          </Tabs>
        </Card>
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Shield,
  Database,
  FileText,
  BarChart3,
  Loader2,
  CheckCircle2,
  XCircle,
  Key,
  Upload,
  Play,
  LogIn,
  Users,
} from "lucide-react";
import DashboardTab from "@/components/admin/DashboardTab";
import UsersTab from "@/components/admin/UsersTab";
import { toast } from "sonner";
import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function AdminPage() {
  const [adminUser, setAdminUser] = useState<{ email: string } | null>(null);
  const [token, setToken] = useState<string | null>(null);

  // Login form
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);

  // Ingest: path mode
  const [ingestPath, setIngestPath] = useState("wiki_content/grade_12");
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<Record<string, unknown> | null>(null);

  // Ingest: upload mode
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<Record<string, unknown> | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // Evaluation
  const [evalType, setEvalType] = useState("rag_quality");
  const [evalSample, setEvalSample] = useState("20");
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("admin_user");
    const storedToken = localStorage.getItem("admin_token");
    if (storedUser && storedToken) {
      try {
        setAdminUser(JSON.parse(storedUser));
        setToken(storedToken);
      } catch {
        /* ignore */
      }
    }
  }, []);

  const api = () =>
    axios.create({
      baseURL: API_BASE,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

  const handleLogin = async () => {
    if (!loginEmail || !loginPassword) {
      toast.error("Vui lòng nhập email và mật khẩu admin");
      return;
    }
    setLoggingIn(true);
    try {
      const res = await axios.post(`${API_BASE}/admin/auth/login`, {
        email: loginEmail,
        password: loginPassword,
      });
      const { access_token, user } = res.data;
      localStorage.setItem("admin_token", access_token);
      localStorage.setItem("admin_user", JSON.stringify(user));
      setToken(access_token);
      setAdminUser(user);
      toast.success("Đăng nhập admin thành công!");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response: { data?: { detail?: string } } }).response?.data?.detail ||
            "Đăng nhập thất bại"
          : "Không thể kết nối backend";
      toast.error(msg);
    } finally {
      setLoggingIn(false);
    }
  };

  const handleIngest = async () => {
    if (!ingestPath.trim()) {
      toast.error("Vui lòng nhập đường dẫn");
      return;
    }
    setIngesting(true);
    setIngestResult(null);
    try {
      const res = await api().post("/admin/wiki/ingest", {
        path: ingestPath,
        generate_embeddings: false,
      });
      setIngestResult(res.data);
      toast.success("Ingest thành công!");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response: { data?: { detail?: string } } }).response?.data?.detail ||
            "Ingest thất bại"
          : "Không thể kết nối backend";
      toast.error(msg);
      setIngestResult({ error: msg });
    } finally {
      setIngesting(false);
    }
  };

  const handleUpload = async () => {
    if (uploadFiles.length === 0) {
      toast.error("Vui lòng chọn file .md");
      return;
    }
    setUploading(true);
    setUploadResult(null);
    try {
      const form = new FormData();
      uploadFiles.forEach((f) => form.append("files", f));
      const res = await api().post("/admin/wiki/ingest/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadResult(res.data);
      toast.success("Upload & ingest thành công!");
      setUploadFiles([]);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response: { data?: { detail?: string } } }).response?.data?.detail ||
            "Upload thất bại"
          : "Không thể kết nối backend";
      toast.error(msg);
      setUploadResult({ error: msg });
    } finally {
      setUploading(false);
    }
  };

  const handleEvaluate = async () => {
    setEvaluating(true);
    setEvalResult(null);
    try {
      const res = await api().post("/admin/evaluation/run", {
        run_type: evalType,
        sample_size: parseInt(evalSample),
      });
      setEvalResult(res.data);
      toast.success("Evaluation hoàn tất!");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response: { data?: { detail?: string } } }).response?.data?.detail ||
            "Evaluation thất bại"
          : "Không thể kết nối backend";
      toast.error(msg);
      setEvalResult({ error: msg });
    } finally {
      setEvaluating(false);
    }
  };

  const evalLabels: Record<string, string> = {
    rag_quality: "Chất lượng RAG",
    response_quality: "Chất lượng phản hồi",
    personalization: "Cá nhân hóa",
  };

  // ── Not logged in: show login form ──
  if (!adminUser || !token) {
    return (
      <div className="min-h-full flex items-center justify-center p-6">
        <Card className="w-full max-w-md shadow-xl border-border/50">
          <CardHeader className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-amber-100 mx-auto mb-2">
              <Shield className="w-6 h-6 text-amber-700" />
            </div>
            <CardTitle className="text-lg">Admin Login</CardTitle>
            <CardDescription className="text-xs">
              Đăng nhập với tài khoản admin để quản trị hệ thống
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="admin-email">Email</Label>
              <Input
                id="admin-email"
                type="email"
                placeholder="admin@example.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="admin-password">Mật khẩu</Label>
              <Input
                id="admin-password"
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
              disabled={loggingIn}
            >
              {loggingIn ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <LogIn className="w-4 h-4 mr-2" />
              )}
              Đăng nhập
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Logged in: show dashboard ──
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        Admin: {adminUser.email}
      </Badge>

      <Tabs defaultValue="dashboard">
        <TabsList>
          <TabsTrigger value="dashboard">
            <BarChart3 className="w-4 h-4 mr-1.5" />
            Tiến độ
          </TabsTrigger>
          <TabsTrigger value="ingest">
            <Upload className="w-4 h-4 mr-1.5" />
            Ingest Wiki
          </TabsTrigger>
          <TabsTrigger value="users">
            <Users className="w-4 h-4 mr-1.5" />
            Người dùng
          </TabsTrigger>
          <TabsTrigger value="evaluate">
            <BarChart3 className="w-4 h-4 mr-1.5" />
            Evaluation
          </TabsTrigger>
        </TabsList>

        {/* Ingest Tab */}
        <TabsContent value="ingest" className="space-y-4 mt-4">
          {/* Path mode */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                Ingest từ đường dẫn server
              </CardTitle>
              <CardDescription className="text-xs">
                Nhập đường dẫn file .md hoặc thư mục chứa markdown trên server
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2">
                <Input
                  placeholder="wiki_content/grade_12"
                  value={ingestPath}
                  onChange={(e) => setIngestPath(e.target.value)}
                />
                <Button
                  onClick={handleIngest}
                  disabled={ingesting}
                >
                  {ingesting ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Database className="w-4 h-4 mr-2" />
                  )}
                  Ingest
                </Button>
              </div>
              {ingestResult && (
                <div className="p-3 rounded-lg bg-muted/50 space-y-1 text-sm">
                  {ingestResult.error ? (
                    <div className="flex items-center gap-2 text-red-600">
                      <XCircle className="w-4 h-4" />
                      {(ingestResult.error as string) || "Thất bại"}
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-2 text-emerald-600">
                        <CheckCircle2 className="w-4 h-4" />
                        Ingest thành công
                      </div>
                      <p>
                        Article: {ingestResult.total_articles as number} |
                        Chunks: {ingestResult.total_chunks as number} |
                        Lỗi: {(ingestResult.errors as string[])?.length || 0}
                      </p>
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Upload mode */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Upload className="w-4 h-4 text-primary" />
                Tải lên file .md từ máy tính
              </CardTitle>
              <CardDescription className="text-xs">
                Kéo thả hoặc chọn file .md để upload và ingest trực tiếp
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  dragOver
                    ? "border-primary bg-primary/5"
                    : "border-muted-foreground/30 hover:border-muted-foreground/50"
                }`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  const dropped = Array.from(e.dataTransfer.files).filter(
                    (f) => f.name.endsWith(".md")
                  );
                  if (dropped.length === 0) {
                    toast.error("Chỉ chấp nhận file .md");
                    return;
                  }
                  setUploadFiles((prev) => [...prev, ...dropped]);
                }}
                onClick={() => document.getElementById("md-file-input")?.click()}
              >
                <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground/60" />
                <p className="text-sm text-muted-foreground">
                  Kéo thả file .md vào đây hoặc click để chọn
                </p>
              </div>
              <input
                id="md-file-input"
                type="file"
                accept=".md"
                multiple
                className="hidden"
                onChange={(e) => {
                  const selected = Array.from(e.target.files || []);
                  setUploadFiles((prev) => [...prev, ...selected]);
                  e.target.value = "";
                }}
              />
              {uploadFiles.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">
                    Đã chọn {uploadFiles.length} file:
                  </p>
                  <div className="max-h-32 overflow-y-auto space-y-1">
                    {uploadFiles.map((f, i) => (
                      <div
                        key={`${f.name}-${i}`}
                        className="flex items-center justify-between text-xs bg-muted/30 px-2 py-1 rounded"
                      >
                        <span className="truncate">{f.name}</span>
                        <button
                          className="text-red-500 hover:text-red-700 ml-2 shrink-0"
                          onClick={() =>
                            setUploadFiles((prev) => prev.filter((_, j) => j !== i))
                          }
                        >
                          <XCircle className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex gap-2">
                {uploadFiles.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setUploadFiles([])}
                  >
                    Xoá tất cả
                  </Button>
                )}
                <Button
                  onClick={handleUpload}
                  disabled={uploading || uploadFiles.length === 0}
                  className="flex-1"
                >
                  {uploading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Upload className="w-4 h-4 mr-2" />
                  )}
                  Upload & Ingest ({uploadFiles.length} file)
                </Button>
              </div>
              {uploadResult && (
                <div className="p-3 rounded-lg bg-muted/50 space-y-1 text-sm">
                  {uploadResult.error ? (
                    <div className="flex items-center gap-2 text-red-600">
                      <XCircle className="w-4 h-4" />
                      {(uploadResult.error as string) || "Upload thất bại"}
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-2 text-emerald-600">
                        <CheckCircle2 className="w-4 h-4" />
                        Upload & Ingest thành công
                      </div>
                      <p>
                        Article: {uploadResult.total_articles as number} |
                        Chunks: {uploadResult.total_chunks as number} |
                        Lỗi: {(uploadResult.errors as string[])?.length || 0}
                      </p>
                      {(uploadResult.errors as string[])?.length > 0 && (
                        <div className="mt-1 text-xs text-red-500 space-y-0.5">
                          {(uploadResult.errors as string[]).map((e, i) => (
                            <p key={i}>- {e}</p>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Dashboard Tab */}
        <DashboardTab apiBase={API_BASE} adminKey="" />

        {/* Users Tab */}
        <UsersTab apiBase={API_BASE} />

        {/* Evaluation Tab */}
        <TabsContent value="evaluate" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                Đánh giá chất lượng
              </CardTitle>
              <CardDescription className="text-xs">
                Chạy các bài kiểm tra để đo lường hiệu năng hệ thống
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Loại</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={evalType}
                    onChange={(e) => setEvalType(e.target.value)}
                  >
                    <option value="rag_quality">RAG Quality</option>
                    <option value="response_quality">Response Quality</option>
                    <option value="personalization">Personalization</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Số mẫu</label>
                  <Input
                    type="number"
                    min={1}
                    max={1000}
                    value={evalSample}
                    onChange={(e) => setEvalSample(e.target.value)}
                  />
                </div>
              </div>
              <Button
                onClick={handleEvaluate}
                disabled={evaluating}
                className="w-full"
              >
                {evaluating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                Chạy {evalLabels[evalType] || evalType}
              </Button>
              {evalResult && (
                <div className="mt-3 p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 mb-2 text-sm font-medium">
                    {evalResult.error ? (
                      <>
                        <XCircle className="w-4 h-4 text-red-600" />
                        <span className="text-red-600">Lỗi</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span className="text-emerald-600">Kết quả</span>
                      </>
                    )}
                  </div>
                  <pre className="text-xs whitespace-pre-wrap bg-background p-2 rounded border">
                    {JSON.stringify(evalResult, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Shield,
  Database,
  FileText,
  BarChart3,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Key,
  Upload,
  Play,
} from "lucide-react";
import DashboardTab from "@/components/admin/DashboardTab";
import { toast } from "sonner";
import axios from "axios";
import { useAuth } from "@/hooks/useAuth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function AdminPage() {
  const { user } = useAuth();
  const [adminKey, setAdminKey] = useState("");
  const [authenticated, setAuthenticated] = useState(false);

  // Ingest
  const [ingestPath, setIngestPath] = useState("wiki_content/grade_12");
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<Record<string, unknown> | null>(null);

  // Evaluation
  const [evalType, setEvalType] = useState("rag_quality");
  const [evalSample, setEvalSample] = useState("20");
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<Record<string, unknown> | null>(null);

  const api = () =>
    axios.create({
      baseURL: API_BASE,
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Api-Key": adminKey,
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    });

  const handleAuth = () => {
    if (!adminKey.trim()) {
      toast.error("Vui lòng nhập Admin API Key");
      return;
    }
    setAuthenticated(true);
    toast.success("Xác thực admin thành công");
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

  return (
    <ScrollArea className="flex-1">
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
            <Shield className="w-5 h-5 text-amber-700" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Admin Dashboard</h1>
            <p className="text-sm text-muted-foreground">
              Quản lý hệ thống MathMentor AI
            </p>
          </div>
        </div>

        {/* API Key */}
        {!authenticated ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Key className="w-4 h-4 text-amber-500" />
                Xác thực Admin
              </CardTitle>
              <CardDescription className="text-xs">
                Nhập Admin API Key từ file .env để truy cập
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input
                type="password"
                placeholder="Nhập Admin API Key..."
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAuth()}
              />
              <Button onClick={handleAuth} className="w-full">
                <Shield className="w-4 h-4 mr-2" />
                Xác thực
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              Đã xác thực Admin
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
                <TabsTrigger value="evaluate">
                  <BarChart3 className="w-4 h-4 mr-1.5" />
                  Evaluation
                </TabsTrigger>
              </TabsList>

              {/* Ingest Tab */}
              <TabsContent value="ingest" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary" />
                      Ingest tài liệu Wiki
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Nhập đường dẫn file .md hoặc thư mục chứa markdown
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
                      <div className="mt-3 p-3 rounded-lg bg-muted/50 space-y-1 text-sm">
                        {ingestResult.error ? (
                          <div className="flex items-center gap-2 text-red-600">
                            <XCircle className="w-4 h-4" />
                            {ingestResult.error as string}
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
              </TabsContent>

              {/* Dashboard Tab */}
              <DashboardTab apiBase={API_BASE} adminKey={adminKey} />

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
          </>
        )}
      </div>
    </ScrollArea>
  );
}

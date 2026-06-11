"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { TabsContent } from "@/components/ui/tabs";
import {
  Users,
  MessageSquare,
  BookOpen,
  Brain,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  GraduationCap,
  Loader2,
  BarChart4,
  Activity,
} from "lucide-react";
import axios from "axios";

interface Stats {
  users: {
    total: number;
    new_7d: number;
    struggling: number;
    active_learners: number;
  };
  sessions: { total: number; active_7d: number };
  interactions: {
    total: number;
    last_7d: number;
    daily: { date: string; count: number }[];
  };
  learning: {
    topic_distribution: Record<string, number>;
    strategy_usage: Record<string, number>;
    top_weak_topics: { topic: string; count: number }[];
  };
  knowledge_base: { total_chunks: number; with_embedding: number };
}

export default function DashboardTab({
  apiBase,
  adminKey,
}: {
  apiBase: string;
  adminKey: string;
}) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const adminToken = localStorage.getItem("admin_token");
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        // Try JWT first (admin page), fallback API Key (old flow)
        if (adminToken) {
          headers["Authorization"] = `Bearer ${adminToken}`;
        } else if (adminKey) {
          headers["X-Admin-Api-Key"] = adminKey;
          headers["Authorization"] = `Bearer ${localStorage.getItem("access_token")}`;
        }
        const res = await axios.get(`${apiBase}/admin/dashboard/stats`, { headers });
        setStats(res.data);
      } catch {
        // silent
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [apiBase, adminKey]);

  if (loading) {
    return (
      <TabsContent value="dashboard" className="space-y-4 mt-4">
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      </TabsContent>
    );
  }

  if (!stats) {
    return (
      <TabsContent value="dashboard" className="space-y-4 mt-4">
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground text-sm">
            Không thể tải dữ liệu
          </CardContent>
        </Card>
      </TabsContent>
    );
  }

  const strategyLabels: Record<string, string> = {
    socratic: "Socratic",
    step_by_step: "Từng bước",
    direct: "Giải thích",
    hint_first: "Gợi ý",
    worked_example: "Ví dụ mẫu",
    metacognitive: "Siêu nhận thức",
  };

  return (
    <TabsContent value="dashboard" className="space-y-4 mt-4">
      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-2 text-primary mb-1">
              <Users className="w-4 h-4" />
              <span className="text-xs text-muted-foreground">Người dùng</span>
            </div>
            <p className="text-2xl font-bold">{stats.users.total}</p>
            <p className="text-xs text-muted-foreground">
              +{stats.users.new_7d} trong 7 ngày
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-2 text-emerald-500 mb-1">
              <MessageSquare className="w-4 h-4" />
              <span className="text-xs text-muted-foreground">Tương tác</span>
            </div>
            <p className="text-2xl font-bold">{stats.interactions.total}</p>
            <p className="text-xs text-muted-foreground">
              {stats.interactions.last_7d} trong 7 ngày
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-2 text-blue-500 mb-1">
              <Activity className="w-4 h-4" />
              <span className="text-xs text-muted-foreground">Session</span>
            </div>
            <p className="text-2xl font-bold">{stats.sessions.total}</p>
            <p className="text-xs text-muted-foreground">
              {stats.sessions.active_7d} hoạt động 7 ngày
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-2 text-amber-500 mb-1">
              <BookOpen className="w-4 h-4" />
              <span className="text-xs text-muted-foreground">Kiến thức</span>
            </div>
            <p className="text-2xl font-bold">{stats.knowledge_base.total_chunks}</p>
            <p className="text-xs text-muted-foreground">
              {stats.knowledge_base.with_embedding} có embedding
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Daily interactions bar chart */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              Tương tác theo ngày (7 ngày)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.interactions.daily.length === 0 ? (
              <div className="h-32 flex items-center justify-center text-sm text-muted-foreground">
                Chưa có dữ liệu
              </div>
            ) : (
              <div className="flex items-end gap-1 h-32">
                {stats.interactions.daily.map((d) => {
                  const maxCount = Math.max(
                    ...stats.interactions.daily.map((x) => x.count),
                    1
                  );
                  const height = Math.max(4, (d.count / maxCount) * 100);
                  return (
                    <div
                      key={d.date}
                      className="flex-1 flex flex-col items-center gap-1"
                    >
                      <span className="text-[10px] text-muted-foreground">
                        {d.count}
                      </span>
                      <div
                        className="w-full rounded-t bg-primary/60 hover:bg-primary transition-colors"
                        style={{ height: `${height}%` }}
                      />
                      <span className="text-[9px] text-muted-foreground rotate-45 origin-left whitespace-nowrap">
                        {d.date.slice(5)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Strategy usage pie */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Brain className="w-4 h-4 text-primary" />
              Chiến lược giảng dạy
            </CardTitle>
          </CardHeader>
          <CardContent>
            {Object.keys(stats.learning.strategy_usage).length === 0 ? (
              <div className="h-32 flex items-center justify-center text-sm text-muted-foreground">
                Chưa có dữ liệu
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(stats.learning.strategy_usage)
                  .sort(([, a], [, b]) => b - a)
                  .map(([key, count]) => {
                    const total = Object.values(
                      stats.learning.strategy_usage
                    ).reduce((a, b) => a + b, 0);
                    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                    return (
                      <div key={key}>
                        <div className="flex justify-between text-xs mb-0.5">
                          <span>{strategyLabels[key] || key}</span>
                          <span className="text-muted-foreground">
                            {count} ({pct}%)
                          </span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-primary transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Topic distribution */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <BarChart4 className="w-4 h-4 text-primary" />
              Chủ đề được học nhiều nhất
            </CardTitle>
          </CardHeader>
          <CardContent>
            {Object.keys(stats.learning.topic_distribution).length === 0 ? (
              <div className="h-32 flex items-center justify-center text-sm text-muted-foreground">
                Chưa có dữ liệu
              </div>
            ) : (
              <div className="space-y-1.5">
                {Object.entries(stats.learning.topic_distribution).map(
                  ([topic, count]) => (
                    <div key={topic} className="flex items-center gap-2">
                      <span className="text-xs flex-1 truncate capitalize">
                        {topic.replace(/_/g, " ")}
                      </span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-emerald-500 transition-all"
                          style={{
                            width: `${Math.min(
                              100,
                              (count /
                                Math.max(
                                  ...Object.values(
                                    stats.learning.topic_distribution
                                  )
                                )) *
                                100
                            )}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground w-6 text-right">
                        {count}
                      </span>
                    </div>
                  )
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Weak topics */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Chủ đề yếu phổ biến
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.learning.top_weak_topics.length === 0 ? (
              <div className="h-32 flex items-center justify-center text-sm text-muted-foreground">
                Chưa có dữ liệu
              </div>
            ) : (
              <div className="space-y-2">
                {stats.learning.top_weak_topics.map((item) => (
                  <div
                    key={item.topic}
                    className="flex items-center justify-between p-2 rounded-lg bg-amber-50 border border-amber-100"
                  >
                    <span className="text-xs capitalize">
                      {item.topic.replace(/_/g, " ")}
                    </span>
                    <Badge
                      variant="outline"
                      className="bg-amber-100 text-amber-700 border-amber-200 text-[10px]"
                    >
                      {item.count} học sinh
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* User insights */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Users className="w-4 h-4 text-primary" />
            Thông tin người học
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 rounded-lg bg-muted/50">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <Users className="w-4 h-4 text-emerald-500" />
              </div>
              <p className="text-lg font-bold text-emerald-600">
                {stats.users.active_learners}
              </p>
              <p className="text-xs text-muted-foreground">
                Học viên tích cực
              </p>
            </div>

            <div className="text-center p-3 rounded-lg bg-muted/50">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <GraduationCap className="w-4 h-4 text-blue-500" />
              </div>
              <p className="text-lg font-bold text-blue-600">
                {stats.sessions.active_7d}
              </p>
              <p className="text-xs text-muted-foreground">
                Session 7 ngày
              </p>
            </div>

            <div className="text-center p-3 rounded-lg bg-muted/50">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
              </div>
              <p className="text-lg font-bold text-amber-600">
                {stats.users.struggling}
              </p>
              <p className="text-xs text-muted-foreground">
                Đang gặp khó khăn
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </TabsContent>
  );
}

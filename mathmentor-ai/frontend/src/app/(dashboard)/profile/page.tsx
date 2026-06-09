"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  UserCircle,
  Brain,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  BookOpen,
  Zap,
  Target,
  BarChart3,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { getProfile, updateProfile } from "@/lib/profile";
import type { UserProfile } from "@/types";
import { toast } from "sonner";

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const [hintLevel, setHintLevel] = useState(0.5);
  const [stepPref, setStepPref] = useState(0.5);
  const [responsePref, setResponsePref] = useState("balanced");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      if (!user) return;
      try {
        const p = await getProfile(user.id);
        setProfile(p);
        setHintLevel(p.hint_dependency_level);
        setStepPref(p.step_by_step_preference);
        setResponsePref(p.response_preference);
      } catch {
        toast.error("Không thể tải thông tin hồ sơ");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user]);

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    try {
      const updated = await updateProfile(user.id, {
        response_preference: responsePref,
        hint_dependency_level: hintLevel,
        step_by_step_preference: stepPref,
      });
      setProfile(updated);
      toast.success("Đã lưu thay đổi");
    } catch {
      toast.error("Lưu thất bại");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const getGradeColor = (val: number) => {
    if (val >= 0.7) return "bg-emerald-500";
    if (val >= 0.4) return "bg-amber-500";
    return "bg-red-500";
  };

  return (
    <ScrollArea className="flex-1">
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
            <UserCircle className="w-7 h-7 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold">
              {user?.email?.split("@")[0] || "Học sinh"}
            </h1>
            <p className="text-sm text-muted-foreground">
              {user?.email} · Lớp {user?.grade_level || "?"}
            </p>
          </div>
        </div>

        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">
              <BarChart3 className="w-4 h-4 mr-1.5" />
              Tổng quan
            </TabsTrigger>
            <TabsTrigger value="topics">
              <BookOpen className="w-4 h-4 mr-1.5" />
              Kiến thức
            </TabsTrigger>
            <TabsTrigger value="preferences">
              <Zap className="w-4 h-4 mr-1.5" />
              Cài đặt
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                {
                  label: "Tốc độ học",
                  value: profile?.learning_speed ?? 0.5,
                  icon: TrendingUp,
                },
                {
                  label: "Ghi nhớ",
                  value: profile?.retention_strength ?? 0.5,
                  icon: Brain,
                },
                {
                  label: "Chịu tải",
                  value: profile?.cognitive_load_tolerance ?? 0.5,
                  icon: Target,
                },
                {
                  label: "Tái phạm lỗi",
                  value: 1 - (profile?.error_recurrence_rate ?? 0.3),
                  icon: AlertTriangle,
                },
              ].map((metric) => (
                <Card key={metric.label}>
                  <CardContent className="pt-4 pb-3">
                    <div className="flex items-center gap-2 mb-3">
                      <metric.icon className="w-4 h-4 text-primary" />
                      <span className="text-xs text-muted-foreground">
                        {metric.label}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${getGradeColor(
                            metric.value
                          )}`}
                          style={{ width: `${metric.value * 100}%` }}
                        />
                      </div>
                      <p className="text-right text-xs font-medium">
                        {Math.round(metric.value * 100)}%
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Chủ đề yếu
                </CardTitle>
              </CardHeader>
              <CardContent>
                {profile?.weak_topics && profile.weak_topics.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {profile.weak_topics.map((t) => (
                      <Badge
                        key={t}
                        variant="outline"
                        className="bg-amber-50 text-amber-700 border-amber-200"
                      >
                        {t.replace(/_/g, " ")}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Chưa xác định — hãy đặt câu hỏi để AI đánh giá
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Chủ đề mạnh
                </CardTitle>
              </CardHeader>
              <CardContent>
                {profile?.strong_topics && profile.strong_topics.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {profile.strong_topics.map((t) => (
                      <Badge
                        key={t}
                        variant="outline"
                        className="bg-emerald-50 text-emerald-700 border-emerald-200"
                      >
                        {t.replace(/_/g, " ")}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Chưa xác định
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Topics Tab */}
          <TabsContent value="topics" className="space-y-4 mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Brain className="w-4 h-4 text-primary" />
                  Mức độ thành thạo theo chủ đề
                </CardTitle>
                <CardDescription className="text-xs">
                  Điểm mastery được AI cập nhật sau mỗi tương tác
                </CardDescription>
              </CardHeader>
              <CardContent>
                {profile?.topic_mastery &&
                Object.keys(profile.topic_mastery).length > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(profile.topic_mastery)
                      .sort(([, a], [, b]) => b - a)
                      .map(([topic, mastery]) => (
                        <div key={topic}>
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-sm capitalize">
                              {topic.replace(/_/g, " ")}
                            </span>
                            <span className="text-xs font-medium text-muted-foreground">
                              {Math.round(mastery * 100)}%
                            </span>
                          </div>
                          <div className="h-2.5 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${getGradeColor(
                                mastery
                              )}`}
                              style={{ width: `${mastery * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Sparkles className="w-8 h-8 mx-auto mb-2" />
                    <p className="text-sm">
                      Hãy đặt câu hỏi để AI cá nhân hóa đánh giá
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences" className="space-y-4 mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Zap className="w-4 h-4 text-primary" />
                  Tùy chỉnh phương pháp học
                </CardTitle>
                <CardDescription className="text-xs">
                  Các lựa chọn này giúp AI điều chỉnh phong cách giảng dạy phù
                  hợp với bạn
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Response Preference */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Kiểu trả lời ưa thích
                  </label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={responsePref}
                    onChange={(e) => setResponsePref(e.target.value)}
                  >
                    <option value="short">Ngắn gọn</option>
                    <option value="balanced">Cân bằng</option>
                    <option value="long">Chi tiết</option>
                    <option value="explain_first">Giải thích trước</option>
                    <option value="solve_first">Giải trước</option>
                  </select>
                </div>

                <Separator />

                {/* Hint Dependency */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm font-medium">
                      Mức độ cần gợi ý
                    </label>
                    <span className="text-xs text-muted-foreground">
                      {Math.round(hintLevel * 100)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={hintLevel}
                    onChange={(e) => setHintLevel(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Tự giải</span>
                    <span>Cần hướng dẫn</span>
                  </div>
                </div>

                <Separator />

                {/* Step-by-step */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm font-medium">
                      Ưa thích từng bước
                    </label>
                    <span className="text-xs text-muted-foreground">
                      {Math.round(stepPref * 100)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={stepPref}
                    onChange={(e) => setStepPref(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Tổng quan</span>
                    <span>Từng bước</span>
                  </div>
                </div>

                <Button
                  onClick={handleSave}
                  disabled={saving}
                  className="w-full"
                >
                  {saving ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4 mr-2" />
                  )}
                  Lưu thay đổi
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </ScrollArea>
  );
}

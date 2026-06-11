"use client";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TabsContent } from "@/components/ui/tabs";
import {
  Users,
  Search,
  Loader2,
  Mail,
  Calendar,
  GraduationCap,
  Shield,
  UserCircle,
  Trash2,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  BookOpen,
  TrendingUp,
  ArrowUpDown,
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

interface UserItem {
  id: string;
  email: string;
  grade_level: number | null;
  role: string;
  created_at: string;
}

interface UserProfile {
  user_id: string;
  topic_mastery: Record<string, number>;
  weak_topics: string[];
  strong_topics: string[];
  learning_speed: number;
  retention_strength: number;
  error_recurrence_rate: number;
  updated_at: string;
}

export default function UsersTab({ apiBase }: { apiBase: string }) {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedUser, setSelectedUser] = useState<UserItem | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const token = () => localStorage.getItem("admin_token");

  const api = () =>
    axios.create({
      baseURL: apiBase,
      headers: { Authorization: `Bearer ${token()}` },
    });

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        skip: page * pageSize,
        limit: pageSize,
      };
      if (search.trim()) params.search = search.trim();
      const res = await api().get("/admin/users", { params });
      setUsers(res.data);
    } catch {
      toast.error("Không thể tải danh sách người dùng");
    } finally {
      setLoading(false);
    }
  }, [page, search]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const viewProfile = async (user: UserItem) => {
    setSelectedUser(user);
    setProfileLoading(true);
    setProfile(null);
    try {
      const res = await api().get(`/admin/users/${user.id}/profile`);
      setProfile(res.data);
    } catch {
      toast.error("Không thể tải profile");
    } finally {
      setProfileLoading(false);
    }
  };

  const changeRole = async (userId: string, newRole: string) => {
    try {
      await api().patch(`/admin/users/${userId}/role`, { role: newRole });
      toast.success(`Đã cập nhật role thành ${newRole}`);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: newRole } : u))
      );
      if (selectedUser?.id === userId) {
        setSelectedUser((prev) => (prev ? { ...prev, role: newRole } : null));
      }
    } catch {
      toast.error("Không thể cập nhật role");
    }
  };

  const deleteUser = async (userId: string, email: string) => {
    if (!confirm(`Xoá người dùng "${email}"? Hành động này không thể hoàn tác.`)) return;
    try {
      await api().delete(`/admin/users/${userId}`);
      toast.success(`Đã xoá ${email}`);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
      if (selectedUser?.id === userId) setSelectedUser(null);
    } catch {
      toast.error("Không thể xoá người dùng");
    }
  };

  const handleSearch = () => {
    setPage(0);
    fetchUsers();
  };

  const formatDate = (d: string) => {
    return new Date(d).toLocaleDateString("vi-VN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };

  const roleBadge = (role: string) => {
    if (role === "admin")
      return (
        <Badge className="bg-amber-100 text-amber-700 border-amber-200 text-[10px]">
          <Shield className="w-3 h-3 mr-0.5" /> Admin
        </Badge>
      );
    return (
      <Badge variant="outline" className="text-[10px]">
        <UserCircle className="w-3 h-3 mr-0.5" /> Student
      </Badge>
    );
  };

  return (
    <TabsContent value="users" className="space-y-4 mt-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* User list */}
        <div className="md:col-span-2">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary" />
                  Người dùng
                </CardTitle>
                <span className="text-xs text-muted-foreground">
                  {users.length} user
                </span>
              </div>
              <div className="flex gap-2 mt-2">
                <div className="relative flex-1">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Tìm bằng email..."
                    className="pl-8 h-8 text-xs"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  />
                </div>
                <Button size="sm" variant="secondary" onClick={handleSearch} className="h-8 text-xs">
                  <Search className="w-3.5 h-3.5 mr-1" />
                  Tìm
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                </div>
              ) : users.length === 0 ? (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  Không tìm thấy người dùng
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {users.map((u) => (
                    <div
                      key={u.id}
                      className={`flex items-center justify-between px-4 py-2.5 hover:bg-muted/50 cursor-pointer transition-colors ${
                        selectedUser?.id === u.id ? "bg-muted/50" : ""
                      }`}
                      onClick={() => viewProfile(u)}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                          <span className="text-xs font-medium text-primary">
                            {u.email.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm truncate">{u.email}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            {roleBadge(u.role)}
                            <span className="text-[10px] text-muted-foreground">
                              {formatDate(u.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="w-7 h-7 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteUser(u.id, u.email);
                          }}
                          title="Xoá user"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination */}
              <div className="flex items-center justify-between px-4 py-2 border-t border-border">
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                  className="text-xs"
                >
                  <ChevronLeft className="w-3.5 h-3.5 mr-1" />
                  Trước
                </Button>
                <span className="text-xs text-muted-foreground">Trang {page + 1}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={users.length < pageSize}
                  onClick={() => setPage((p) => p + 1)}
                  className="text-xs"
                >
                  Sau
                  <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* User detail / profile */}
        <div>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <UserCircle className="w-4 h-4 text-primary" />
                Chi tiết
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedUser ? (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  Chọn một người dùng để xem chi tiết
                </div>
              ) : profileLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="space-y-3">
                  {/* User info */}
                  <div className="space-y-2 pb-3 border-b border-border">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-muted-foreground" />
                      <span className="text-xs">{selectedUser.email}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-muted-foreground" />
                      <span className="text-xs">Tham gia: {formatDate(selectedUser.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <GraduationCap className="w-3.5 h-3.5 text-muted-foreground" />
                      <span className="text-xs">
                        Lớp {selectedUser.grade_level || "Chưa cập nhật"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {roleBadge(selectedUser.role)}
                      <select
                        className="text-xs border rounded px-1 py-0.5 bg-background"
                        value={selectedUser.role}
                        onChange={(e) => changeRole(selectedUser.id, e.target.value)}
                      >
                        <option value="student">Student</option>
                        <option value="admin">Admin</option>
                      </select>
                    </div>
                  </div>

                  {/* Topic mastery */}
                  {profile && (
                    <>
                      <div>
                        <p className="text-xs font-medium flex items-center gap-1 mb-2">
                          <TrendingUp className="w-3 h-3 text-emerald-500" />
                          Mức độ thành thạo
                        </p>
                        {Object.keys(profile.topic_mastery).length === 0 ? (
                          <p className="text-[10px] text-muted-foreground">Chưa có dữ liệu</p>
                        ) : (
                          <div className="space-y-1">
                            {Object.entries(profile.topic_mastery)
                              .sort(([, a], [, b]) => b - a)
                              .slice(0, 8)
                              .map(([topic, value]) => (
                                <div key={topic} className="flex items-center gap-2">
                                  <span className="text-[10px] flex-1 truncate capitalize">
                                    {topic.replace(/_/g, " ")}
                                  </span>
                                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                                    <div
                                      className={`h-full rounded-full ${
                                        value > 0.75
                                          ? "bg-emerald-500"
                                          : value > 0.4
                                          ? "bg-amber-500"
                                          : "bg-red-500"
                                      }`}
                                      style={{ width: `${value * 100}%` }}
                                    />
                                  </div>
                                  <span className="text-[10px] text-muted-foreground w-8 text-right">
                                    {Math.round(value * 100)}%
                                  </span>
                                </div>
                              ))}
                          </div>
                        )}
                      </div>

                      {/* Weak topics */}
                      <div>
                        <p className="text-xs font-medium flex items-center gap-1 mb-2">
                          <AlertTriangle className="w-3 h-3 text-red-500" />
                          Chủ đề yếu
                        </p>
                        {profile.weak_topics.length === 0 ? (
                          <p className="text-[10px] text-muted-foreground">Không có</p>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {profile.weak_topics.map((t) => (
                              <Badge
                                key={t}
                                variant="outline"
                                className="bg-red-50 text-red-600 border-red-200 text-[10px]"
                              >
                                {t.replace(/_/g, " ")}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Strong topics */}
                      <div>
                        <p className="text-xs font-medium flex items-center gap-1 mb-2">
                          <BookOpen className="w-3 h-3 text-emerald-500" />
                          Chủ đề mạnh
                        </p>
                        {profile.strong_topics.length === 0 ? (
                          <p className="text-[10px] text-muted-foreground">Không có</p>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {profile.strong_topics.map((t) => (
                              <Badge
                                key={t}
                                variant="outline"
                                className="bg-emerald-50 text-emerald-600 border-emerald-200 text-[10px]"
                              >
                                {t.replace(/_/g, " ")}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Stats */}
                      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border">
                        <div className="text-center">
                          <p className="text-xs font-semibold">
                            {Math.round(profile.learning_speed * 100)}%
                          </p>
                          <p className="text-[9px] text-muted-foreground">Tốc độ học</p>
                        </div>
                        <div className="text-center">
                          <p className="text-xs font-semibold">
                            {Math.round(profile.retention_strength * 100)}%
                          </p>
                          <p className="text-[9px] text-muted-foreground">Ghi nhớ</p>
                        </div>
                        <div className="text-center">
                          <p className="text-xs font-semibold">
                            {Math.round(profile.error_recurrence_rate * 100)}%
                          </p>
                          <p className="text-[9px] text-muted-foreground">Tái phạm</p>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </TabsContent>
  );
}

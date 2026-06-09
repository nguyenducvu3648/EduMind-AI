"use client";

import { useEffect, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BookOpen,
  Search,
  Filter,
  GraduationCap,
  FileText,
  Bookmark,
  ChevronRight,
  Loader2,
} from "lucide-react";
import type { WikiChunk } from "@/types";
import { getWikiChunks } from "@/lib/wiki";

export default function WikiPage() {
  const [chunks, setChunks] = useState<WikiChunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [gradeFilter, setGradeFilter] = useState<number | null>(null);
  const [selectedChunk, setSelectedChunk] = useState<WikiChunk | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getWikiChunks({ limit: 500 });
        setChunks(data);
      } catch {
        // silent
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = chunks.filter((c) => {
    if (gradeFilter && c.grade !== gradeFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        c.title.toLowerCase().includes(q) ||
        c.content.toLowerCase().includes(q) ||
        (c.topic || "").toLowerCase().includes(q) ||
        (c.section || "").toLowerCase().includes(q)
      );
    }
    return true;
  });

  const grades = [...new Set(chunks.map((c) => c.grade).filter(Boolean))].sort() as number[];
  const subjects = [...new Set(chunks.map((c) => c.subject).filter(Boolean))];

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left panel: list */}
      <div className="w-[380px] border-r border-border flex flex-col shrink-0 h-full">
        <div className="p-4 border-b border-border space-y-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary" />
            <h2 className="font-semibold text-sm">Tài liệu học tập</h2>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Tìm kiếm tài liệu..."
              className="pl-8 h-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-1 flex-wrap">
            <button
              onClick={() => setGradeFilter(null)}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                gradeFilter === null
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80 text-muted-foreground"
              }`}
            >
              Tất cả
            </button>
            {grades.map((g) => (
              <button
                key={g}
                onClick={() => setGradeFilter(g)}
                className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                  gradeFilter === g
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted hover:bg-muted/80 text-muted-foreground"
                }`}
              >
                Lớp {g}
              </button>
            ))}
          </div>
        </div>

        <ScrollArea className="flex-1 h-0 min-h-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground text-sm">
              Không tìm thấy tài liệu
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {filtered.map((chunk) => (
                <button
                  key={chunk.id}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedChunk?.id === chunk.id
                      ? "bg-primary/10 border border-primary/20"
                      : "hover:bg-muted/50 border border-transparent"
                  }`}
                  onClick={() => setSelectedChunk(chunk)}
                >
                  <div className="flex items-start gap-2">
                    <FileText className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">
                        {chunk.title}
                      </p>
                      {chunk.section && (
                        <p className="text-xs text-muted-foreground truncate">
                          {chunk.section}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-1.5">
                        <Badge
                          variant="secondary"
                          className="text-[10px] px-1.5 py-0 h-4"
                        >
                          Lớp {chunk.grade}
                        </Badge>
                        {chunk.topic && (
                          <Badge
                            variant="outline"
                            className="text-[10px] px-1.5 py-0 h-4"
                          >
                            {chunk.topic}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0 mt-1 ml-auto" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Right panel: detail */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {selectedChunk ? (
          <ScrollArea className="flex-1 h-0 min-h-0 p-6">
            <div className="max-w-3xl mx-auto">
              <div className="flex items-center gap-2 mb-4">
                <Badge variant="secondary">Lớp {selectedChunk.grade}</Badge>
                {selectedChunk.subject && (
                  <Badge variant="outline">{selectedChunk.subject}</Badge>
                )}
                {selectedChunk.topic && (
                  <Badge variant="outline">{selectedChunk.topic}</Badge>
                )}
              </div>

              <h1 className="text-xl font-bold mb-1">{selectedChunk.title}</h1>
              {selectedChunk.section && (
                <p className="text-sm text-muted-foreground mb-4">
                  {selectedChunk.section}
                </p>
              )}

              <Card>
                <CardContent className="pt-6">
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    {selectedChunk.content.split("\n").map((line, i) => (
                      <p key={i}>{line || " "}</p>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {selectedChunk.source && (
                <p className="text-xs text-muted-foreground mt-4">
                  Nguồn: {selectedChunk.source}
                </p>
              )}
            </div>
          </ScrollArea>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
            <BookOpen className="w-12 h-12 mb-3" />
            <h3 className="font-medium text-sm">Chọn một tài liệu để xem</h3>
            <p className="text-xs mt-1">
              Duyệt qua kho kiến thức Toán THPT
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

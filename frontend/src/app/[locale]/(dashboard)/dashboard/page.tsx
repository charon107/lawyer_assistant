"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent, Button, Skeleton } from "@/components/ui";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/hooks";
import { ROUTES, BACKEND_URL } from "@/lib/constants";
import type { HealthResponse } from "@/types";
import {
  CheckCircle,
  XCircle,
  User,
  ArrowRight,
  MessageSquare,
  Settings,
  Activity,
  ExternalLink,
  BookOpen,
  Star,
  List,
} from "lucide-react";

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "早上好";
  if (hour < 18) return "下午好";
  return "晚上好";
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await apiClient.get<HealthResponse>("/health");
        setHealth(data);
        setHealthError(false);
      } catch {
        setHealthError(true);
      } finally {
        setHealthLoading(false);
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="space-y-6 pb-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold">
          {getGreeting()}{user?.name ? `, ${user.name}` : user?.email ? `, ${user.email.split("@")[0]}` : ""}
        </h1>
        <p className="text-sm sm:text-base text-muted-foreground">
          以下是您的项目动态。
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">API 状态</CardTitle>
            {healthLoading ? (
              <Skeleton className="h-4 w-4 rounded-full" />
            ) : healthError ? (
              <XCircle className="h-4 w-4 text-destructive" />
            ) : (
              <CheckCircle className="h-4 w-4 text-green-500" />
            )}
          </CardHeader>
          <CardContent>
            {healthLoading ? <Skeleton className="h-8 w-16 rounded" /> : (
              <p className="text-2xl font-bold">{healthError ? "离线" : health?.status || "正常"}</p>
            )}
            {health?.version && (
              <p className="text-xs text-muted-foreground">v{health.version}</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">账户</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {user?.email ? (
              <p className="text-sm font-medium truncate">{user.email}</p>
            ) : (
              <Skeleton className="h-5 w-40 rounded" />
            )}
            <p className="text-xs text-muted-foreground">
              {user?.role === "admin" ? "管理员" : "用户"}
              {user?.created_at && ` · 注册于 ${new Date(user.created_at).toLocaleDateString()}`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">AI 智能体</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">pydantic_ai</p>
            <p className="text-xs text-muted-foreground">OpenAI 提供商</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="mb-3 text-lg font-semibold">快捷操作</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Link href={ROUTES.CHAT}>
            <Card className="cursor-pointer transition-colors hover:bg-accent">
              <CardContent className="flex items-center gap-3 p-4">
                <MessageSquare className="h-5 w-5 text-primary" />
                <div className="flex-1">
                  <p className="text-sm font-medium">开始对话</p>
                  <p className="text-xs text-muted-foreground">与 AI 智能体交流</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>
          </Link>

          <Link href={ROUTES.PROFILE}>
            <Card className="cursor-pointer transition-colors hover:bg-accent">
              <CardContent className="flex items-center gap-3 p-4">
                <Settings className="h-5 w-5 text-primary" />
                <div className="flex-1">
                  <p className="text-sm font-medium">个人中心与设置</p>
                  <p className="text-xs text-muted-foreground">管理您的账户</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>
          </Link>

          <a href={`${BACKEND_URL}/docs`} target="_blank" rel="noopener noreferrer">
            <Card className="cursor-pointer transition-colors hover:bg-accent">
              <CardContent className="flex items-center gap-3 p-4">
                <BookOpen className="h-5 w-5 text-primary" />
                <div className="flex-1">
                  <p className="text-sm font-medium">API 文档</p>
                  <p className="text-xs text-muted-foreground">OpenAPI / Swagger 接口文档</p>
                </div>
                <ExternalLink className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>
          </a>

          <a href="/api/conversations/export" download="conversations_export.json">
            <Card className="cursor-pointer transition-colors hover:bg-accent">
              <CardContent className="flex items-center gap-3 p-4">
                <ArrowRight className="h-5 w-5 text-primary" />
                <div className="flex-1">
                  <p className="text-sm font-medium">导出对话</p>
                  <p className="text-xs text-muted-foreground">以 JSON 格式下载所有对话记录</p>
                </div>
                <ExternalLink className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>
          </a>
        </div>
      </div>
      {/* Admin Actions */}
      {user?.role === "admin" && (
        <div>
          <h2 className="mb-3 text-lg font-semibold">管理员操作</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Link href={ROUTES.ADMIN_RATINGS}>
              <Card className="cursor-pointer transition-colors hover:bg-accent">
                <CardContent className="flex items-center gap-3 p-4">
                  <Star className="h-5 w-5 text-primary" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">回复评分</p>
                    <p className="text-xs text-muted-foreground">查看和管理评分</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </CardContent>
              </Card>
            </Link>

            <Link href={ROUTES.ADMIN_CONVERSATIONS}>
              <Card className="cursor-pointer transition-colors hover:bg-accent">
                <CardContent className="flex items-center gap-3 p-4">
                  <List className="h-5 w-5 text-primary" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">全部对话</p>
                    <p className="text-xs text-muted-foreground">查看所有用户的对话</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </CardContent>
              </Card>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

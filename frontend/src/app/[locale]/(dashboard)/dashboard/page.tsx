"use client";

import Link from "next/link";
import { Card, CardContent, Skeleton } from "@/components/ui";
import { useAuth } from "@/hooks";
import { ROUTES } from "@/lib/constants";
import {
  MessageSquare,
  FileSearch,
  Briefcase,
  Download,
  Star,
  List,
  User,
} from "lucide-react";

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "早上好";
  if (hour < 18) return "下午好";
  return "晚上好";
}

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6 pb-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {getGreeting()}{user?.name ? `，${user.name}` : user?.email ? `，${user.email.split("@")[0]}` : ""}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          欢迎使用 LexMind — 以下是您的工作台概览
        </p>
      </div>

      {/* Account card */}
      <Card className="max-w-sm">
        <CardContent className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-[13px] font-medium text-muted-foreground">账户</span>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-950">
              <User className="h-4 w-4 text-amber-600" />
            </div>
          </div>
          {user?.email ? (
            <p className="text-[28px] font-bold leading-none tracking-tight truncate">
              {user.email.split("@")[0]}
            </p>
          ) : (
            <Skeleton className="h-7 w-24 rounded" />
          )}
          <p className="mt-1 text-xs text-muted-foreground">
            {user?.role === "admin" ? "管理员" : "用户"}
          </p>
        </CardContent>
      </Card>

      {/* Quick actions */}
      <div>
        <h2 className="mb-3 text-xs font-bold uppercase tracking-widest text-muted-foreground">快捷操作</h2>
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <Link href={ROUTES.CHAT}>
            <Card className="cursor-pointer transition-colors hover:border-brand/40">
              <CardContent className="flex flex-col items-center gap-2 p-4 text-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/8">
                  <MessageSquare className="h-5 w-5 text-brand" />
                </div>
                <p className="text-[13px] font-semibold">AI 对话</p>
                <p className="text-xs text-muted-foreground">法律咨询与分析</p>
              </CardContent>
            </Card>
          </Link>

          <Link href={ROUTES.REVIEW}>
            <Card className="cursor-pointer transition-colors hover:border-brand/40">
              <CardContent className="flex flex-col items-center gap-2 p-4 text-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/8">
                  <FileSearch className="h-5 w-5 text-brand" />
                </div>
                <p className="text-[13px] font-semibold">文件审查</p>
                <p className="text-xs text-muted-foreground">合同与协议审查</p>
              </CardContent>
            </Card>
          </Link>

          <Link href={ROUTES.CASES}>
            <Card className="cursor-pointer transition-colors hover:border-brand/40">
              <CardContent className="flex flex-col items-center gap-2 p-4 text-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/8">
                  <Briefcase className="h-5 w-5 text-brand" />
                </div>
                <p className="text-[13px] font-semibold">案件管理</p>
                <p className="text-xs text-muted-foreground">查看与管理案件</p>
              </CardContent>
            </Card>
          </Link>

          <a href="/api/conversations/export" download="conversations_export.json">
            <Card className="cursor-pointer transition-colors hover:border-brand/40">
              <CardContent className="flex flex-col items-center gap-2 p-4 text-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/8">
                  <Download className="h-5 w-5 text-brand" />
                </div>
                <p className="text-[13px] font-semibold">文档导出</p>
                <p className="text-xs text-muted-foreground">下载对话记录</p>
              </CardContent>
            </Card>
          </a>
        </div>
      </div>

      {/* Admin Actions */}
      {user?.role === "admin" && (
        <div>
          <h2 className="mb-3 text-xs font-bold uppercase tracking-widest text-muted-foreground">管理员</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Link href={ROUTES.ADMIN_RATINGS}>
              <Card className="cursor-pointer transition-colors hover:border-brand/40">
                <CardContent className="flex flex-col items-center gap-2 p-4 text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-950">
                    <Star className="h-5 w-5 text-amber-600" />
                  </div>
                  <p className="text-[13px] font-semibold">回复评分</p>
                  <p className="text-xs text-muted-foreground">查看和管理评分</p>
                </CardContent>
              </Card>
            </Link>

            <Link href={ROUTES.ADMIN_CONVERSATIONS}>
              <Card className="cursor-pointer transition-colors hover:border-brand/40">
                <CardContent className="flex flex-col items-center gap-2 p-4 text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 dark:bg-purple-950">
                    <List className="h-5 w-5 text-purple-600" />
                  </div>
                  <p className="text-[13px] font-semibold">全部对话</p>
                  <p className="text-xs text-muted-foreground">查看所有用户的对话</p>
                </CardContent>
              </Card>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

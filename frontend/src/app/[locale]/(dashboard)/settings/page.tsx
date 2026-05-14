"use client";

import { Card, Badge } from "@/components/ui";
import { ThemeToggle } from "@/components/theme";
import { Server, Code, Shield, Palette } from "lucide-react";
import { Breadcrumb } from "@/components/layout/breadcrumb";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl pb-8">
      <Breadcrumb />
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">设置</h1>
        <p className="text-sm text-muted-foreground">
          应用配置与偏好设置
        </p>
      </div>

      <div className="grid gap-4">
        {/* Appearance */}
        <Card className="p-4 sm:p-6">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Palette className="h-5 w-5" />
            外观
          </h3>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="font-medium text-sm">主题</p>
              <p className="text-xs text-muted-foreground">选择浅色、深色或跟随系统主题</p>
            </div>
            <ThemeToggle variant="dropdown" />
          </div>
        </Card>

        {/* Application Info */}
        <Card className="p-4 sm:p-6">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Server className="h-5 w-5" />
            应用信息
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">项目</span>
              <span className="font-medium">LexMind</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">AI 框架</span>
              <Badge variant="secondary">pydantic_ai</Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">大模型提供商</span>
              <Badge variant="secondary">openai</Badge>
            </div>
          </div>
        </Card>

        {/* Stack Info */}
        <Card className="p-4 sm:p-6">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Code className="h-5 w-5" />
            技术栈
          </h3>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">FastAPI</Badge>
            <Badge variant="outline">Next.js 15</Badge>
            <Badge variant="outline">SQLite</Badge>
          </div>
        </Card>

        {/* Security */}
        <Card className="p-4 sm:p-6">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Shield className="h-5 w-5" />
            安全
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">身份认证</span>
              <Badge variant="outline">JWT</Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">API 密钥</span>
              <Badge variant="outline">已启用</Badge>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}


"use client";

import { useState, useRef, useEffect } from "react";
import { toast } from "sonner";
import { useAuth } from "@/hooks";
import { useAuthStore } from "@/stores";
import { apiClient, ApiError } from "@/lib/api-client";
import type { User } from "@/types";
import {
  Button, Card, CardHeader, CardTitle, CardContent, Input, Label, Badge,
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from "@/components/ui";
import { ThemeToggle } from "@/components/theme";
import { User as UserIcon, Mail, Shield, Settings, Palette, LogOut, Camera, Bot, Eye, EyeOff, RotateCcw } from "lucide-react";
import Image from "next/image";
import { Breadcrumb } from "@/components/layout/breadcrumb";

export default function ProfilePage() {
  const { user, isAuthenticated, logout } = useAuth();
  const { setUser } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editEmail, setEditEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement>(null);

  // LLM config state
  const [llmProvider, setLlmProvider] = useState("");
  const [aiModel, setAiModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [llmBaseUrl, setLlmBaseUrl] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [llmSaving, setLlmSaving] = useState(false);
  const [hasExistingKey, setHasExistingKey] = useState(false);

  // Initialize LLM config from user data
  useEffect(() => {
    if (user) {
      setLlmProvider(user.llm_provider || "");
      setAiModel(user.ai_model || "");
      setLlmBaseUrl(user.llm_base_url || "");
      setHasExistingKey(user.has_openai_key || user.has_anthropic_key || false);
    }
  }, [user]);

  const handleLlmSave = async () => {
    setLlmSaving(true);
    try {
      const payload: Record<string, unknown> = {
        llm_provider: llmProvider || null,
        ai_model: aiModel || null,
        llm_base_url: llmBaseUrl || null,
      };
      // Only send API key if user typed a new one
      if (apiKey) {
        if (llmProvider === "anthropic") {
          payload.anthropic_api_key = apiKey;
        } else {
          payload.openai_api_key = apiKey;
        }
      }
      const updated = await apiClient.patch<User>("/users/me", payload);
      setUser(updated);
      setApiKey(""); // Clear the input after save
      setHasExistingKey(updated.has_openai_key || updated.has_anthropic_key || false);
      toast.success("模型配置已保存");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "保存模型配置失败");
    } finally {
      setLlmSaving(false);
    }
  };

  const handleLlmReset = async () => {
    setLlmSaving(true);
    try {
      const updated = await apiClient.patch<User>("/users/me", {
        llm_provider: null,
        ai_model: null,
        openai_api_key: null,
        anthropic_api_key: null,
        llm_base_url: null,
      });
      setUser(updated);
      setLlmProvider("");
      setAiModel("");
      setApiKey("");
      setLlmBaseUrl("");
      setHasExistingKey(false);
      toast.success("已恢复全局默认配置");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "重置失败");
    } finally {
      setLlmSaving(false);
    }
  };

  const handleEdit = () => {
    if (!isEditing && user) setEditEmail(user.email);
    setIsEditing(!isEditing);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await apiClient.patch<User>("/users/me", { email: editEmail });
      setUser(updated);
      toast.success("个人资料已更新");
      setIsEditing(false);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "更新个人资料失败");
    } finally { setIsSaving(false); }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    if (file.size > 2 * 1024 * 1024) { toast.error("头像文件过大，最大 2MB。"); return; }
    setAvatarUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/users/me/avatar", { method: "POST", body: formData });
      if (!res.ok) { const err = await res.json().catch(() => ({ detail: "上传失败" })); throw new Error(err.detail || "上传失败"); }
      const updated = await res.json();
      setUser(updated);
      toast.success("头像已更新");
    } catch (err) { toast.error(err instanceof Error ? err.message : "上传头像失败"); }
    finally { setAvatarUploading(false); }
  };

  if (!isAuthenticated || !user) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Card className="p-6 sm:p-8 text-center mx-4">
          <p className="text-muted-foreground">请登录后查看个人中心。</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      <Breadcrumb />
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <button type="button" onClick={() => avatarInputRef.current?.click()} disabled={avatarUploading}
            className="group relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-full bg-primary/10">
            {user.avatar_url ? (
              <Image src={`/api/users/avatar/${user.id}`} alt="" width={56} height={56} className="h-full w-full object-cover" unoptimized />
            ) : (
              <UserIcon className="text-primary h-7 w-7" />
            )}
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100">
              <Camera className="h-5 w-5 text-white" />
            </div>
          </button>
          <input ref={avatarInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={handleAvatarUpload} className="hidden" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{user.email}</h1>
            <div className="mt-1 flex items-center gap-2">
              {user.role === "admin" && <Badge variant="secondary"><Shield className="mr-1 h-3 w-3" />管理员</Badge>}
              {user.is_active && <Badge variant="outline" className="text-green-600">活跃</Badge>}
              {user.created_at && (
                <span className="text-muted-foreground text-xs">注册于 {new Date(user.created_at).toLocaleDateString()}</span>
              )}
            </div>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={handleEdit} className="h-10 self-start">
          <Settings className="mr-2 h-4 w-4" />
          {isEditing ? "取消" : "编辑资料"}
        </Button>
      </div>

      {/* Main grid */}
      <div className="grid gap-4 lg:grid-cols-5 sm:gap-6">
        {/* Left column */}
        <div className="space-y-4 lg:col-span-3 sm:space-y-6">
          {/* Account Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Mail className="h-4 w-4" /> 账户信息
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="email" className="text-sm">邮箱地址</Label>
                  <Input id="email" type="email" value={isEditing ? editEmail : user.email}
                    onChange={(e) => setEditEmail(e.target.value)} disabled={!isEditing}
                    className={!isEditing ? "bg-muted" : ""} />
                </div>
                {isEditing && (
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={handleEdit} size="sm">取消</Button>
                    <Button onClick={handleSave} disabled={isSaving} size="sm">
                      {isSaving ? "保存中..." : "保存修改"}
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Model Configuration */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Bot className="h-4 w-4" /> 模型配置
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label className="text-sm">提供商</Label>
                  <Select value={llmProvider} onValueChange={setLlmProvider}>
                    <SelectTrigger>
                      <SelectValue placeholder="使用全局默认" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI 兼容</SelectItem>
                      <SelectItem value="anthropic">Anthropic</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="ai-model" className="text-sm">模型名称</Label>
                  <Input id="ai-model" value={aiModel} onChange={(e) => setAiModel(e.target.value)}
                    placeholder="例: deepseek-v4-pro" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="api-key" className="text-sm">API Key</Label>
                  <div className="relative">
                    <Input id="api-key" type={showApiKey ? "text" : "password"} value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder={hasExistingKey ? "已设置（留空保持不变）" : "输入 API Key"} />
                    <button type="button" onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                      {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="base-url" className="text-sm">Base URL</Label>
                  <Input id="base-url" value={llmBaseUrl} onChange={(e) => setLlmBaseUrl(e.target.value)}
                    placeholder="例: https://api.deepseek.com" />
                </div>
                <div className="flex justify-between gap-2">
                  <Button variant="outline" size="sm" onClick={handleLlmReset} disabled={llmSaving}>
                    <RotateCcw className="mr-1 h-3 w-3" /> 恢复默认
                  </Button>
                  <Button size="sm" onClick={handleLlmSave} disabled={llmSaving}>
                    {llmSaving ? "保存中..." : "保存配置"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-4 lg:col-span-2 sm:space-y-6">

          {/* Preferences */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Palette className="h-4 w-4" /> 偏好设置
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">主题</p>
                  <p className="text-muted-foreground text-xs">配色方案</p>
                </div>
                <ThemeToggle variant="dropdown" />
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-destructive/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-destructive flex items-center gap-2 text-sm font-semibold">
                <LogOut className="h-4 w-4" /> 危险区域
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">退出登录</p>
                  <p className="text-muted-foreground text-xs">从当前设备退出登录</p>
                </div>
                <Button variant="destructive" size="sm" onClick={logout}>退出登录</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

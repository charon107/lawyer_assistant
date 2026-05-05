
"use client";

import { useState, useRef, useEffect } from "react";
import { toast } from "sonner";
import { useAuth } from "@/hooks";
import { useAuthStore } from "@/stores";
import { apiClient, ApiError } from "@/lib/api-client";
import { PROVIDERS, getProvider } from "@/lib/providers";
import type { User, LLMConfig } from "@/types";
import {
  Button, Card, CardHeader, CardTitle, CardContent, Input, Label, Badge,
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from "@/components/ui";
import { ThemeToggle } from "@/components/theme";
import {
  User as UserIcon, Mail, Shield, Settings, Palette, LogOut, Camera, Bot,
  Eye, EyeOff, RotateCcw, CheckCircle, XCircle, Loader2, Plus, Trash2, Pencil,
} from "lucide-react";
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

  // LLM configs state
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  // Load configs on mount
  useEffect(() => {
    if (user?.llm_configs) {
      setConfigs(user.llm_configs);
    }
  }, [user]);

  const refreshUser = async () => {
    try {
      const updated = await apiClient.get<User>("/users/me");
      setUser(updated);
      setConfigs(updated.llm_configs || []);
    } catch { /* ignore */ }
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

  const handleDeleteConfig = async (configId: string) => {
    try {
      await apiClient.delete(`/users/me/llm-configs/${configId}`);
      toast.success("已删除");
      await refreshUser();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "删除失败");
    }
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
              <CardTitle className="flex items-center justify-between text-sm font-semibold">
                <span className="flex items-center gap-2"><Bot className="h-4 w-4" /> 模型配置</span>
                {!showAddForm && !editingConfig && (
                  <Button variant="outline" size="sm" onClick={() => setShowAddForm(true)}>
                    <Plus className="mr-1 h-3 w-3" /> 添加
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Existing configs */}
              {configs.length > 0 && !showAddForm && !editingConfig && (
                <div className="space-y-3">
                  {configs.map((cfg) => (
                    <ConfigCard
                      key={cfg.id}
                      config={cfg}
                      onEdit={() => setEditingConfig(cfg)}
                      onDelete={() => handleDeleteConfig(cfg.id)}
                    />
                  ))}
                </div>
              )}

              {configs.length === 0 && !showAddForm && !editingConfig && (
                <p className="text-muted-foreground text-sm">尚未配置任何模型提供商。点击"添加"开始。</p>
              )}

              {/* Add/Edit form */}
              {(showAddForm || editingConfig) && (
                <LLMConfigForm
                  config={editingConfig}
                  onSave={async () => {
                    setShowAddForm(false);
                    setEditingConfig(null);
                    await refreshUser();
                  }}
                  onCancel={() => {
                    setShowAddForm(false);
                    setEditingConfig(null);
                  }}
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-4 lg:col-span-2 sm:space-y-6">
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


function ConfigCard({ config, onEdit, onDelete }: { config: LLMConfig; onEdit: () => void; onDelete: () => void }) {
  const provider = getProvider(config.provider);
  return (
    <div className="flex items-center justify-between rounded-md border px-3 py-2">
      <div className="flex items-center gap-3">
        <Bot className="h-4 w-4 text-muted-foreground" />
        <div>
          <p className="text-sm font-medium">{provider?.name || config.provider}</p>
          <p className="text-muted-foreground text-xs">
            {config.model || "未选模型"} {config.has_api_key ? <span className="text-green-600">Key OK</span> : <span className="text-destructive">无 Key</span>}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={onEdit}><Pencil className="h-3 w-3" /></Button>
        <Button variant="ghost" size="sm" onClick={onDelete}><Trash2 className="h-3 w-3 text-destructive" /></Button>
      </div>
    </div>
  );
}


function LLMConfigForm({ config, onSave, onCancel }: { config: LLMConfig | null; onSave: () => void; onCancel: () => void }) {
  const [provider, setProvider] = useState(config?.provider || "");
  const [model, setModel] = useState(config?.model || "");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState(config?.base_url || "");
  const [showApiKey, setShowApiKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [connectionMessage, setConnectionMessage] = useState("");
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [configId, setConfigId] = useState<string | null>(config?.id || null);

  const selectedProvider = getProvider(provider);

  // If editing an existing config with API key, auto-test to load models
  useEffect(() => {
    if (config?.has_api_key && config.id) {
      handleTestConnection(config.id);
    }
  }, []);

  const handleProviderChange = (p: string) => {
    setProvider(p);
    const prov = getProvider(p);
    if (prov) setBaseUrl(prov.defaultBaseUrl);
    setModel("");
    setAvailableModels([]);
    setConnectionStatus("idle");
    setConfigId(null);
  };

  const handleTestConnection = async (existingConfigId?: string) => {
    if (!provider) { toast.error("请先选择提供商"); return; }
    if (!apiKey && !existingConfigId) { toast.error("请输入 API Key"); return; }

    setTesting(true);
    setConnectionStatus("testing");
    setConnectionMessage("");
    setAvailableModels([]);

    try {
      // Step 1: Create or use existing config
      let cid = existingConfigId || configId;
      if (!cid) {
        const payload: Record<string, unknown> = { provider, base_url: baseUrl || null };
        if (apiKey) payload.api_key = apiKey;
        const created = await apiClient.post<LLMConfig>("/users/me/llm-configs", payload);
        cid = created.id;
        setConfigId(cid);
      } else if (apiKey) {
        // Update API key if user typed a new one
        await apiClient.patch(`/users/me/llm-configs/${cid}`, { api_key: apiKey });
      }

      // Step 2: Test connection + fetch models (single endpoint)
      const result = await apiClient.post<{ success: boolean; message: string; models: string[] }>(
        `/users/me/llm-configs/${cid}/test-connection`, {}
      );

      if (result.success) {
        setConnectionStatus("success");
        setConnectionMessage(result.message);
        setAvailableModels(result.models || []);
        // For Anthropic, use hardcoded models if API didn't return any
        if ((!result.models || result.models.length === 0) && selectedProvider?.models?.length) {
          setAvailableModels(selectedProvider.models);
        }
      } else {
        setConnectionStatus("error");
        setConnectionMessage(result.message);
        setAvailableModels([]);
      }
    } catch {
      setConnectionStatus("error");
      setConnectionMessage("测试请求失败");
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!configId) return;
    setSaving(true);
    try {
      await apiClient.patch(`/users/me/llm-configs/${configId}`, { model: model || null });
      toast.success(config ? "配置已更新" : "配置已保存");
      await onSave();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "保存失败");
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-4 rounded-md border p-4">
      {/* Provider */}
      <div className="grid gap-2">
        <Label className="text-sm">提供商</Label>
        <Select value={provider} onValueChange={handleProviderChange}>
          <SelectTrigger><SelectValue placeholder="选择提供商" /></SelectTrigger>
          <SelectContent>
            {PROVIDERS.map((p) => (
              <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* API Key */}
      <div className="grid gap-2">
        <Label className="text-sm">API Key</Label>
        <div className="relative">
          <Input type={showApiKey ? "text" : "password"} value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={config?.has_api_key ? "已设置（留空保持不变）" : (selectedProvider?.apiKeyPlaceholder || "输入 API Key")} />
          <button type="button" onClick={() => setShowApiKey(!showApiKey)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
            {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Base URL */}
      <div className="grid gap-2">
        <Label className="text-sm">Base URL</Label>
        <Input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
          placeholder={selectedProvider?.defaultBaseUrl || "https://..."} />
      </div>

      {/* Test Connection button — only show when models not yet loaded */}
      {availableModels.length === 0 && connectionStatus !== "success" && (
        <Button size="sm" onClick={() => handleTestConnection()} disabled={testing || !provider}
          className="w-full" variant="outline">
          {testing ? <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> 测试连接中...</> : "测试连接"}
        </Button>
      )}

      {/* Connection status */}
      {connectionStatus !== "idle" && (
        <div className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
          {connectionStatus === "testing" && <><Loader2 className="h-4 w-4 animate-spin text-muted-foreground" /> 测试连接中...</>}
          {connectionStatus === "success" && <><CheckCircle className="h-4 w-4 text-green-600" /> <span className="text-green-600">{connectionMessage}</span></>}
          {connectionStatus === "error" && <><XCircle className="h-4 w-4 text-destructive" /> <span className="text-destructive">{connectionMessage}</span></>}
        </div>
      )}

      {/* Model selection — only after successful connection */}
      {availableModels.length > 0 && connectionStatus === "success" && (
        <div className="grid gap-2">
          <Label className="text-sm">模型</Label>
          <Select value={model} onValueChange={setModel}>
            <SelectTrigger><SelectValue placeholder="选择模型" /></SelectTrigger>
            <SelectContent>
              {availableModels.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Save / Cancel — only show save after connection success */}
      <div className="flex justify-between gap-2">
        <Button variant="outline" size="sm" onClick={onCancel}>取消</Button>
        {connectionStatus === "success" && (
          <Button size="sm" onClick={handleSave} disabled={saving}>
            {saving ? <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> 保存中...</> : "保存"}
          </Button>
        )}
      </div>
    </div>
  );
}

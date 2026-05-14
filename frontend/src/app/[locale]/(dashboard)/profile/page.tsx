"use client";

import { useState, useRef, useEffect } from "react";
import { toast } from "sonner";
import { useAuth } from "@/hooks";
import { useAuthStore } from "@/stores";
import { apiClient, ApiError } from "@/lib/api-client";
import { PROVIDERS, getProvider } from "@/lib/providers";
import type { User, LLMConfig } from "@/types";
import {
  Button, Input, Label,
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
  Avatar, AvatarFallback, AvatarImage,
} from "@/components/ui";
import { ThemeToggle } from "@/components/theme";
import {
  Shield, LogOut, Camera, Bot,
  Eye, EyeOff, CheckCircle, XCircle,
  Loader2, Plus, Trash2, Pencil, Palette,
} from "lucide-react";

export default function ProfilePage() {
  const { user, isAuthenticated, logout } = useAuth();
  const { setUser } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editEmail, setEditEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement>(null);

  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    if (user?.llm_configs) setConfigs(user.llm_configs);
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
        <p className="text-sm text-muted-foreground">请登录后查看个人中心。</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl pb-8">
      {/* Header */}
      <div className="mb-8 flex items-center gap-4">
        <button
          type="button"
          onClick={() => avatarInputRef.current?.click()}
          disabled={avatarUploading}
          className="group relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-full"
        >
          <Avatar className="h-14 w-14">
            {user.avatar_url && <AvatarImage src={`/api/users/avatar/${user.id}`} alt={user.email} />}
            <AvatarFallback className="bg-brand/10 text-brand text-base font-semibold">
              {user.email?.substring(0, 2).toUpperCase() || "U"}
            </AvatarFallback>
          </Avatar>
          <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/40 opacity-0 transition-opacity group-hover:opacity-100">
            <Camera className="h-4 w-4 text-white" />
          </div>
        </button>
        <input ref={avatarInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={handleAvatarUpload} className="hidden" />
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-bold tracking-tight truncate">{user.email}</h1>
          <div className="mt-1 flex items-center gap-2">
            {user.role === "admin" && (
              <span className="inline-flex items-center gap-1 rounded-full bg-brand/8 px-2 py-0.5 text-[11px] font-medium text-brand">
                <Shield className="h-3 w-3" /> 管理员
              </span>
            )}
            {user.created_at && (
              <span className="text-[11px] text-muted-foreground">注册于 {new Date(user.created_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>
      </div>

      {/* Account Info */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold">账户信息</h2>
          <button
            onClick={handleEdit}
            className="text-xs font-medium text-brand hover:underline"
          >
            {isEditing ? "取消" : "编辑"}
          </button>
        </div>
        <div className="grid gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="email" className="text-[13px]">邮箱地址</Label>
            <Input
              id="email"
              type="email"
              value={isEditing ? editEmail : user.email}
              onChange={(e) => setEditEmail(e.target.value)}
              disabled={!isEditing}
              className={!isEditing ? "bg-muted/50 text-sm" : "text-sm"}
            />
          </div>
          {isEditing && (
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={handleEdit} className="h-8 text-xs">取消</Button>
              <Button size="sm" onClick={handleSave} disabled={isSaving} className="h-8 text-xs">
                {isSaving ? "保存中..." : "保存"}
              </Button>
            </div>
          )}
        </div>
      </section>

      <div className="my-6 border-t" />

      {/* Preferences */}
      <section>
        <h2 className="mb-3 text-sm font-semibold">偏好设置</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[13px] font-medium">主题</p>
            <p className="text-xs text-muted-foreground">浅色、深色或跟随系统</p>
          </div>
          <ThemeToggle variant="dropdown" />
        </div>
      </section>

      <div className="my-6 border-t" />

      {/* Model Configuration */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold">模型配置</h2>
            <p className="text-xs text-muted-foreground mt-0.5">管理 AI 模型提供商和密钥</p>
          </div>
          {!showAddForm && !editingConfig && (
            <button
              onClick={() => setShowAddForm(true)}
              className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-brand hover:bg-brand/8 transition-colors"
            >
              <Plus className="h-3 w-3" /> 添加
            </button>
          )}
        </div>

        {configs.length > 0 && !showAddForm && !editingConfig && (
          <div className="divide-y rounded-lg border">
            {configs.map((cfg) => (
              <ConfigRow
                key={cfg.id}
                config={cfg}
                onEdit={() => setEditingConfig(cfg)}
                onDelete={() => handleDeleteConfig(cfg.id)}
              />
            ))}
          </div>
        )}

        {configs.length === 0 && !showAddForm && !editingConfig && (
          <div className="rounded-lg border border-dashed py-6 text-center">
            <Bot className="mx-auto h-7 w-7 text-muted-foreground/40" />
            <p className="mt-1.5 text-xs text-muted-foreground">尚未配置任何模型提供商</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-1.5 text-xs font-medium text-brand hover:underline"
            >
              立即添加
            </button>
          </div>
        )}

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
      </section>

      <div className="my-6 border-t" />

      {/* Logout */}
      <section>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold">退出登录</h2>
            <p className="text-xs text-muted-foreground mt-0.5">从当前设备退出登录</p>
          </div>
          <Button variant="outline" size="sm" onClick={logout} className="h-8 text-xs text-destructive border-destructive/30 hover:bg-destructive/8 hover:text-destructive">
            <LogOut className="mr-1.5 h-3 w-3" /> 退出
          </Button>
        </div>
      </section>
    </div>
  );
}


function ConfigRow({ config, onEdit, onDelete }: { config: LLMConfig; onEdit: () => void; onDelete: () => void }) {
  const provider = getProvider(config.provider);
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <div className="flex items-center gap-3 min-w-0">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-[11px] font-bold text-muted-foreground">
          {(provider?.name || config.provider).substring(0, 2).toUpperCase()}
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-medium truncate">{provider?.name || config.provider}</p>
          <p className="text-xs text-muted-foreground truncate">
            {config.model || "未选模型"}{" "}
            {config.has_api_key
              ? <span className="text-emerald-600">Key OK</span>
              : <span className="text-destructive">无 Key</span>}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-1 shrink-0 ml-2">
        <button onClick={onEdit} className="rounded p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
          <Pencil className="h-3.5 w-3.5" />
        </button>
        <button onClick={onDelete} className="rounded p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/8 transition-colors">
          <Trash2 className="h-3.5 w-3.5" />
        </button>
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
      let cid = existingConfigId || configId;
      if (!cid) {
        const payload: Record<string, unknown> = { provider, base_url: baseUrl || null };
        if (apiKey) payload.api_key = apiKey;
        const created = await apiClient.post<LLMConfig>("/users/me/llm-configs", payload);
        cid = created.id;
        setConfigId(cid);
      } else if (apiKey) {
        await apiClient.patch(`/users/me/llm-configs/${cid}`, { api_key: apiKey });
      }

      const result = await apiClient.post<{ success: boolean; message: string; models: string[] }>(
        `/users/me/llm-configs/${cid}/test-connection`, {}
      );

      if (result.success) {
        setConnectionStatus("success");
        setConnectionMessage(result.message);
        setAvailableModels(result.models || []);
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
    <div className="mt-3 space-y-5 rounded-lg border p-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="grid gap-1.5">
          <Label className="text-[13px]">提供商</Label>
          <Select value={provider} onValueChange={handleProviderChange}>
            <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="选择提供商" /></SelectTrigger>
            <SelectContent>
              {PROVIDERS.map((p) => (
                <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-1.5">
          <Label className="text-[13px]">API Key</Label>
          <div className="relative">
            <Input
              type={showApiKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={config?.has_api_key ? "已设置（留空不变）" : (selectedProvider?.apiKeyPlaceholder || "输入 API Key")}
              className="h-9 pr-9 text-sm"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-1.5">
        <Label className="text-[13px]">Base URL</Label>
        <Input
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          placeholder={selectedProvider?.defaultBaseUrl || "https://..."}
          className="h-9 text-sm"
        />
      </div>

      {connectionStatus !== "idle" && (
        <div className="flex items-center gap-2 text-[13px]">
          {connectionStatus === "testing" && <><Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" /> <span className="text-muted-foreground">测试连接中...</span></>}
          {connectionStatus === "success" && <><CheckCircle className="h-3.5 w-3.5 text-emerald-600" /> <span className="text-emerald-600">{connectionMessage}</span></>}
          {connectionStatus === "error" && <><XCircle className="h-3.5 w-3.5 text-destructive" /> <span className="text-destructive">{connectionMessage}</span></>}
        </div>
      )}

      {availableModels.length > 0 && connectionStatus === "success" && (
        <div className="grid gap-1.5">
          <Label className="text-[13px]">模型</Label>
          <Select value={model} onValueChange={setModel}>
            <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="选择模型" /></SelectTrigger>
            <SelectContent>
              {availableModels.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      )}

      <div className="flex items-center gap-2 pt-1">
        {availableModels.length === 0 && connectionStatus !== "success" && (
          <Button
            size="sm"
            onClick={() => handleTestConnection()}
            disabled={testing || !provider}
            className="h-8 text-xs"
            variant="outline"
          >
            {testing ? <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> 测试中...</> : "测试连接"}
          </Button>
        )}
        <div className="flex-1" />
        <Button variant="ghost" size="sm" onClick={onCancel} className="h-8 text-xs">取消</Button>
        {connectionStatus === "success" && (
          <Button size="sm" onClick={handleSave} disabled={saving} className="h-8 text-xs">
            {saving ? <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> 保存中...</> : "保存"}
          </Button>
        )}
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { useAuth } from "@/hooks";
import { useAuthStore } from "@/stores";
import { apiClient, ApiError } from "@/lib/api-client";
import { PROVIDERS, getProvider } from "@/lib/providers";
import type { User, LLMConfig } from "@/types";
import {
  Button, Input, Label,
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from "@/components/ui";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui";
import {
  Bot, LogOut, Eye, EyeOff, CheckCircle, XCircle,
  Loader2, Plus, Trash2, Pencil, Plug, AlertTriangle, Shield, Mail, Calendar,
} from "lucide-react";

export default function SettingsPage() {
  const { user, isAuthenticated, logout } = useAuth();
  const { setUser } = useAuthStore();

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
        <p className="text-sm text-muted-foreground">请登录后查看设置。</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl pb-12">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight">个人中心</h1>
        <p className="mt-1 text-[13px] text-muted-foreground">管理你的模型配置与账户设置</p>
      </div>

      {/* User Info */}
      <section className="mb-10">
        <div className="flex items-center gap-4">
          <Avatar className="h-14 w-14">
            {user.avatar_url && <AvatarImage src={`/api/users/avatar/${user.id}`} alt={user.email} />}
            <AvatarFallback className="bg-brand/10 text-brand text-base font-semibold">
              {user.email?.substring(0, 2).toUpperCase() || "U"}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-semibold truncate">{user.email}</p>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1">
              {user.role === "admin" && (
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Shield className="h-3 w-3" /> 管理员
                </span>
              )}
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <Mail className="h-3 w-3" /> {user.email}
              </span>
              {user.created_at && (
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" /> 注册于 {new Date(user.created_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Model Configuration Section */}
      <section className="mb-10">
        <div className="mb-1 flex items-center gap-2">
          <Plug className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-[15px] font-semibold">模型配置</h2>
        </div>
        <p className="mb-5 text-[13px] text-muted-foreground pl-6">添加和管理你的 AI 模型提供商</p>

        {/* Config list */}
        {configs.length > 0 && !showAddForm && !editingConfig && (
          <div className="space-y-2">
            {configs.map((cfg) => (
              <ConfigRow
                key={cfg.id}
                config={cfg}
                onEdit={() => setEditingConfig(cfg)}
                onDelete={() => handleDeleteConfig(cfg.id)}
              />
            ))}
            <button
              onClick={() => setShowAddForm(true)}
              className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-muted-foreground/20 py-3 text-[13px] font-medium text-muted-foreground transition-colors hover:border-brand/40 hover:text-brand"
            >
              <Plus className="h-3.5 w-3.5" /> 添加新配置
            </button>
          </div>
        )}

        {/* Empty state */}
        {configs.length === 0 && !showAddForm && !editingConfig && (
          <div className="rounded-xl border border-dashed bg-muted/30 px-6 py-10 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <Bot className="h-6 w-6 text-muted-foreground/60" />
            </div>
            <p className="text-[13px] font-medium">尚未配置任何模型</p>
            <p className="mt-1 text-xs text-muted-foreground">添加一个 AI 模型提供商以开始使用</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-brand-hover"
            >
              <Plus className="h-3.5 w-3.5" /> 添加配置
            </button>
          </div>
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
      </section>

      {/* Logout Section */}
      <section className="rounded-xl border border-destructive/20 bg-destructive/[0.02] p-5">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-destructive/8">
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </div>
          <div className="flex-1">
            <h3 className="text-[13px] font-semibold">退出登录</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">退出后需要重新登录才能访问你的账户</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="shrink-0 text-xs text-destructive hover:bg-destructive/8 hover:text-destructive"
          >
            <LogOut className="mr-1.5 h-3.5 w-3.5" /> 退出
          </Button>
        </div>
      </section>
    </div>
  );
}


function ConfigRow({ config, onEdit, onDelete }: { config: LLMConfig; onEdit: () => void; onDelete: () => void }) {
  const provider = getProvider(config.provider);
  const name = provider?.name || config.provider;
  const initials = name.substring(0, 2).toUpperCase();

  return (
    <div className="group flex items-center gap-4 rounded-xl border bg-card p-4 transition-colors hover:bg-muted/30">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted text-xs font-bold text-muted-foreground">
        {initials}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-medium">{name}</p>
        <p className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
          <span className="truncate">{config.model || "未选模型"}</span>
          {config.has_api_key ? (
            <span className="inline-flex items-center gap-1 text-emerald-600">
              <CheckCircle className="h-3 w-3" /> 已连接
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-amber-600">
              <XCircle className="h-3 w-3" /> 未配置
            </span>
          )}
        </p>
      </div>
      <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          onClick={onEdit}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={onDelete}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-destructive/8 hover:text-destructive"
        >
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

  const step = connectionStatus === "success" ? 2 : 1;

  return (
    <div className="rounded-xl border bg-card">
      {/* Step indicator */}
      <div className="flex items-center gap-3 border-b px-5 py-3">
        <div className="flex items-center gap-2">
          <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${step >= 1 ? "bg-brand text-white" : "bg-muted text-muted-foreground"}`}>1</span>
          <span className={`text-xs ${step >= 1 ? "font-medium text-foreground" : "text-muted-foreground"}`}>连接</span>
        </div>
        <div className="h-px flex-1 bg-border" />
        <div className="flex items-center gap-2">
          <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${step >= 2 ? "bg-brand text-white" : "bg-muted text-muted-foreground"}`}>2</span>
          <span className={`text-xs ${step >= 2 ? "font-medium text-foreground" : "text-muted-foreground"}`}>选择模型</span>
        </div>
      </div>

      {/* Form body */}
      <div className="space-y-5 p-5">
        {/* Step 1: Connection */}
        <div className="grid gap-4 sm:grid-cols-2">
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
                placeholder={config?.has_api_key ? "已设置（留空不变）" : (selectedProvider?.apiKeyPlaceholder || "sk-...")}
                className="h-9 pr-9 text-sm"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>

        <div className="grid gap-1.5">
          <Label className="text-[13px]">Base URL <span className="text-muted-foreground font-normal">(可选)</span></Label>
          <Input
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder={selectedProvider?.defaultBaseUrl || "https://..."}
            className="h-9 text-sm"
          />
        </div>

        {/* Connection status */}
        {connectionStatus !== "idle" && (
          <div className={`flex items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-[13px] ${
            connectionStatus === "success" ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400" :
            connectionStatus === "error" ? "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400" :
            "bg-muted text-muted-foreground"
          }`}>
            {connectionStatus === "testing" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            {connectionStatus === "success" && <CheckCircle className="h-3.5 w-3.5" />}
            {connectionStatus === "error" && <XCircle className="h-3.5 w-3.5" />}
            {connectionStatus === "testing" ? "正在测试连接..." : connectionMessage}
          </div>
        )}

        {/* Step 2: Model selection */}
        {availableModels.length > 0 && connectionStatus === "success" && (
          <div className="grid gap-1.5">
            <Label className="text-[13px]">选择模型</Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="选择一个模型" /></SelectTrigger>
              <SelectContent>
                {availableModels.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 border-t pt-4">
          {availableModels.length === 0 && connectionStatus !== "success" && (
            <Button
              size="sm"
              onClick={() => handleTestConnection()}
              disabled={testing || !provider}
              className="h-9 px-4 text-xs"
            >
              {testing ? <><Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> 测试中...</> : "测试连接"}
            </Button>
          )}
          <div className="flex-1" />
          <Button variant="ghost" size="sm" onClick={onCancel} className="h-9 px-4 text-xs">
            取消
          </Button>
          {connectionStatus === "success" && (
            <Button size="sm" onClick={handleSave} disabled={saving} className="h-9 px-4 text-xs">
              {saving ? <><Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> 保存中...</> : "保存配置"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

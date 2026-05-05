export interface ProviderMeta {
  id: string;
  name: string;
  defaultBaseUrl: string;
  apiKeyPlaceholder: string;
  type: "openai_compatible" | "anthropic" | "google";
  models?: string[]; // Hardcoded fallback for providers without /models endpoint
}

export const PROVIDERS: ProviderMeta[] = [
  // === Major providers ===
  {
    id: "deepseek",
    name: "DeepSeek",
    defaultBaseUrl: "https://api.deepseek.com",
    apiKeyPlaceholder: "sk-...",
    type: "openai_compatible",
  },
  {
    id: "openai",
    name: "OpenAI Codex",
    defaultBaseUrl: "https://api.openai.com/v1",
    apiKeyPlaceholder: "sk-...",
    type: "openai_compatible",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    defaultBaseUrl: "https://api.anthropic.com",
    apiKeyPlaceholder: "sk-ant-...",
    type: "anthropic",
    models: ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"],
  },
  {
    id: "google",
    name: "Google AI Studio (Gemini)",
    defaultBaseUrl: "https://generativelanguage.googleapis.com/v1beta/openai",
    apiKeyPlaceholder: "AIza...",
    type: "openai_compatible",
    models: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
  },
  // === Multi-model aggregators ===
  {
    id: "openrouter",
    name: "OpenRouter (100+ models)",
    defaultBaseUrl: "https://openrouter.ai/api/v1",
    apiKeyPlaceholder: "sk-or-...",
    type: "openai_compatible",
  },
  {
    id: "nous",
    name: "Nous Portal",
    defaultBaseUrl: "https://api.nousresearch.com/v1",
    apiKeyPlaceholder: "sk-...",
    type: "openai_compatible",
  },
  {
    id: "huggingface",
    name: "Hugging Face Inference",
    defaultBaseUrl: "https://api-inference.huggingface.co/v1",
    apiKeyPlaceholder: "hf_...",
    type: "openai_compatible",
  },
  {
    id: "nvidia",
    name: "NVIDIA NIM",
    defaultBaseUrl: "https://integrate.api.nvidia.com/v1",
    apiKeyPlaceholder: "nvapi-...",
    type: "openai_compatible",
  },
  // === Chinese providers ===
  {
    id: "xiaomi",
    name: "Xiaomi MiMo",
    defaultBaseUrl: "https://api.xiaomi.com/v1",
    apiKeyPlaceholder: "...",
    type: "openai_compatible",
    models: ["MiMo-V2.5-pro", "MiMo-V2.5-omni", "MiMo-V2.5-flash", "MiMo-V2-pro", "MiMo-V2-flash"],
  },
  {
    id: "tencent",
    name: "Tencent TokenHub",
    defaultBaseUrl: "https://tokenhub.tencentmaas.com/v1",
    apiKeyPlaceholder: "...",
    type: "openai_compatible",
    models: ["Hy3-Preview"],
  },
  {
    id: "zhipu",
    name: "Z.AI / GLM (Zhipu)",
    defaultBaseUrl: "https://open.bigmodel.cn/api/paas/v4",
    apiKeyPlaceholder: "...",
    type: "openai_compatible",
  },
  {
    id: "kimi",
    name: "Kimi / Moonshot",
    defaultBaseUrl: "https://api.moonshot.cn/v1",
    apiKeyPlaceholder: "sk-...",
    type: "openai_compatible",
  },
  {
    id: "minimax",
    name: "MiniMax (Global)",
    defaultBaseUrl: "https://api.minimax.chat/v1",
    apiKeyPlaceholder: "...",
    type: "openai_compatible",
  },
  {
    id: "minimax_cn",
    name: "MiniMax China",
    defaultBaseUrl: "https://api.minimaxi.com/v1",
    apiKeyPlaceholder: "...",
    type: "openai_compatible",
  },
  {
    id: "stepfun",
    name: "StepFun",
    defaultBaseUrl: "https://api.stepfun.com/v1",
    apiKeyPlaceholder: "...",
    type: "openai_compatible",
  },
  {
    id: "qwen",
    name: "Alibaba / DashScope (Qwen)",
    defaultBaseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    apiKeyPlaceholder: "sk-...",
    type: "openai_compatible",
  },
  // === Other ===
  {
    id: "xai",
    name: "xAI (Grok)",
    defaultBaseUrl: "https://api.x.ai/v1",
    apiKeyPlaceholder: "xai-...",
    type: "openai_compatible",
  },
  {
    id: "arcee",
    name: "Arcee AI (Trinity)",
    defaultBaseUrl: "https://api.arcee.ai/v1",
    apiKeyPlaceholder: "...",
    type: "openai_compatible",
  },
  {
    id: "ollama_cloud",
    name: "Ollama Cloud",
    defaultBaseUrl: "https://api.ollama.com/v1",
    apiKeyPlaceholder: "...",
    type: "openai_compatible",
  },
  {
    id: "lmstudio",
    name: "LM Studio (local)",
    defaultBaseUrl: "http://localhost:1234/v1",
    apiKeyPlaceholder: "留空即可",
    type: "openai_compatible",
  },
];

export function getProvider(id: string): ProviderMeta | undefined {
  return PROVIDERS.find((p) => p.id === id);
}

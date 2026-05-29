"use client";

import { useCallback, useRef, useState } from "react";
import { FileText, X } from "lucide-react";
import { Button, Textarea } from "@/components/ui";

/**
 * Collects contract text for a commercial review.
 *
 * The commercial WebSocket takes `contract_text` (a string), so we
 * read plain-text files (.txt / .md) directly in the browser. For
 * PDF/DOCX — which need server-side parsing not built in Phase A —
 * the user pastes the text instead. Both paths feed the same
 * `onTextChange` callback.
 */

const TEXT_EXTENSIONS = [".txt", ".md", ".markdown"];

function isPlainText(name: string): boolean {
  const lower = name.toLowerCase();
  return TEXT_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

interface ContractUploaderProps {
  value: string;
  onTextChange: (text: string) => void;
  disabled?: boolean;
}

export function ContractUploader({ value, onTextChange, disabled }: ContractUploaderProps) {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const readFile = useCallback(
    async (file: File) => {
      setNotice(null);
      if (!isPlainText(file.name)) {
        setFileName(null);
        setNotice(`暂不支持在浏览器中解析 ${file.name} —— 请将合同正文粘贴到下方文本框。`);
        return;
      }
      const text = await file.text();
      setFileName(file.name);
      onTextChange(text);
    },
    [onTextChange],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) void readFile(file);
    },
    [readFile],
  );

  const clearFile = useCallback(() => {
    setFileName(null);
    setNotice(null);
    onTextChange("");
    if (inputRef.current) inputRef.current.value = "";
  }, [onTextChange]);

  return (
    <div className="flex flex-col gap-3">
      <div
        role="button"
        tabIndex={0}
        aria-label="上传合同文本文件，或拖拽到此处"
        className={`rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
          dragging ? "border-brand bg-brand/5" : "border-border hover:border-brand/50"
        } ${disabled ? "pointer-events-none opacity-50" : "cursor-pointer"}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.md,.markdown,.pdf,.docx"
          className="hidden"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void readFile(file);
          }}
        />
        <div className="mb-2 flex justify-center">
          <div className="bg-brand/8 flex h-12 w-12 items-center justify-center rounded-xl">
            <FileText className="text-brand h-6 w-6" />
          </div>
        </div>
        <p className="text-sm font-medium">拖拽合同文件到此处，或点击上传</p>
        <p className="text-muted-foreground text-xs">支持 TXT / Markdown 直接读取；PDF / Word 请粘贴正文</p>
      </div>

      {fileName && (
        <div className="bg-muted flex items-center justify-between rounded-md px-3 py-2 text-sm">
          <span className="flex items-center gap-2 truncate">
            <FileText className="h-4 w-4 shrink-0 opacity-70" />
            {fileName}
          </span>
          <Button variant="ghost" size="sm" onClick={clearFile} disabled={disabled} className="h-7 px-2">
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {notice && <p className="text-amber-600 dark:text-amber-400 text-xs">{notice}</p>}

      <Textarea
        value={value}
        onChange={(e) => {
          onTextChange(e.target.value);
          if (fileName) setFileName(null);
        }}
        disabled={disabled}
        placeholder="或在此粘贴合同正文……"
        className="min-h-[180px] font-mono text-xs"
      />
      <p className="text-muted-foreground text-right text-xs">{value.length.toLocaleString()} 字符</p>
    </div>
  );
}

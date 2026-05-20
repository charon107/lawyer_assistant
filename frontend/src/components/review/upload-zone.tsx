"use client";

import { useState, useCallback } from "react";
import { FileText } from "lucide-react";

interface UploadZoneProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export function UploadZone({ onUpload, disabled }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) onUpload(file);
    },
    [onUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onUpload(file);
    },
    [onUpload]
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="上传法律文件，支持 PDF、Word、Markdown、TXT 格式"
      className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors
        ${dragging
          ? "border-brand bg-brand/5"
          : "border-border hover:border-brand/50"}
        ${disabled ? "opacity-50 pointer-events-none" : "cursor-pointer"}
      `}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          document.getElementById("document-upload")?.click();
        }
      }}
    >
      <input
        type="file"
        accept=".pdf,.docx,.txt,.md"
        onChange={handleChange}
        className="hidden"
        id="document-upload"
        disabled={disabled}
      />
      <label htmlFor="document-upload" className="cursor-pointer">
        <div className="flex justify-center mb-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand/8">
            <FileText className="h-8 w-8 text-brand" />
          </div>
        </div>
        <p className="text-lg font-medium mb-1">
          拖拽法律文件到此处，或点击上传
        </p>
        <p className="text-sm text-muted-foreground">
          支持 PDF、Word、Markdown、TXT
        </p>
        <p className="text-xs text-muted-foreground/70 mt-2">
          最大 50MB &middot; 文件不会上传到第三方服务器
        </p>
      </label>
    </div>
  );
}

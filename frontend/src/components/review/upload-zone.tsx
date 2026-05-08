"use client";

import { useState, useCallback } from "react";

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
      className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors
        ${dragging
          ? "border-blue-500 bg-blue-500/10"
          : "border-zinc-700 hover:border-zinc-500"}
        ${disabled ? "opacity-50 pointer-events-none" : "cursor-pointer"}
      `}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".pdf,.docx,.txt,.md"
        onChange={handleChange}
        className="hidden"
        id="lpa-upload"
        disabled={disabled}
      />
      <label htmlFor="lpa-upload" className="cursor-pointer">
        <div className="text-5xl mb-4">&#x1F4C4;</div>
        <p className="text-lg font-medium mb-1">
          拖拽法律文件到此处，或点击上传
        </p>
        <p className="text-sm text-zinc-400">
          支持 PDF、Word、Markdown、TXT
        </p>
        <p className="text-xs text-zinc-500 mt-2">
          最大 50MB &middot; 文件不会上传到第三方服务器
        </p>
      </label>
    </div>
  );
}

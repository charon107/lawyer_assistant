"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/stores";
import { useAdminUsers, type AdminUserDetail, type UserUpdatePayload } from "@/hooks/use-admin-users";
import {
  Badge,
  Button,
  Input,
  Label,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui";
import { MoreHorizontal, Search } from "lucide-react";
import { formatDate } from "@/lib/utils";

const PAGE_SIZE = 50;

type ActionDialog =
  | { kind: "edit"; user: AdminUserDetail }
  | { kind: "password"; user: AdminUserDetail }
  | { kind: "promote"; user: AdminUserDetail }
  | null;

export default function AdminUsersPage() {
  const t = useTranslations("admin");
  const { user: currentUser } = useAuthStore();
  const { users, total, isLoading, error, fetchUsers, updateUser } = useAdminUsers();

  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [page, setPage] = useState(0);
  const [dialog, setDialog] = useState<ActionDialog>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(() => {
    fetchUsers({
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
      search: search || undefined,
    });
  }, [fetchUsers, page, search]);

  useEffect(() => {
    if (currentUser?.role !== "admin") return;
    load();
  }, [currentUser, load]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    setSearch(searchInput.trim());
  };

  const doUpdate = useCallback(
    async (userId: string, payload: UserUpdatePayload) => {
      setActionError(null);
      try {
        await updateUser(userId, payload);
        await load();
        setDialog(null);
      } catch (err) {
        setActionError(err instanceof Error ? err.message : t("updateFailed"));
      }
    },
    [updateUser, load, t]
  );

  if (currentUser?.role !== "admin") {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="text-center text-muted-foreground py-12">{t("accessDenied")}</div>
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <TooltipProvider>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{t("usersTitle")}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{t("usersDesc")}</p>
        </div>

        <form onSubmit={handleSearch} className="flex items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder={t("searchUsers")}
              className="pl-9"
            />
          </div>
          <span className="text-sm text-muted-foreground">{t("total", { count: total })}</span>
        </form>

        {error && <div className="text-sm text-red-600">{error}</div>}

        <div className="overflow-x-auto rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("email")}</TableHead>
                <TableHead>{t("name")}</TableHead>
                <TableHead>{t("role")}</TableHead>
                <TableHead>{t("status")}</TableHead>
                <TableHead>{t("createdAt")}</TableHead>
                <TableHead className="w-20 text-right">{t("actions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.length === 0 && !isLoading && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                    {t("noUsers")}
                  </TableCell>
                </TableRow>
              )}
              {users.map((u) => {
                const isSelf = u.id === currentUser?.id;
                const isAdmin = u.role === "admin";
                return (
                  <TableRow key={u.id}>
                    <TableCell className="font-medium">{u.email}</TableCell>
                    <TableCell>{u.full_name || "—"}</TableCell>
                    <TableCell>
                      <Badge variant={isAdmin ? "default" : "secondary"}>
                        {isAdmin ? t("roleAdmin") : t("roleUser")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={u.is_active ? "default" : "destructive"}>
                        {u.is_active ? t("statusActive") : t("statusInactive")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDate(u.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-44">
                          <DropdownMenuItem onSelect={() => setDialog({ kind: "edit", user: u })}>
                            {t("editUser")}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {isAdmin ? (
                            <RoleMenuItem
                              disabled={isSelf}
                              disabledReason={t("cannotChangeSelfRole")}
                              label={t("demoteToUser")}
                              onClick={() => doUpdate(u.id, { role: "user" })}
                            />
                          ) : (
                            <RoleMenuItem
                              disabled={isSelf}
                              disabledReason={t("cannotChangeSelfRole")}
                              label={t("promoteToAdmin")}
                              onClick={() => setDialog({ kind: "promote", user: u })}
                            />
                          )}
                          {u.is_active ? (
                            <RoleMenuItem
                              disabled={isSelf}
                              disabledReason={t("cannotDisableSelf")}
                              label={t("disableAccount")}
                              onClick={() => doUpdate(u.id, { is_active: false })}
                            />
                          ) : (
                            <DropdownMenuItem
                              onSelect={() => doUpdate(u.id, { is_active: true })}
                            >
                              {t("enableAccount")}
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onSelect={() => setDialog({ kind: "password", user: u })}
                          >
                            {t("resetPassword")}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {t("pageInfo", { page: page + 1, total: totalPages })}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 0 || isLoading}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                {t("previousPage")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages - 1 || isLoading}
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              >
                {t("nextPage")}
              </Button>
            </div>
          </div>
        )}

        <PromoteConfirmDialog
          open={dialog?.kind === "promote"}
          user={dialog?.kind === "promote" ? dialog.user : null}
          onCancel={() => setDialog(null)}
          onConfirm={async (id) => {
            await doUpdate(id, { role: "admin" });
          }}
          error={actionError}
        />

        <EditUserDialog
          open={dialog?.kind === "edit"}
          user={dialog?.kind === "edit" ? dialog.user : null}
          onClose={() => {
            setDialog(null);
            setActionError(null);
          }}
          onSubmit={(id, payload) => doUpdate(id, payload)}
          error={actionError}
        />

        <ResetPasswordDialog
          open={dialog?.kind === "password"}
          user={dialog?.kind === "password" ? dialog.user : null}
          onClose={() => {
            setDialog(null);
            setActionError(null);
          }}
          onSubmit={(id, password) => doUpdate(id, { password })}
          error={actionError}
        />
      </div>
    </TooltipProvider>
  );
}

function RoleMenuItem({
  disabled,
  disabledReason,
  label,
  onClick,
}: {
  disabled: boolean;
  disabledReason: string;
  label: string;
  onClick: () => void;
}) {
  if (disabled) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className="relative flex cursor-not-allowed select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-muted-foreground/60"
            onClick={(e) => e.preventDefault()}
          >
            {label}
          </div>
        </TooltipTrigger>
        <TooltipContent side="left">{disabledReason}</TooltipContent>
      </Tooltip>
    );
  }
  return <DropdownMenuItem onSelect={onClick}>{label}</DropdownMenuItem>;
}

function PromoteConfirmDialog({
  open,
  user,
  onCancel,
  onConfirm,
  error,
}: {
  open: boolean;
  user: AdminUserDetail | null;
  onCancel: () => void;
  onConfirm: (userId: string) => Promise<void>;
  error: string | null;
}) {
  const t = useTranslations("admin");
  const [submitting, setSubmitting] = useState(false);

  return (
    <AlertDialog open={open} onOpenChange={(v) => !v && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("confirmPromoteTitle")}</AlertDialogTitle>
          <AlertDialogDescription>
            {t("confirmPromoteDesc")}
            {user && <div className="mt-2 font-mono text-sm">{user.email}</div>}
          </AlertDialogDescription>
        </AlertDialogHeader>
        {error && <div className="text-sm text-red-600">{error}</div>}
        <AlertDialogFooter>
          <AlertDialogCancel disabled={submitting}>{t("cancel")}</AlertDialogCancel>
          <AlertDialogAction
            disabled={submitting || !user}
            onClick={async (e) => {
              e.preventDefault();
              if (!user) return;
              setSubmitting(true);
              try {
                await onConfirm(user.id);
              } finally {
                setSubmitting(false);
              }
            }}
          >
            {submitting ? t("saving") : t("confirmPromote")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

function EditUserDialog({
  open,
  user,
  onClose,
  onSubmit,
  error,
}: {
  open: boolean;
  user: AdminUserDetail | null;
  onClose: () => void;
  onSubmit: (userId: string, payload: UserUpdatePayload) => Promise<void>;
  error: string | null;
}) {
  const t = useTranslations("admin");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user) {
      setEmail(user.email);
      setFullName(user.full_name || "");
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    const payload: UserUpdatePayload = {};
    if (email !== user.email) payload.email = email;
    if (fullName !== (user.full_name || "")) payload.full_name = fullName;
    if (Object.keys(payload).length === 0) {
      onClose();
      return;
    }
    setSubmitting(true);
    try {
      await onSubmit(user.id, payload);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("editUser")}</DialogTitle>
          <DialogDescription>{user?.email}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="edit-email">{t("email")}</Label>
            <Input
              id="edit-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="edit-name">{t("fullName")}</Label>
            <Input
              id="edit-name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder={t("fullNameOptional")}
            />
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              {t("cancel")}
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? t("saving") : t("save")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ResetPasswordDialog({
  open,
  user,
  onClose,
  onSubmit,
  error,
}: {
  open: boolean;
  user: AdminUserDetail | null;
  onClose: () => void;
  onSubmit: (userId: string, password: string) => Promise<void>;
  error: string | null;
}) {
  const t = useTranslations("admin");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setPassword("");
      setConfirm("");
      setLocalError(null);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    if (password.length < 8) {
      setLocalError(t("passwordTooShort"));
      return;
    }
    if (password !== confirm) {
      setLocalError(t("passwordMismatch"));
      return;
    }
    setLocalError(null);
    setSubmitting(true);
    try {
      await onSubmit(user.id, password);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("resetPassword")}</DialogTitle>
          <DialogDescription>{user?.email}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="new-password">{t("newPassword")}</Label>
            <Input
              id="new-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirm-password">{t("confirmPassword")}</Label>
            <Input
              id="confirm-password"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              minLength={8}
              required
            />
          </div>
          {(localError || error) && (
            <div className="text-sm text-red-600">{localError || error}</div>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              {t("cancel")}
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? t("saving") : t("save")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

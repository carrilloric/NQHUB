import React, { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNavbar } from "@/components/layout/TopNavbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { apiClient, ApiClient } from "@/services/api";
import type { Invitation, InvitationCreate } from "@/types/auth";
import { Copy, Mail, Plus, Trash2, CheckCircle, XCircle, Clock } from "lucide-react";
import { toast } from "sonner";

const Invitations: React.FC = () => {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Create form state
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"superuser" | "trader">("trader");
  const [expiresInDays, setExpiresInDays] = useState(7);

  useEffect(() => {
    loadInvitations();
  }, []);

  const loadInvitations = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getInvitations();
      setInvitations(data);
    } catch (error) {
      toast.error("Failed to load invitations", {
        description: ApiClient.getErrorMessage(error),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      const data: InvitationCreate = {
        email: email || undefined,
        role,
        expires_in_days: expiresInDays,
      };

      const invitation = await apiClient.createInvitation(data);
      setInvitations([invitation, ...invitations]);
      setIsCreateDialogOpen(false);

      // Reset form
      setEmail("");
      setRole("trader");
      setExpiresInDays(7);

      toast.success("Invitation created successfully", {
        description: "Share the token with the invited user",
      });
    } catch (error) {
      toast.error("Failed to create invitation", {
        description: ApiClient.getErrorMessage(error),
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteInvitation = async (id: number) => {
    if (!confirm("Are you sure you want to delete this invitation?")) {
      return;
    }

    try {
      await apiClient.deleteInvitation(id);
      setInvitations(invitations.filter((inv) => inv.id !== id));
      toast.success("Invitation deleted successfully");
    } catch (error) {
      toast.error("Failed to delete invitation", {
        description: ApiClient.getErrorMessage(error),
      });
    }
  };

  const handleCopyToken = (token: string) => {
    const registerUrl = `${window.location.origin}/register?token=${token}`;
    navigator.clipboard.writeText(registerUrl);
    toast.success("Registration link copied to clipboard");
  };

  const getInvitationStatus = (invitation: Invitation) => {
    if (invitation.used_at) {
      return {
        label: "Used",
        icon: CheckCircle,
        className: "text-green-500",
      };
    }
    if (new Date(invitation.expires_at) < new Date()) {
      return {
        label: "Expired",
        icon: XCircle,
        className: "text-red-500",
      };
    }
    return {
      label: "Active",
      icon: Clock,
      className: "text-blue-500",
    };
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <TopNavbar />
      <main className="pl-14 md:pl-60 pt-16 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Invitations</h1>
              <p className="text-muted-foreground mt-1">
                Manage user invitations and registration tokens
              </p>
            </div>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Invitation
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Invitation</DialogTitle>
                  <DialogDescription>
                    Generate a new invitation token to register a new user
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateInvitation}>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email (optional)</Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="user@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                      <p className="text-xs text-muted-foreground">
                        If specified, only this email can use the invitation
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="role">Role</Label>
                      <Select value={role} onValueChange={(value) => setRole(value as "superuser" | "trader")}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="trader">Trader</SelectItem>
                          <SelectItem value="superuser">Superuser</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="expiresInDays">Expires In (days)</Label>
                      <Input
                        id="expiresInDays"
                        type="number"
                        min={1}
                        max={365}
                        value={expiresInDays}
                        onChange={(e) => setExpiresInDays(parseInt(e.target.value))}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={isCreating}>
                      {isCreating ? "Creating..." : "Create"}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Invitations Table */}
          <div className="rounded-lg border border-border bg-card">
            {loading ? (
              <div className="flex items-center justify-center p-12">
                <div className="text-muted-foreground">Loading invitations...</div>
              </div>
            ) : invitations.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 text-center">
                <Mail className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold">No invitations yet</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Create your first invitation to start inviting users
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border bg-muted/50">
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Email
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Expires
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {invitations.map((invitation) => {
                      const status = getInvitationStatus(invitation);
                      const StatusIcon = status.icon;
                      return (
                        <tr key={invitation.id} className="hover:bg-muted/30">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className={`flex items-center gap-2 ${status.className}`}>
                              <StatusIcon className="h-4 w-4" />
                              <span className="text-sm font-medium">{status.label}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm">
                              {invitation.email || (
                                <span className="text-muted-foreground italic">Any email</span>
                              )}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                              {invitation.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                            {formatDate(invitation.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                            {formatDate(invitation.expires_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleCopyToken(invitation.token)}
                                disabled={invitation.used_at !== null || new Date(invitation.expires_at) < new Date()}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleDeleteInvitation(invitation.id)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Invitations;

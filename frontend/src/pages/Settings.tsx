import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LogOut } from "lucide-react";
import { useState } from "react";

import { PageContainer } from "@/components/layout/PageContainer";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toaster";
import { useAuth } from "@/hooks/use-auth";
import { api, ApiError } from "@/lib/api";
import { AGE_RANGES, CURRENCIES, USER_TYPES } from "@/lib/constants";
import type { ProfileUpdate } from "@/types/api";

interface ProfileFormProps {
  initialProfile: ProfileUpdate;
  onSave: (values: ProfileUpdate) => void;
  isSaving: boolean;
}

// Seeding `form` from `initialProfile` via useState's lazy initializer (not
// an effect) means this component's very first render already has the
// right values, instead of mounting empty and updating a tick later.
// Mounting a Radix Select with an empty value and then flipping it to a
// real one right after was silently resetting back to empty — that
// transition is exactly what this avoids.
function ProfileForm({ initialProfile, onSave, isSaving }: ProfileFormProps) {
  const [form, setForm] = useState<ProfileUpdate>(initialProfile);

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        onSave(form);
      }}
    >
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label>I am a</Label>
          <Select value={form.user_type ?? ""} onValueChange={(value) => setForm((f) => ({ ...f, user_type: value }))}>
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              {USER_TYPES.map((type) => (
                <SelectItem key={type} value={type}>
                  {type.replace("_", " ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label>Age range</Label>
          <Select
            value={form.age_range ?? ""}
            onValueChange={(value) => setForm((f) => ({ ...f, age_range: value }))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              {AGE_RANGES.map((range) => (
                <SelectItem key={range} value={range}>
                  {range}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="monthly_income">Monthly income</Label>
          <Input
            id="monthly_income"
            type="number"
            value={form.monthly_income ?? ""}
            onChange={(e) =>
              setForm((f) => ({ ...f, monthly_income: e.target.value ? Number(e.target.value) : undefined }))
            }
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="monthly_budget">Monthly budget</Label>
          <Input
            id="monthly_budget"
            type="number"
            value={form.monthly_budget ?? ""}
            onChange={(e) =>
              setForm((f) => ({ ...f, monthly_budget: e.target.value ? Number(e.target.value) : undefined }))
            }
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label>Currency</Label>
        <Select value={form.currency ?? "INR"} onValueChange={(value) => setForm((f) => ({ ...f, currency: value }))}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CURRENCIES.map((c) => (
              <SelectItem key={c.value} value={c.value}>
                {c.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Button type="submit" isLoading={isSaving}>
        Save changes
      </Button>
    </form>
  );
}

export function Settings() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.getProfile });

  const saveProfile = useMutation({
    mutationFn: (payload: ProfileUpdate) => api.updateProfile(payload),
    onSuccess: (data) => {
      toast.success("Profile updated");
      queryClient.setQueryData(["profile"], data);
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Couldn't update profile"),
  });

  const initials = user?.full_name
    ?.split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <PageContainer className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Settings</h2>
        <p className="text-sm text-muted-foreground">Manage your account and personalization preferences.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Account</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Avatar className="size-12">
              <AvatarFallback className="text-base">{initials ?? "?"}</AvatarFallback>
            </Avatar>
            <div>
              <p className="font-medium">{user?.full_name}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
            </div>
          </div>
          <Button variant="outline" onClick={logout}>
            <LogOut />
            Log out
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Profile</CardTitle>
        </CardHeader>
        <CardContent>
          {profile.isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-10" />
              <Skeleton className="h-10" />
              <Skeleton className="h-10" />
            </div>
          ) : profile.isError ? (
            <ErrorState onRetry={() => profile.refetch()} />
          ) : profile.data ? (
            <ProfileForm
              key={JSON.stringify(profile.data)}
              initialProfile={profile.data}
              onSave={(values) => saveProfile.mutate(values)}
              isSaving={saveProfile.isPending}
            />
          ) : null}
        </CardContent>
      </Card>
    </PageContainer>
  );
}

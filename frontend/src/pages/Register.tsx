import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Rocket } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/components/ui/toaster";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api";

const schema = z.object({
  full_name: z.string().min(1, "Name is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Use at least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

export function Register() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setIsSubmitting(true);
    try {
      await registerUser(values.email, values.password, values.full_name);
      navigate("/onboarding");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-sm space-y-6"
      >
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex size-10 items-center justify-center rounded-lg bg-brand text-brand-foreground">
            <Rocket className="size-5" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">Create your account</h1>
          <p className="text-sm text-muted-foreground">Start understanding your money with FinPilot AI</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="full_name">Full name</Label>
            <Input id="full_name" placeholder="Jane Doe" {...register("full_name")} />
            {errors.full_name && <p className="text-xs text-danger">{errors.full_name.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="you@example.com" {...register("email")} />
            {errors.email && <p className="text-xs text-danger">{errors.email.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" placeholder="At least 8 characters" {...register("password")} />
            {errors.password && <p className="text-xs text-danger">{errors.password.message}</p>}
          </div>
          <Button type="submit" className="w-full" isLoading={isSubmitting}>
            Create account
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-brand hover:underline">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

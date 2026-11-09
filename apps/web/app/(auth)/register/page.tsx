import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export const metadata = { title: "Create account" };

export default function RegisterPage() {
  return (
    <div>
      <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-leaf">Get started</p>
      <h1 className="mt-3 text-3xl font-extrabold tracking-[-0.045em]">
        Create your CropNet account
      </h1>
      <p className="mt-3 text-sm leading-6 text-muted">
        Account creation will be enabled when Supabase authentication is connected.
      </p>
      <form className="mt-8 space-y-5">
        <label className="block">
          <span className="mb-2 block text-sm font-bold">Full name</span>
          <Input placeholder="Enter your name" />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-bold">Phone or email</span>
          <Input placeholder="Enter your phone or email" />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-bold">Create password</span>
          <Input type="password" placeholder="Choose a secure password" />
        </label>
        <Button type="button" size="lg" className="w-full">
          Create account <ArrowRight size={18} />
        </Button>
      </form>
      <p className="mt-7 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-extrabold text-forest">
          Sign in
        </Link>
      </p>
    </div>
  );
}

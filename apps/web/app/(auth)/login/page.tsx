import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export const metadata = { title: "Sign in" };

export default function LoginPage() {
  return (
    <div>
      <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-leaf">Welcome back</p>
      <h1 className="mt-3 text-3xl font-extrabold tracking-[-0.045em]">
        Sign in to your farm workspace
      </h1>
      <p className="mt-3 text-sm leading-6 text-muted">
        Sign-in is unavailable until the CropNet account service is connected.
      </p>
      <form className="mt-8 space-y-5">
        <label className="block">
          <span className="mb-2 block text-sm font-bold">Phone or email</span>
          <Input type="text" placeholder="Enter your phone or email" />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-bold">Password</span>
          <Input type="password" placeholder="Enter your password" />
        </label>
        <Button type="button" size="lg" className="w-full">
          Continue <ArrowRight size={18} />
        </Button>
      </form>
      <p className="mt-7 text-center text-sm text-muted">
        New to CropNet?{" "}
        <Link href="/register" className="font-extrabold text-forest">
          Create an account
        </Link>
      </p>
    </div>
  );
}

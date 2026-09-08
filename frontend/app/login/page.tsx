import { Suspense } from "react";

import { AuthForm } from "@/components/auth-form";
import { SiteHeader } from "@/components/site-header";

export default function LoginPage() {
  return <main><SiteHeader /><Suspense><AuthForm mode="login" /></Suspense></main>;
}

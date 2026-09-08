import { Suspense } from "react";

import { AuthForm } from "@/components/auth-form";
import { SiteHeader } from "@/components/site-header";

export default function RegisterPage() {
  return <main><SiteHeader /><Suspense><AuthForm mode="register" /></Suspense></main>;
}

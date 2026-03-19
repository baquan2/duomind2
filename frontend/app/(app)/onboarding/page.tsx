import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard"

export default function OnboardingPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_hsl(var(--accent)/0.65),_transparent_30%),linear-gradient(180deg,_hsl(var(--background)),_hsl(var(--secondary)/0.35))]" />
      <div className="absolute left-[-8rem] top-16 -z-10 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
      <div className="absolute bottom-10 right-[-6rem] -z-10 h-80 w-80 rounded-full bg-accent/35 blur-3xl" />
      <OnboardingWizard />
    </div>
  )
}

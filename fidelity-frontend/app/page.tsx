export default function Home() {
  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold text-slate-900">
          Fidelity Control Center
        </h1>
        <p className="max-w-2xl text-base text-slate-600">
          This frontend connects to the FastAPI loyalty platform. Sign in to
          access your marketplace wallet or manage coupon inventory from the
          admin portal.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <FeatureCard
          title="Marketplace wallet"
          description="Track point balances and browse tenant-specific coupon offers."
          href="/marketplace/dashboard"
        />
        <FeatureCard
          title="Admin operations"
          description="Create coupon types, publish offers, and monitor live inventory."
          href="/admin/portal"
        />
      </div>
    </section>
  );
}

function FeatureCard({
  title,
  description,
  href,
}: {
  title: string;
  description: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
    </a>
  );
}

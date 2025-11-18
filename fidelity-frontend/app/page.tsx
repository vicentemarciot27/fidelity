import Link from 'next/link';

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="flex flex-col items-center text-center py-16 px-6">
        <h1 className="text-5xl font-bold text-slate-900 mb-4">
          Sistema de Fidelidade
        </h1>
        <p className="text-lg text-slate-600 max-w-3xl mb-8">
          Plataforma completa para gerenciamento de programas de fidelidade multi-tenant
        </p>
        <div className="flex gap-4 mb-16">
          <Link
            href="/marketplace/dashboard"
            className="bg-slate-900 text-white px-8 py-3 rounded-lg font-medium hover:bg-slate-800 transition"
          >
            Começar Agora
          </Link>
          <Link
            href="/login"
            className="bg-white text-slate-900 px-8 py-3 rounded-lg font-medium border-2 border-slate-300 hover:bg-slate-50 transition"
          >
            Fazer Login
          </Link>
        </div>

        {/* Feature Cards */}
        <div className="grid gap-6 md:grid-cols-2 w-full max-w-6xl">
          <FeatureCard
            title="Marketplace"
            description="Interface para clientes navegarem ofertas e gerenciarem pontos"
            href="/marketplace/dashboard"
            icon="marketplace"
            iconColor="text-blue-600"
            iconBg="bg-blue-50"
          />
          <FeatureCard
            title="Admin"
            description="Painel administrativo para gerenciar todo o sistema"
            href="/admin/portal"
            icon="admin"
            iconColor="text-slate-900"
            iconBg="bg-slate-100"
          />
        </div>
      </section>

      {/* Why Choose Section */}
      <section className="py-16 px-6 bg-slate-50">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            Por que escolher nosso sistema?
          </h2>
          <p className="text-lg text-slate-600 max-w-3xl mx-auto">
            Recursos avançados para maximizar o engajamento dos clientes e o crescimento do seu negócio
          </p>
          
          <div className="grid gap-8 md:grid-cols-3 mt-12">
            <BenefitCard
              title="Multi-tenant"
              description="Gerencie múltiplos negócios em uma única plataforma"
              icon="users"
            />
            <BenefitCard
              title="Analytics"
              description="Acompanhe métricas e insights em tempo real"
              icon="chart"
            />
            <BenefitCard
              title="Segurança"
              description="Sistema robusto com controle de acesso e auditoria"
              icon="shield"
            />
          </div>
        </div>
      </section>
    </div>
  );
}

function FeatureCard({
  title,
  description,
  href,
  icon,
  iconColor,
  iconBg,
}: {
  title: string;
  description: string;
  href: string;
  icon: string;
  iconColor: string;
  iconBg: string;
}) {
  return (
    <div className="flex flex-col items-center p-8 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition">
      <div className={`${iconBg} ${iconColor} p-4 rounded-xl mb-4`}>
        {icon === 'marketplace' && (
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
        )}
        {icon === 'admin' && (
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        )}
      </div>
      <h3 className="text-xl font-semibold text-slate-900 mb-2">{title}</h3>
      <p className="text-sm text-slate-600 text-center mb-6">{description}</p>
      <Link
        href={href}
        className="w-full bg-slate-900 text-white px-6 py-3 rounded-lg font-medium text-center hover:bg-slate-800 transition"
      >
        Acessar {title}
      </Link>
    </div>
  );
}

function BenefitCard({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <div className="flex flex-col items-center">
      <div className="text-blue-600 mb-4">
        {icon === 'users' && (
          <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        )}
        {icon === 'chart' && (
          <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        )}
        {icon === 'shield' && (
          <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        )}
      </div>
      <h3 className="text-xl font-semibold text-slate-900 mb-2">{title}</h3>
      <p className="text-sm text-slate-600 text-center">{description}</p>
    </div>
  );
}

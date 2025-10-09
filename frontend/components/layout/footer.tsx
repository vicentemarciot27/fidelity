export function Footer() {
  return (
    <footer className="bg-muted mt-auto">
      <div className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-semibold mb-4">Sistema de Fidelidade</h3>
            <p className="text-sm text-muted-foreground">
              Plataforma completa para gerenciamento de programas de fidelidade multi-tenant.
            </p>
          </div>

          <div>
            <h4 className="font-medium mb-4">Módulos</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/marketplace" className="text-muted-foreground hover:text-foreground">
                  Marketplace
                </a>
              </li>
              <li>
                <a href="/pdv" className="text-muted-foreground hover:text-foreground">
                  PDV
                </a>
              </li>
              <li>
                <a href="/admin" className="text-muted-foreground hover:text-foreground">
                  Admin
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-medium mb-4">Suporte</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#" className="text-muted-foreground hover:text-foreground">
                  Documentação
                </a>
              </li>
              <li>
                <a href="#" className="text-muted-foreground hover:text-foreground">
                  FAQ
                </a>
              </li>
              <li>
                <a href="#" className="text-muted-foreground hover:text-foreground">
                  Contato
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-medium mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#" className="text-muted-foreground hover:text-foreground">
                  Termos de Uso
                </a>
              </li>
              <li>
                <a href="#" className="text-muted-foreground hover:text-foreground">
                  Política de Privacidade
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-border mt-8 pt-8 text-center text-sm text-muted-foreground">
          <p>&copy; 2024 Sistema de Fidelidade. Todos os direitos reservados.</p>
        </div>
      </div>
    </footer>
  )
}

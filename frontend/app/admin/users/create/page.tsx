"use client"

import { AdminRegisterForm } from "@/components/auth/admin-register-form"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function CreateUserPage() {
  const handleCreateUser = async (data: any) => {
    console.log("[v0] Creating user with role:", data.role)
    // Implementation would call: await adminApi.createUser(data)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Criar Novo Usuário</CardTitle>
          <CardDescription>
            Criar usuários com roles administrativos (gerentes, admins de franquia, etc.)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AdminRegisterForm onSubmit={handleCreateUser} />
        </CardContent>
      </Card>
    </div>
  )
}

"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2 } from "lucide-react"
import { registerSchema } from "@/lib/schemas/auth"
import { z } from "zod"

const adminRegisterSchema = registerSchema.extend({
  role: z.enum(["store_manager", "franchise_admin", "super_admin"]),
  franchiseId: z.string().optional(),
  storeId: z.string().optional(),
})

type AdminRegisterInput = z.infer<typeof adminRegisterSchema>

interface AdminRegisterFormProps {
  onSubmit: (data: AdminRegisterInput) => Promise<void>
  isLoading?: boolean
}

export function AdminRegisterForm({ onSubmit, isLoading = false }: AdminRegisterFormProps) {
  const [error, setError] = useState<string | null>(null)
  const [selectedRole, setSelectedRole] = useState<string>("")

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<AdminRegisterInput>({
    resolver: zodResolver(adminRegisterSchema),
  })

  const handleFormSubmit = async (data: AdminRegisterInput) => {
    try {
      setError(null)
      await onSubmit(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar usuário")
    }
  }

  const roleOptions = [
    { value: "store_manager", label: "Gerente de Loja" },
    { value: "franchise_admin", label: "Admin de Franquia" },
    { value: "super_admin", label: "Super Admin" },
  ]

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <Label htmlFor="role">Tipo de Usuário</Label>
        <Select
          onValueChange={(value) => {
            setSelectedRole(value)
            setValue("role", value as any)
          }}
          disabled={isLoading}
        >
          <SelectTrigger>
            <SelectValue placeholder="Selecione o tipo de usuário" />
          </SelectTrigger>
          <SelectContent>
            {roleOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.role && <p className="text-sm text-destructive">{errors.role.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">Nome completo</Label>
        <Input
          id="name"
          type="text"
          placeholder="Nome completo do usuário"
          {...register("name")}
          disabled={isLoading}
        />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" placeholder="email@empresa.com" {...register("email")} disabled={isLoading} />
        {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone">Telefone</Label>
        <Input id="phone" type="tel" placeholder="(11) 99999-9999" {...register("phone")} disabled={isLoading} />
        {errors.phone && <p className="text-sm text-destructive">{errors.phone.message}</p>}
      </div>

      {(selectedRole === "franchise_admin" || selectedRole === "store_manager") && (
        <div className="space-y-2">
          <Label htmlFor="franchiseId">ID da Franquia</Label>
          <Input
            id="franchiseId"
            type="text"
            placeholder="ID da franquia"
            {...register("franchiseId")}
            disabled={isLoading}
          />
          {errors.franchiseId && <p className="text-sm text-destructive">{errors.franchiseId.message}</p>}
        </div>
      )}

      {selectedRole === "store_manager" && (
        <div className="space-y-2">
          <Label htmlFor="storeId">ID da Loja</Label>
          <Input id="storeId" type="text" placeholder="ID da loja" {...register("storeId")} disabled={isLoading} />
          {errors.storeId && <p className="text-sm text-destructive">{errors.storeId.message}</p>}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="password">Senha Temporária</Label>
        <Input
          id="password"
          type="password"
          placeholder="Senha temporária (usuário deve alterar)"
          {...register("password")}
          disabled={isLoading}
        />
        {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="confirmPassword">Confirmar Senha</Label>
        <Input
          id="confirmPassword"
          type="password"
          placeholder="Confirme a senha"
          {...register("confirmPassword")}
          disabled={isLoading}
        />
        {errors.confirmPassword && <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>}
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Criando usuário...
          </>
        ) : (
          "Criar Usuário"
        )}
      </Button>
    </form>
  )
}

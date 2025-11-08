# Fidelity Frontend

Next.js frontend application for the Fidelity loyalty and coupon system. Connects to the FastAPI backend to provide marketplace and admin interfaces.

## Prerequisites

- Node.js 18+ and pnpm (or npm/yarn)
- FastAPI backend running on `http://localhost:8000` (or configure via environment variable)

## Setup

1. Install dependencies:
```bash
pnpm install
```

2. Configure environment variables (optional):
```bash
cp .env.example .env
# Edit .env and set NEXT_PUBLIC_API_BASE_URL if different from http://localhost:8000
```

3. Start the development server:
```bash
pnpm dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## Testing Flows

### User/Marketplace Flow

1. **Login as a regular user:**
   - Navigate to `/login`
   - Use credentials from your FastAPI backend (user with `USER` role and associated `person_id`)
   - After login, you'll be redirected to `/marketplace/dashboard`

2. **View wallet:**
   - On the dashboard, see your point balances (toggle between points and BRL display)
   - View available coupons in your wallet

3. **Browse offers:**
   - The dashboard shows available coupon offers
   - Click on an offer card to view details

4. **Purchase a coupon:**
   - Click "Get coupon" on an offer detail page
   - The coupon code and QR code will be displayed
   - Your wallet will refresh automatically

### Admin Flow

1. **Login as admin:**
   - Navigate to `/login`
   - Use admin credentials (role: `ADMIN`, `GLOBAL_ADMIN`, `CUSTOMER_ADMIN`, or `FRANCHISE_MANAGER`)
   - After login, you'll be redirected to `/admin/portal`

2. **Create a coupon type:**
   - In the admin portal, fill out the "Create coupon type" form
   - Select redeem type (BRL, PERCENTAGE, or FREE_SKU)
   - Enter discount amount/percentage/SKUs as required
   - Click "Create coupon type"
   - Success toast will appear and the type list will refresh

3. **Create a coupon offer:**
   - Fill out the "Publish coupon offer" form
   - Select entity scope (CUSTOMER, FRANCHISE, or STORE)
   - Enter entity ID (UUID of the customer/franchise/store)
   - Select a coupon type from the dropdown
   - Set initial quantity, max per customer, and validity dates
   - Click "Create coupon offer"
   - Success toast will appear and the offer list will refresh

4. **View offer statistics:**
   - Click on an offer in the list to view details
   - Statistics show issued, reserved, redeemed, cancelled, and expired counts
   - Redemption breakdown by store and timeline are displayed

## Project Structure

```
fidelity-frontend/
├── app/                    # Next.js app router pages
│   ├── (auth)/            # Auth routes (route group, doesn't affect URL)
│   │   └── login/         # Login page at /login
│   ├── admin/             # Admin routes
│   │   └── portal/        # Admin portal at /admin/portal
│   ├── marketplace/       # Marketplace routes
│   │   ├── dashboard/     # Dashboard at /marketplace/dashboard
│   │   └── offers/        # Offer routes
│   │       └── [id]/      # Offer detail at /marketplace/offers/[id]
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── admin/            # Admin-specific components
│   ├── auth/             # Auth components (Protected route wrapper)
│   ├── layout/            # Layout components (AppShell)
│   ├── marketplace/      # Marketplace components
│   ├── providers/        # Context providers (Auth, App)
│   └── ui/               # Shared UI components (Toast)
├── hooks/                # Custom React hooks for data fetching
├── lib/                  # Utilities and type definitions
│   ├── api-client.ts     # HTTP client with auth
│   └── api-types.ts      # TypeScript types matching backend schemas
└── package.json
```

## Key Features

- **Authentication**: JWT-based auth with refresh tokens stored in localStorage
- **Route Protection**: Protected routes based on user roles
- **Toast Notifications**: Success/error feedback for user actions
- **Type Safety**: Full TypeScript types matching FastAPI schemas
- **Responsive Design**: Mobile-friendly UI using Tailwind CSS

## API Integration

The frontend communicates with the FastAPI backend via:
- `GET /offers` - List coupon offers
- `GET /offers/{id}` - Get offer details
- `POST /coupons/buy` - Purchase a coupon
- `GET /wallet` - Get user wallet (points and coupons)
- `POST /auth/login` - User authentication
- `GET /admin/coupon-types` - List coupon types (admin)
- `POST /admin/coupon-types` - Create coupon type (admin)
- `GET /admin/coupon-offers` - List coupon offers (admin)
- `POST /admin/coupon-offers` - Create coupon offer (admin)
- `GET /admin/coupon-offers/{id}` - Get offer details with stats (admin)

All authenticated requests include `Authorization: Bearer <token>` header automatically.

## Troubleshooting

- **404 errors**: Ensure route groups `(marketplace)` and `(admin)` have been renamed to `marketplace` and `admin` (route groups don't create URL segments)
- **API errors**: Verify the backend is running and `NEXT_PUBLIC_API_BASE_URL` is correct
- **Auth issues**: Check browser console for token storage errors; clear localStorage if needed
- **CORS errors**: Ensure backend CORS is configured to allow requests from `http://localhost:3000`

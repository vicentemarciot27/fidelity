'use client';

import { FormEvent, useState } from 'react';
import { ApiError, apiFetch } from '../../lib/api-client';
import type { CreateCouponTypeRequest } from '../../lib/api-types';
import { showToast } from '../ui/toast';

type CouponTypeFormProps = {
  onCreated: () => void;
};

const REDEEM_OPTIONS: CreateCouponTypeRequest['redeem_type'][] = [
  'BRL',
  'PERCENTAGE',
  'FREE_SKU',
];

export function CouponTypeForm({ onCreated }: CouponTypeFormProps) {
  const [redeemType, setRedeemType] =
    useState<CreateCouponTypeRequest['redeem_type']>('BRL');
  const [discountAmountBrl, setDiscountAmountBrl] = useState('');
  const [discountPercentage, setDiscountPercentage] = useState('');
  const [skuSpecific, setSkuSpecific] = useState(false);
  const [validSkus, setValidSkus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const payload: CreateCouponTypeRequest = {
      redeem_type: redeemType,
      sku_specific: skuSpecific,
    };

    if (redeemType === 'BRL') {
      payload.discount_amount_brl = Number(discountAmountBrl);
    } else if (redeemType === 'PERCENTAGE') {
      payload.discount_amount_percentage = Number(discountPercentage);
    } else if (redeemType === 'FREE_SKU') {
      payload.valid_skus = validSkus
        .split(',')
        .map((sku) => sku.trim())
        .filter(Boolean);
    }

    try {
      await apiFetch('/admin/coupon-types', 'POST', payload);
      showToast('Coupon type created successfully', 'success');
      onCreated();
      setDiscountAmountBrl('');
      setDiscountPercentage('');
      setValidSkus('');
      setSkuSpecific(false);
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = (err.body as { detail?: string })?.detail;
        const errorMsg = detail ?? 'Failed to create coupon type.';
        setError(errorMsg);
        showToast(errorMsg, 'error');
      } else {
        const errorMsg = 'Unexpected error while creating coupon type.';
        setError(errorMsg);
        showToast(errorMsg, 'error');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1 text-sm text-slate-600">
        <label>
          Redeem type
          <select
            value={redeemType}
            onChange={(event) =>
              setRedeemType(event.target.value as CreateCouponTypeRequest['redeem_type'])
            }
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
          >
            {REDEEM_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      {redeemType === 'BRL' ? (
        <LabeledInput
          label="Discount amount (BRL)"
          type="number"
          min="0"
          step="0.01"
          value={discountAmountBrl}
          onValueChange={setDiscountAmountBrl}
          required
        />
      ) : redeemType === 'PERCENTAGE' ? (
        <LabeledInput
          label="Discount percentage"
          type="number"
          min="0"
          max="100"
          step="0.1"
          value={discountPercentage}
          onValueChange={setDiscountPercentage}
          required
        />
      ) : (
        <LabeledInput
          label="Valid SKUs (comma separated)"
          type="text"
          value={validSkus}
          onValueChange={setValidSkus}
          placeholder="sku-1, sku-2"
          required
        />
      )}

      <label className="inline-flex items-center gap-2 text-sm text-slate-600">
        <input
          type="checkbox"
          checked={skuSpecific}
          onChange={(event) => setSkuSpecific(event.target.checked)}
          className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500"
        />
        SKU specific
      </label>

      {error ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={isSubmitting}
        className="inline-flex h-10 items-center justify-center rounded-md bg-slate-900 px-4 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Saving…' : 'Create coupon type'}
      </button>
    </form>
  );
}

function LabeledInput({
  label,
  value,
  onValueChange,
  ...props
}: {
  label: string;
  value: string;
  onValueChange: (value: string) => void;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'>) {
  return (
    <label className="flex flex-col gap-1 text-sm text-slate-600">
      {label}
      <input
        {...props}
        value={value}
        onChange={(event) => onValueChange(event.target.value)}
        className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
      />
    </label>
  );
}


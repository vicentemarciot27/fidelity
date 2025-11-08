'use client';

import { FormEvent, useState, useEffect } from 'react';
import { ApiError, apiFetch } from '../../lib/api-client';
import type {
  AdminCouponType,
  CouponOfferCreateRequest,
} from '../../lib/api-types';
import { showToast } from '../ui/toast';
import { useCustomers, useFranchises, useStores } from '../../hooks/use-admin-entities';

type CouponOfferFormProps = {
  couponTypes: AdminCouponType[];
  onCreated: () => void;
};

const ENTITY_OPTIONS: CouponOfferCreateRequest['entity_scope'][] = [
  'CUSTOMER',
  'FRANCHISE',
  'STORE',
];

export function CouponOfferForm({ couponTypes, onCreated }: CouponOfferFormProps) {
  const [entityScope, setEntityScope] =
    useState<CouponOfferCreateRequest['entity_scope']>('CUSTOMER');
  const [entityId, setEntityId] = useState('');
  const [couponTypeId, setCouponTypeId] = useState('');
  const [initialQuantity, setInitialQuantity] = useState('0');
  const [maxPerCustomer, setMaxPerCustomer] = useState('0');
  const [startAt, setStartAt] = useState('');
  const [endAt, setEndAt] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [segmentJson, setSegmentJson] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch entities based on scope
  const { customers, loading: loadingCustomers } = useCustomers();
  const { franchises, loading: loadingFranchises } = useFranchises();
  const { stores, loading: loadingStores } = useStores();

  // Reset entityId when scope changes
  useEffect(() => {
    setEntityId('');
  }, [entityScope]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const payload: CouponOfferCreateRequest = {
      entity_scope: entityScope,
      entity_id: entityId,
      coupon_type_id: couponTypeId,
      initial_quantity: Number(initialQuantity),
      max_per_customer: Number(maxPerCustomer),
      is_active: isActive,
    };

    if (startAt) {
      payload.start_at = new Date(startAt).toISOString();
    }
    if (endAt) {
      payload.end_at = new Date(endAt).toISOString();
    }
    if (segmentJson.trim()) {
      try {
        payload.customer_segment = JSON.parse(segmentJson);
      } catch {
        setError('Customer segment must be valid JSON.');
        setIsSubmitting(false);
        return;
      }
    }

    try {
      await apiFetch('/admin/coupon-offers', 'POST', payload);
      showToast('Coupon offer created successfully', 'success');
      onCreated();
      setEntityId('');
      setCouponTypeId('');
      setInitialQuantity('0');
      setMaxPerCustomer('0');
      setStartAt('');
      setEndAt('');
      setSegmentJson('');
      setIsActive(true);
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = (err.body as { detail?: string })?.detail;
        const errorMsg = detail ?? 'Failed to create coupon offer.';
        setError(errorMsg);
        showToast(errorMsg, 'error');
      } else {
        const errorMsg = 'Unexpected error while creating coupon offer.';
        setError(errorMsg);
        showToast(errorMsg, 'error');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get entity options based on scope
  const getEntityOptions = () => {
    if (entityScope === 'CUSTOMER') {
      return customers.map((c) => ({ value: c.id, label: c.name }));
    }
    if (entityScope === 'FRANCHISE') {
      return franchises.map((f) => ({ value: f.id, label: f.name }));
    }
    if (entityScope === 'STORE') {
      return stores.map((s) => ({ value: s.id, label: s.name }));
    }
    return [];
  };

  const isLoadingEntities =
    (entityScope === 'CUSTOMER' && loadingCustomers) ||
    (entityScope === 'FRANCHISE' && loadingFranchises) ||
    (entityScope === 'STORE' && loadingStores);

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="grid gap-4 md:grid-cols-2">
        <SelectField
          label="Entity scope"
          value={entityScope}
          onChange={(value) =>
            setEntityScope(value as CouponOfferCreateRequest['entity_scope'])
          }
          options={ENTITY_OPTIONS}
        />
        <SelectField
          label={
            entityScope === 'CUSTOMER'
              ? 'Customer'
              : entityScope === 'FRANCHISE'
              ? 'Franchise'
              : 'Store'
          }
          value={entityId}
          onChange={setEntityId}
          options={getEntityOptions()}
          placeholder={
            isLoadingEntities
              ? 'Loading...'
              : `Select ${entityScope.toLowerCase()}`
          }
          required
          disabled={isLoadingEntities}
        />
      </div>

      <SelectField
        label="Coupon type"
        value={couponTypeId}
        onChange={setCouponTypeId}
        options={couponTypes.map((type) => ({
          value: type.id,
          label: formatCouponTypeLabel(type),
        }))}
        placeholder="Select coupon type"
        required
      />

      <div className="grid gap-4 md:grid-cols-2">
        <LabeledInput
          label="Initial quantity"
          type="number"
          min="0"
          value={initialQuantity}
          onValueChange={setInitialQuantity}
          required
        />
        <LabeledInput
          label="Max per customer (0 = unlimited)"
          type="number"
          min="0"
          value={maxPerCustomer}
          onValueChange={setMaxPerCustomer}
          required
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <LabeledInput
          label="Start at"
          type="datetime-local"
          value={startAt}
          onValueChange={setStartAt}
        />
        <LabeledInput
          label="End at"
          type="datetime-local"
          value={endAt}
          onValueChange={setEndAt}
        />
      </div>

      <label className="inline-flex items-center gap-2 text-sm text-slate-600">
        <input
          type="checkbox"
          checked={isActive}
          onChange={(event) => setIsActive(event.target.checked)}
          className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500"
        />
        Offer is active
      </label>

      <label className="flex flex-col gap-1 text-sm text-slate-600">
        Customer segment (JSON, optional)
        <textarea
          value={segmentJson}
          onChange={(event) => setSegmentJson(event.target.value)}
          rows={3}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
          placeholder='{"zip_prefix": "123"}'
        />
      </label>

      {error ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={isSubmitting || couponTypes.length === 0}
        className="inline-flex h-10 items-center justify-center rounded-md bg-slate-900 px-4 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Saving…' : 'Create coupon offer'}
      </button>

      {couponTypes.length === 0 ? (
        <p className="text-xs text-slate-500">
          Create at least one coupon type before publishing offers.
        </p>
      ) : null}
    </form>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  placeholder,
  required,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options:
    | string[]
    | {
        label: string;
        value: string;
      }[];
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
}) {
  const normalized =
    typeof options[0] === 'string'
      ? (options as string[]).map((option) => ({
          label: option,
          value: option,
        }))
      : (options as { label: string; value: string }[]);

  return (
    <label className="flex flex-col gap-1 text-sm text-slate-600">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        disabled={disabled}
        className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="">{placeholder ?? 'Select an option'}</option>
        {normalized.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
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

function formatCouponTypeLabel(type: AdminCouponType) {
  if (type.redeem_type === 'BRL' && type.discount_amount_brl) {
    return `BRL • R$ ${Number(type.discount_amount_brl).toFixed(2)}`;
  }
  if (type.redeem_type === 'PERCENTAGE' && type.discount_amount_percentage) {
    return `Percentage • ${Number(type.discount_amount_percentage)}%`;
  }
  if (type.redeem_type === 'FREE_SKU') {
    return 'Free SKU';
  }
  return type.redeem_type;
}


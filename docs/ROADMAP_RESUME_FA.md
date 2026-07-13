
# RedShop resume-focused hardening roadmap

## Phase 01 - Critical financial integrity

This phase fixes the issues that experienced Django reviewers notice first:

- Payment callbacks are routed through a single atomic lifecycle service.
- Successful callbacks after cancellation move the order to payment_review.
- User deletion no longer deletes order history.
- Product deletion no longer deletes order item snapshots.
- Transaction history is protected from order deletion.
- Admin cannot directly edit paid/status fields.
- Database constraints protect discount, item quantity, and payment consistency.
- Regression tests document the critical behavior.

## Next phases

1. Password validation and login throttling.
2. Real pagination and product card annotations.
3. DOM XSS cleanup in live search and toast rendering.
4. Product feature constraints and default address constraints.
5. Checkout reservation expiry job for abandoned online payments.


## Phase 02 - Account security hardening

Implemented:

- Public registration now uses Django password validators.
- Login endpoint has cache-backed throttling for phone and IP failures.
- Profile editing supports email so password reset can work for phone-first users.
- Public profile forms no longer collect plaintext national ID or bank/card fields.
- Account security behavior is covered by regression tests.

Recommended next:

1. Replace email-only password reset with OTP or verified-email reset flow.
2. Add audit logs for admin-level account changes.
3. Add database constraints for default addresses.

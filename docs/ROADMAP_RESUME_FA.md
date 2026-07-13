
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


## Phase 03 - Frontend XSS and safe rendering

Implemented:

- Live Search no longer builds result rows with HTML string interpolation.
- Product names, categories, search terms, and prices are inserted with DOM APIs.
- Search result URLs are constrained to same-origin URLs.
- Toast messages use textContent instead of innerHTML.
- Admin chart JSON parsing uses escapejs instead of raw safe output.
- Static frontend safety checks were added as regression tests.

Recommended next:

1. Replace remaining trusted partial swaps with a tiny reviewed helper.
2. Add CSP headers before deployment.
3. Add integration tests for AJAX partial rendering.

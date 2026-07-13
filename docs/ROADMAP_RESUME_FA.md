
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


## Phase 04 - Database and domain constraints

Implemented:

- Each user can have at most one default address.
- Duplicate product feature values for the same product and feature are blocked.
- Product discounts cannot exceed product price.
- Product new_price must be zero or no greater than product price.
- Product comment score and suggest values are protected at database level.
- Existing duplicate/default data is normalized before constraints are applied.
- Domain integrity regression tests were added.

Recommended next:

1. Move address default selection into a small AddressService.
2. Add model-level clean methods for better form/admin error messages.
3. Add search/query performance improvements for product listing pages.


## Phase 05 - Product listing performance

Implemented:

- Product listing pages now use real Django pagination.
- AJAX filtering returns paginated product result HTML and page metadata.
- Product card query optimization is centralized in get_product_card_queryset.
- Product list ordering is deterministic, preventing pagination drift.
- Product detail related items no longer use expensive database random ordering.
- Live search now evaluates only a small optimized product list.
- Regression tests cover pagination, AJAX pagination, search limits, and random-order removal.

Recommended next:

1. Add annotated review counts/scores to product cards to remove comment N+1 queries.
2. Cache frequently used filter metadata by category.
3. Add full-text search or trigram search when moving beyond simple icontains.

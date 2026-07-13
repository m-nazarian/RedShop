
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


## Phase 06 - Product review annotations

Implemented:

- Product card querysets now include review_count and avg_score annotations.
- Review summary values are calculated from active comments only.
- Empty review summaries default to zero.
- Product list pages expose review annotations to card templates without extra queries.
- Regression tests cover annotated review counts, average score, and list-page availability.

Recommended next:

1. Display review_count and avg_score in the card UI if the current design needs it.
2. Add category-level cached filter metadata for heavy catalogs.
3. Add query-count tests around the product list after UI usage stabilizes.


## Phase 07 - Expired online order release

Implemented:

- Added release_expired_orders management command.
- The command releases only unpaid, pending, online orders older than the configured threshold.
- It uses row-level locking before invoking the order lifecycle service.
- Dry-run mode reports matching orders without changing data.
- Limit option prevents large one-off batches from overloading the system.
- Regression tests cover selection rules, dry-run behavior, and batch limits.

Recommended next:

1. Run the command periodically in production through cron, Task Scheduler, or a worker.
2. Add an admin action/report for orders in payment_review.
3. Add observability counters for released reservations.


## Phase 08 - Payment review admin tooling

Implemented:

- Added a dedicated admin filter for orders in payment_review.
- Added an admin badge so payment-review orders are visible in the order list.
- Added a CSV export action for payment-review orders.
- The export is read-only and does not mutate order/payment state.
- Regression tests verify admin registration, filtering, and CSV export behavior.

Recommended next:

1. Add a staff-only dashboard card for payment_review counts.
2. Add operational documentation for resolving payment_review orders.
3. Add audit logging if staff actions start changing payment-review state.


## Phase 09 - Security headers

Implemented:

- Added SecurityHeadersMiddleware.
- Added X-Content-Type-Options: nosniff.
- Added Referrer-Policy: same-origin.
- Added Permissions-Policy for camera, microphone, geolocation, and payment.
- Added Cross-Origin-Opener-Policy: same-origin.
- Added Content-Security-Policy in report-only mode by default.
- CSP can be enforced later with REDSHOP_ENFORCE_CSP=True.
- Regression tests verify headers, non-overwrite behavior, and CSP enforcement mode.

Recommended next:

1. Review CSP reports before enabling enforced CSP in production.
2. Move external assets to self-hosted static files where possible.
3. Add deployment-specific secure cookie/HSTS checks once production settings are split.


## Phase 10 - Deployment readiness checks

Implemented:

- Added redshop_deployment_check management command.
- Added checks for DEBUG, ALLOWED_HOSTS, SECRET_KEY, SSL redirect, HSTS, secure cookies, and CSP enforcement mode.
- Default mode reports findings without breaking local development.
- Strict mode raises a CommandError for blocking deployment risks.
- Regression tests cover safe production settings, insecure settings, strict mode, and wildcard hosts.

Recommended next:

1. Add this command to CI before deployment.
2. Split local and production settings modules.
3. Move secrets fully to environment variables.


## Phase 11 - Production settings from environment

Implemented:

- Added RedShop.env helpers for required values, booleans, integers, and lists.
- Added RedShop.settings_production for environment-driven production configuration.
- Production settings require DJANGO_SECRET_KEY and DJANGO_ALLOWED_HOSTS.
- Production defaults enable HTTPS redirect, secure cookies, HSTS, and enforced CSP.
- Local development settings remain unchanged.
- Regression tests cover env parsing, invalid env values, required secrets, required hosts, and production security defaults.

Recommended next:

1. Add a .env.example file documenting required deployment variables.
2. Add CI commands for check, tests, deployment check, and migration dry-run.
3. Add README deployment section.


## Phase 12 - Deployment documentation and CI

Implemented:

- Added .env.example with local and production-oriented variables.
- Added Persian deployment guide in docs/DEPLOYMENT_FA.md.
- Added GitHub Actions workflow for compile, migration dry-run, system check, deployment readiness report, and tests.
- Added static regression tests to ensure deployment docs and CI quality gates remain present.
- Removed temporary AI patch scripts left from the previous fix.

Recommended next:

1. Verify CI environment variable names against the final hosting provider.
2. Add README badges after the first successful GitHub Actions run.
3. Add production logging configuration and Sentry-style error reporting.


## Phase 13 - Production logging

Implemented:

- Added RedShop.logging_config with dependency-free production logging helpers.
- Added console logging for all deployments.
- Added optional rotating file logging through DJANGO_LOG_FILE.
- Added optional JSON logs through DJANGO_LOG_JSON.
- Added focused loggers for django, django.request, apps.orders, and apps.payment.
- Wired LOGGING into RedShop.settings_production through environment variables.
- Regression tests cover log-level normalization, console logging, file logging, JSON formatting, and production settings integration.

Recommended next:

1. Add request correlation IDs for tracing checkout and payment flows.
2. Add structured audit logs for staff actions on payment_review orders.
3. Add external error reporting such as Sentry when a production provider is chosen.


## Phase 14 - Request correlation IDs

Implemented:

- Added RequestIDMiddleware.
- Every response gets X-Request-ID.
- Valid incoming X-Request-ID values are preserved.
- Unsafe or oversized request IDs are replaced with generated UUID hex values.
- Request ID is stored in a context variable during the request lifecycle.
- Logging configuration now injects request_id into plain and JSON logs.
- Regression tests cover request headers, context reset, sanitizer behavior, log filter injection, JSON output, and logging config wiring.

Recommended next:

1. Add audit logging for staff actions on payment_review orders.
2. Include request_id in payment callback logs and operational runbooks.
3. Forward X-Request-ID through reverse proxy configuration in production.


## Phase 15 - Order audit logs

Implemented:

- Added OrderAuditLog as an append-only operational audit model.
- Added order, actor, action, request_id, message, metadata, and created_at fields.
- Added reusable log_order_audit helper.
- Added read-only Django admin for audit logs.
- Wrapped payment_review CSV export so every exported review order gets an audit record.
- Audit records include the current request_id for correlation with production logs.
- Regression tests cover manual audit logging, payment-review export audit logs, and read-only audit admin behavior.

Recommended next:

1. Add audit entries for explicit payment_review resolution actions once those actions exist.
2. Add request_id to payment gateway callback logs.
3. Add a staff-facing runbook for refund/re-reserve decisions.


## Phase 16 - Sensitive log redaction

Implemented:

- Added RedactingFilter for production logging.
- Added masking for emails, Iranian mobile numbers, card-like numbers, Bearer tokens, and secret key-value pairs.
- Added recursive redaction for dictionaries, lists, tuples, and sets.
- Logging handlers now apply redaction before request_id injection.
- JSON logs and plain logs both receive redacted messages.
- Regression tests cover text redaction, nested mappings, logging records, JSON output, and logging config wiring.

Recommended next:

1. Add explicit payment callback log events now that redaction and request_id are in place.
2. Add audit entries for future payment_review resolution actions.
3. Add a README security section summarizing redaction and request tracing.


## Phase 17 - Structured payment callback logging

Implemented:

- Added apps.payment.logging_events for safe payment callback event logging.
- Added hash_payment_identifier so raw gateway Authority values are not emitted.
- Added request_id-aware payment callback event payloads.
- Instrumented payment_verify with callback_received logging.
- Regression tests cover stable hashing, request_id propagation, raw Authority non-disclosure, and view instrumentation.

Recommended next:

1. Add more granular callback outcome logs after success, failure, cancel, and payment_review branches.
2. Add production runbook examples using request_id plus authority_hash.
3. Add alerting around repeated failed callback events once a monitoring provider is chosen.

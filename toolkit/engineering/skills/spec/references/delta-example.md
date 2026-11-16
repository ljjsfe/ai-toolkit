# Delta spec example

Read when drafting a delta spec for the first time in a repo, or when unsure of a section's
shape. All four delta sections are shown; a real delta includes only those it needs.

```markdown
# Auth Session (Delta)

## Purpose
Manages interactive user session lifecycle, rotation, and revocation across devices.

## ADDED Requirements

### Requirement: [REQ-AUTH-001] Session revocation on password change
The system SHALL revoke every active session of a user other than the initiating session when that user changes their password.

#### Scenario: Concurrent device session is rejected after password change
- **WHEN** an authenticated user changes their password from session A while session B is active
- **THEN** the next request authenticated with session B fails with HTTP 401
- **AND** session A remains authenticated

## MODIFIED Requirements

### Requirement: [REQ-AUTH-002] Idle session expiration
The system SHALL expire an interactive session after 24 hours of inactivity.
<!-- Full block required: include ALL surviving scenarios alongside any edited or new ones -->

#### Scenario: Request within idle window extends activity timestamp
- **WHEN** an authenticated request arrives 23 hours after the prior request
- **THEN** the request succeeds and the idle window resets to 24 hours

## REMOVED Requirements

### Requirement: [REQ-AUTH-003] Legacy query-string session token
**Reason**: Query-string tokens leak through referrer headers and access logs.
**Migration**: Clients send bearer tokens in the `Authorization` header or `HttpOnly` cookies.

## RENAMED Requirements

- FROM: `### Requirement: [REQ-AUTH-004] Login rate throttle`
- TO: `### Requirement: [REQ-AUTH-004] Credential-stuffing rate limit`
```

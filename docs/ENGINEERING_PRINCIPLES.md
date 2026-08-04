# ENGINEERING_PRINCIPLES.md

# ProDrive Engineering Principles

Version 1.0

---

# Purpose

This document defines how software is built at ProDrive.

Every engineer, AI coding assistant and contributor must follow these principles.

These rules exist to maximize:

* Maintainability
* Reliability
* Simplicity
* Performance
* Developer Experience

Good software is not measured by how quickly it is written.

It is measured by how easily it can be maintained five years later.

---

# Rule 1

## Build software for the next developer.

The next developer might be:

* another engineer
* your future self
* another AI

Code must explain itself.

---

# Rule 2

## Readability is more important than cleverness.

Avoid "smart" code.

Prefer obvious code.

Future maintainers should understand every function without explanation.

---

# Rule 3

## One responsibility per component.

Routes handle HTTP.

Services handle workflows.

Repositories handle persistence.

Models represent data.

Never mix responsibilities.

---

# Rule 4

## Business logic belongs in the backend.

Never implement business rules in:

Flutter

React

JavaScript

The frontend displays information.

The backend decides.

---

# Rule 5

## Prefer explicit code.

Avoid hidden magic.

Avoid unexpected side effects.

Prefer writing five understandable lines over one clever line.

---

# Rule 6

## Functions should be small.

Target:

20–40 lines.

If a function becomes difficult to understand:

Split it.

---

# Rule 7

## Classes should have one purpose.

Large classes become maintenance problems.

Split responsibilities early.

---

# Rule 8

## Never duplicate business logic.

One implementation.

One source of truth.

If copied twice:

Refactor.

---

# Rule 9

## Prefer composition.

Avoid deep inheritance.

Compose behavior from smaller services.

---

# Rule 10

## Name things clearly.

Bad

process()

handle()

manager()

Good

assign_driver()

generate_cmr()

calculate_loading_plan()

validate_vin()

Names should describe intent.

---

# Rule 11

## Every module must be independently understandable.

Opening the Orders module should not require reading unrelated modules.

Keep dependencies minimal.

---

# Rule 12

## Every feature must have a clear owner.

Examples

Orders module owns:

* Orders
* Stops
* Timeline

Fleet owns:

* Drivers
* Trucks
* Trailers

AI owns:

* Suggestions
* Parsing
* Recommendations

Ownership prevents duplicated logic.

---

# Rule 13

## APIs represent business actions.

Bad

update_status()

Good

accept_order()

complete_loading()

arrive_pickup()

Business language improves readability.

---

# Rule 14

## Validate everything.

Never trust:

Mobile apps.

Browsers.

External systems.

Every request is validated.

---

# Rule 15

## Never trust AI output.

AI suggestions are suggestions.

They must be validated.

Never automatically modify production data.

---

# Rule 16

## Fail safely.

Errors should never corrupt data.

Transactions should roll back.

Unexpected situations should be logged.

---

# Rule 17

## Prefer immutable data.

Avoid changing objects unexpectedly.

Return new objects where practical.

Predictability is more important than clever optimization.

---

# Rule 18

## Every important action is audited.

Who

When

What

Old value

New value

Reason

No exceptions.

---

# Rule 19

## Every feature should be testable.

Business logic should be independent from HTTP.

Testing should not require UI.

Backend testing should not require Flutter.

---

# Rule 20

## Logging is for production.

Logs should help diagnose problems.

Logs should never expose:

Passwords

Tokens

Personal data

Sensitive information

---

# Rule 21

## Optimize after measuring.

Never optimize because it "might" be slow.

Measure first.

Improve second.

---

# Rule 22

## Security is never optional.

Every endpoint:

Authorization.

Validation.

Permissions.

Input sanitization.

Parameterized queries.

Always.

---

# Rule 23

## Soft delete only.

Never permanently remove business data.

Historical information is valuable.

---

# Rule 24

## Every commit should improve the project.

Small commits.

Focused commits.

One feature per commit.

Examples

feat(auth): add JWT login

feat(order): implement order timeline

fix(driver): validate VIN before save

---

# Rule 25

## Code reviews

Before considering a task complete, ask:

Would I merge this into production?

If not:

Continue improving.

---

# Rule 26

## Documentation

Every significant module must explain:

Purpose

Dependencies

Public API

Examples

Limitations

Documentation evolves with the code.

---

# Rule 27

## Backward compatibility

Avoid breaking public APIs.

If breaking changes are required:

Create a new API version.

Never surprise existing clients.

---

# Rule 28

## AI Development Workflow

AI assists development.

AI does not replace engineering judgment.

Every generated implementation should be reviewed before acceptance.

Generated code is a starting point, not the final answer.

---

# Rule 29

## User Experience

Every feature should answer one question:

Does this save the dispatcher time?

or

Does this make the driver's work easier?

If not:

Reconsider the feature.

---

# Rule 30

## Simplicity wins.

Simple systems survive.

Complex systems fail.

Every implementation should strive to remove complexity instead of adding it.

---

# Rule 31

## Technical Debt

Technical debt is acceptable only when:

* documented
* intentional
* scheduled for removal

Never leave hidden shortcuts.

---

# Rule 32

## Error Messages

Errors should help users recover.

Bad

Unknown Error

Good

Vehicle VIN is invalid.

Expected 17 characters.

---

# Rule 33

## Configuration

Never hardcode:

URLs

Secrets

Passwords

Keys

Ports

Environment-specific values belong in configuration.

---

# Rule 34

## Architecture before implementation

Before writing code ask:

Where does this belong?

Avoid creating shortcuts that violate architecture.

---

# Rule 35

## Long-term thinking

Every implementation should assume:

ProDrive will eventually support

Thousands of companies.

Millions of vehicles.

Millions of orders.

Hundreds of concurrent users.

The architecture should not require redesign to reach those goals.

---

# Final Principle

The objective is not to write code.

The objective is to build software that transport companies trust with their daily operations.

Every engineering decision should increase trust, reliability and simplicity.

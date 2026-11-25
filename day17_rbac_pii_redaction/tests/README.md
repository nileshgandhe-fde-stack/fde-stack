# Security Guardrail Tests

## Overview

This directory contains pytest coverage for the Day 17 redaction and
role-protected retrieval behavior.

## Business purpose

The tests help ensure that sensitive text is scrubbed and that access roles
are derived from verified JWT claims rather than accepted as arbitrary
authorization input.

## Run

From the repository root, run
`python -m pytest day17_rbac_pii_redaction/tests -q`.

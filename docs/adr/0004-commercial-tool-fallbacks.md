# ADR 0004: Commercial Tool Fallbacks

## Status

Accepted for Milestone 1.

## Context

The target architecture may discuss Denodo and SAS Viya, but the project must remain runnable without either tool and must not fabricate evidence.

## Decision

Commercial-tool modes must be labelled honestly as `real_denodo`, `denodo_compatible_local`, `real_sas_viya`, or `local_model_lifecycle`. Milestone 1 implements none of these integrations beyond documentation and config placeholders.

## Consequences

The platform can show realistic enterprise boundaries while remaining locally runnable. Any future real integration requires genuine access and evidence.

## Alternatives Considered

Pretending local files are real commercial integrations was rejected. Removing commercial-tool references was rejected because future integration boundaries are part of the product story.

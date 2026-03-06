# Workflow 1: Advanced SEO Query Report

## Goal

Perform high-fidelity keyword research and mapping to generate a "Query Report" for a specific SEO campaign (Local, Regional, or National). The output will be a two-tab Google Spreadsheet created in a user-provided Drive folder.

## Inputs

1. **Google Drive Folder ID:** (Required)
2. **Campaign Type:** Local, Regional, or National.
3. **Money Pages:** URLs for Product, Service, or SEO landing pages (exclude Blog, Contact, About).
4. **Data Sources:** Exports from GSC (Volume) and Semrush (KD, Intent, Current Rankings).

## Process

1. **Campaign Scoping:**
   - Ask for Campaign Type at start.
   - Ask for "Money Pages" (Service/Product pages) to be mapped.
   - **Local:** Focus on `Keyword + City`. If no volume found, suggest generic location-less terms.
   - **Regional:** Focus on `Keyword + State/Region`. If no volume, suggest generic.
   - **National:** No GEO added. Mix Local + National recommendations if the business has a Physical home base.
   - **AEO/GEO targeting:** Actively identify and include queries that help rank for AI Answer Engines.
2. **Filtering:** Explicitly **exclude** all "near me" keywords.
3. **Merging:** Join datasets precisely:
   - Volume from GSC.
   - KD, Intent, and Rankings from Semrush.
4. **Categorization:** Map Semrush Intent to Funnel stages: Informational (ToFU), Navigational/Commercial (MoFU), Transactional (BoFU).

## Outputs

A Google Spreadsheet with:

- **Tab 1: Raw Keywords** - Compilation of all relevant business keywords.
- **Tab 2: Recommended Keywords & Mapping** - Final recommendations with columns:
  - Recommended Keywords
  - Search volume (GSC)
  - Keyword difficulty (Semrush)
  - Funnel (ToFU, MoFU, BoFU)
  - Current rankings (Semrush)
  - Mapped page (Mapping to Money Pages only)

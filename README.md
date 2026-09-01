# CyberScope Investigations

IMPORTANT:

Modify files only inside frontend/**.

Do not create, modify, rename, or delete anything inside backend/**.

The backend is maintained separately and must remain untouched.




Build the FRONTEND ONLY for my cybersecurity platform:

AI-Powered Email Threat Detection, GeoLocation and Forensic Intelligence Platform.

IMPORTANT:

I already have a separate FastAPI backend being developed.

Do NOT create backend logic.

Do NOT create Supabase tables.

Do NOT create Supabase Edge Functions.

Do NOT implement email parsing.

Do NOT implement threat detection.

Do NOT implement database logic.

The frontend must be cleanly structured so that I can later continue editing,

refactoring and connecting it to my FastAPI backend using Codex.

Use:

- React

- TypeScript

- Vite

- Tailwind CSS

- Framer Motion where useful for polished animations

- Lucide icons

Use the provided sample_analysis.json as the EXACT frontend data contract.

For now use mock data matching that contract.

Later the mock data will be replaced by calls to:

POST /api/v1/cases/analyze

GET /api/v1/cases

GET /api/v1/cases/{case_id}

GET /api/v1/cases/{case_id}/report

==================================================

VISUAL DIRECTION

==================================================

The design should closely follow this visual language:

PREMIUM DARK CYBERSECURITY INTERFACE

The overall visual feeling should be:

- extremely dark / near-black

- premium

- technical

- futuristic

- security-focused

- minimal

- high contrast

- sophisticated rather than flashy

Do NOT create a generic blue SaaS dashboard.

Do NOT make it look like a gaming dashboard.

Do NOT use excessive gradients everywhere.

The design should feel similar to a modern enterprise cybersecurity product.

==================================================

COLOR SYSTEM

==================================================

Primary background:

almost black

Examples:

#050505

#080808

#0A0A0A

Surface/card backgrounds:

#0D0D0D

#101010

#121212

Borders:

subtle dark gray

Primary accent:

bright acid / electric lime

Example visual direction:

#D7FF3F

#DFFF00

#CFFF33

Use lime for:

- active navigation

- primary buttons

- important statistics

- selected controls

- risk highlights where appropriate

- small glow effects

- hover accents

Secondary accents should be used SPARINGLY:

Cyan / aqua:

for infrastructure/network information

Magenta / pink:

for selected AI/security visual details

Red:

only for actual dangerous/critical states

Orange:

warnings

Green:

safe/pass

Do not turn the whole UI neon.

Most of the interface should remain black, white and charcoal.

==================================================

TYPOGRAPHY

==================================================

Use large bold modern sans-serif typography.

Headings should have:

- strong weight

- tight line height

- clean spacing

- large visual hierarchy

Main page titles should feel similar to a premium security company's website:

large

bold

white

minimal

Use smaller muted gray text for metadata.

Do not use overly decorative fonts.

==================================================

GLOBAL BACKGROUND

==================================================

Create a subtle technical background.

Possible effects:

- faint grid

- tiny dots

- subtle noise/grain

- faint radial illumination behind important content

- very subtle lime glow in selected areas

Keep it understated.

The background must not interfere with readability.

==================================================

CARD STYLE

==================================================

Cards are extremely important.

Use dark rectangular security panels.

Card appearance:

- nearly black fill

- thin #222 / #272727 border

- modest border radius

- clean spacing

- very subtle shadow

- optional internal grid/noise

Do NOT use giant rounded SaaS cards.

Cards should feel like technical modules.

==================================================

CARD HOVER EFFECT

==================================================

Create polished animated hover behavior.

When hovering:

- card lifts approximately 2-4px

- border becomes slightly brighter

- subtle lime glow can appear

- inner content shifts very slightly

- animation should be smooth

- optional light/spotlight following mouse position

- no exaggerated bouncing

Transition duration approximately:

200-350ms

Use smooth easing.

Some important cards may have a subtle animated border sweep.

Do not animate every element continuously.

Motion should happen primarily as a response to interaction.

==================================================

BUTTON STYLE

==================================================

PRIMARY BUTTON

Bright acid-lime background

black text

bold

compact

minimal radius

Hover:

- slight scale around 1.02

- subtle glow

- slightly brighter surface

- optional small arrow movement

Example:

Analyze Email   →

SECONDARY BUTTON

dark background

thin border

white text

Hover:

border changes toward lime

==================================================

NAVIGATION

==================================================

Create a fixed/collapsible left sidebar for the actual application.

Logo/project name at top.

Navigation:

Dashboard

Analyze Email

Investigations

Threat Intelligence

Reports

Bottom:

System Status

Settings

Active item:

- dark highlighted panel

- lime icon/accent

- subtle glow or side indicator

Hovering navigation items should create a smooth dark-to-highlight transition.

==================================================

APPLICATION ROUTES

==================================================

Create:

/dashboard

/analyze

/cases

/cases/:caseId

/reports

Also create a polished root page if useful:

/

But the actual product dashboard is the priority.

==================================================

DASHBOARD

==================================================

Create a premium cybersecurity operations dashboard.

Top header:

"Threat Intelligence Overview"

or

"Email Security Command Center"

Include:

- date/time area

- system status

- compact analyst profile area

Main statistics:

Emails Analyzed

Threats Detected

High Risk

Phishing

Business Email Compromise

Suspicious Attachments

Use dark cards.

Cards should NOT all look identical.

Use interesting sizing and composition.

For example:

large threat score card

smaller statistic cards

recent investigations

threat classification chart

authentication failures

infrastructure observations

Create a visually rich but clean Bento-style security dashboard.

==================================================

ANALYZE EMAIL PAGE

==================================================

This page should feel visually important.

Title:

Analyze Suspicious Email

Subtitle explaining that .eml files can be submitted for forensic analysis.

Create a large upload module.

The upload area should have:

- dark bordered box

- subtle animated grid

- email/file icon

- drag-and-drop

- Select .EML File

- maximum file size text

When a file is selected show:

filename

file size

file icon

remove button

Primary CTA:

ANALYZE EMAIL →

When analysis begins display animated stages:

1. Reading Email

2. Parsing MIME Structure

3. Extracting Headers

4. Extracting Indicators

5. Analyzing Threat Intent

6. Checking Threat Intelligence

7. Mapping Infrastructure

8. Calculating Risk

9. Complete

Create an elegant scanning animation.

For example:

- moving thin lime scan line

- subtle progress indicator

- active stage glowing lime

- completed stages check marked

Do not fake backend functionality.

This is visual state only for now.

==================================================

INVESTIGATION PAGE

==================================================

This is the MOST IMPORTANT page.

Route:

/cases/:caseId

Create a professional security analyst workspace.

TOP HEADER

Show:

Case ID

Subject

Sender

Receiver

Timestamp

Buttons:

Generate Report

Export Evidence

==================================================

RISK HERO

==================================================

Create a visually impressive main threat summary.

Example:

87

/100

HIGH RISK

The number should be large.

Use an animated circular or semicircular risk indicator,

but keep it professional.

HIGH:

orange/red

CRITICAL:

red

LOW:

green

MEDIUM:

yellow

Beside it display:

Threat Classification

Phishing

Business Email Compromise

Social Engineering

And:

6 Threat Indicators Detected

==================================================

EXPLAINABLE RISK

==================================================

Create a prominent card:

"Why this email was flagged"

Show something like:

SPF authentication failed                +10

DMARC authentication failed              +12

Display-name impersonation detected      +12

Urgent payment request                   +10

Business Email Compromise pattern        +15

Suspicious URL                           +10

Negative infrastructure reputation       +12

Use thin horizontal separators.

Hovering a signal should reveal more information.

==================================================

INVESTIGATION NAVIGATION

==================================================

Use tab navigation:

Overview

Email Forensics

Authentication

Indicators

Infrastructure

AI Findings

Timeline

Evidence

Tabs should animate smoothly.

Active tab:

lime indicator

white text

Inactive:

muted gray

==================================================

OVERVIEW

==================================================

Show:

Threat Summary

Email Summary

Risk Breakdown

Key Findings

Infrastructure Summary

Authentication Summary

Use an asymmetric dashboard layout.

==================================================

EMAIL FORENSICS

==================================================

Create structured panels for:

Sender

Receiver

Subject

Date

Message-ID

Reply-To

Return-Path

Add:

MIME Structure

Display MIME hierarchy visually.

Example:

multipart/mixed

    ├── text/plain

    ├── text/html

    └── application/pdf

Create:

Received Header Chain

Each routing hop should appear as a connected technical timeline.

==================================================

AUTHENTICATION

==================================================

Create three strong cards:

SPF

DKIM

DMARC

Example:

SPF

FAIL

DKIM

PASS

DMARC

FAIL

Use large state text.

PASS:

green

FAIL:

red

UNKNOWN:

gray

Add concise explanations underneath.

==================================================

INDICATORS

==================================================

Create professional IOC tables.

Sections:

IP Addresses

Domains

URLs

Attachments

Use columns appropriate to each type.

IP:

IP Address

Reputation

Source

Actions

Domain:

Domain

Reputation

Type

URL:

URL

Domain

Reputation

Attachment:

Filename

MIME Type

Size

SHA-256

Status

Hashes must use monospace fonts.

Long hashes should support copy-to-clipboard.

Rows should have subtle hover highlighting.

==================================================

INFRASTRUCTURE

==================================================

Title:

Observed Email Infrastructure

IMPORTANT:

Never call this:

Attacker Location

Show this disclaimer prominently but elegantly:

"Observed infrastructure information represents routing/network

infrastructure associated with the email and does not establish

the physical location or identity of the attacker."

Create an attractive infrastructure route visualization.

For example:

Email Origin

    ↓

Hop 1

    ↓

Hop 2

    ↓

Receiving Mail Server

For each infrastructure node show:

IP

Country

Region

City

ISP

ASN

Reputation

Use cyan selectively for infrastructure/network elements.

If map visualization is added, keep it visually subtle.

==================================================

AI FINDINGS

==================================================

Create individual cards for:

Phishing

Social Engineering

Urgency

Credential Request

Payment Request

Impersonation

Business Email Compromise

Suspicious Call-to-Action

Each card:

Title

Detected / Not Detected

Confidence

Evidence

Explanation

Detected cards can show a subtle accent glow.

Do not make every result giant.

==================================================

TIMELINE

==================================================

Create a vertical forensic timeline.

Example:

14:03:11

Email received for analysis

14:03:11

SHA-256 evidence hash calculated

14:03:12

MIME structure parsed

14:03:12

Routing headers extracted

14:03:13

Threat analysis completed

14:03:14

Threat intelligence completed

14:03:14

Risk score calculated

Timeline should animate subtly when displayed.

==================================================

EVIDENCE

==================================================

Create evidence cards for:

Original Email SHA-256

Attachment SHA-256 hashes

Analysis Timestamp

Case ID

Evidence Events

Provide copy buttons.

Use monospace text.

==================================================

REPORT

==================================================

Create:

Generate Forensic Report

primary action.

Report card should explain that the platform can generate a structured

forensic investigation report.

Do not claim automatic legal admissibility.

==================================================

CASES PAGE

==================================================

Create investigation table.

Columns:

Risk

Subject

Sender

Classification

Created

Status

Add:

search

severity filter

threat-type filter

Rows should have polished hover behavior.

Clicking a row opens:

/cases/:caseId

==================================================

ANIMATION SYSTEM

==================================================

Use Framer Motion where appropriate.

Animation style:

subtle

premium

controlled

responsive

Use:

fade + slight translate

card hover lift

border illumination

count-up risk score

tab transitions

staggered card entrance

button arrow movement

dropdown transitions

progress/scanning animation

Do NOT use:

large bouncing

constant spinning

excessive parallax

gaming effects

random animations

The interface should still feel extremely professional.

==================================================

SPECIAL VISUAL ELEMENT

==================================================

Create one reusable abstract cybersecurity visual inspired by

interconnected digital blocks / data cubes.

It should use combinations of:

lime

cyan

magenta

against black.

It can appear on:

landing page

empty analysis state

login/hero area

Use CSS/SVG/HTML elements if possible.

Do not copy logos, wording, artwork or branding from another company.

Create an original visual using only the same general design language.

==================================================

RESPONSIVENESS

==================================================

Prioritize desktop/laptop because this is an analyst workstation.

Target:

1920x1080

1440x900

1366x768

Still make it usable on tablet/mobile.

==================================================

CODE ARCHITECTURE — EXTREMELY IMPORTANT

==================================================

I will continue development later using Codex.

Therefore the project MUST be easy for another coding agent to understand.

Do NOT place the whole application in one giant component.

Create clean separation.

Preferred structure:

src/

  components/

    ui/

    dashboard/

    investigation/

    forensics/

    indicators/

    infrastructure/

    findings/

    timeline/

  pages/

    DashboardPage.tsx

    AnalyzePage.tsx

    CasesPage.tsx

    InvestigationPage.tsx

    ReportsPage.tsx

  services/

    api.ts

  types/

    analysis.ts

  mocks/

    sampleAnalysis.ts

  hooks/

  lib/

  styles/

Create reusable components.

Examples:

StatCard

RiskScore

ThreatBadge

AuthenticationCard

FindingCard

IOCDataTable

InfrastructureHop

TimelineEvent

EvidenceHash

SectionHeader

==================================================

DESIGN TOKENS

==================================================

Centralize colors and visual variables.

Do not hardcode lime/black values separately in dozens of components.

Use CSS variables or Tailwind configuration for:

--background

--surface

--surface-hover

--border

--foreground

--muted

--accent

--danger

--warning

--success

--network

--ai

This is important because I want Codex to be able to change

the entire visual theme later easily.

==================================================

API ARCHITECTURE

==================================================

Create:

src/services/api.ts

Use:

VITE_API_BASE_URL

For now the API layer can return mock EmailAnalysis data.

Do NOT hardcode mock data directly inside page components.

Later I should be able to replace:

getMockAnalysis()

with a real fetch/API call without redesigning the UI.

Do not create backend code.

==================================================

TYPE ARCHITECTURE

==================================================

Create TypeScript interfaces that match the supplied

sample_analysis.json exactly.

Do not invent incompatible fields.

Keep all types centralized.

==================================================

FINAL REQUIREMENTS

==================================================

Before finishing:

1. ensure all routes work

2. ensure there are no broken imports

3. ensure TypeScript compiles

4. ensure responsive layout

5. ensure mock investigation renders

6. ensure animations remain smooth

7. ensure components are modular

8. ensure backend logic has NOT been created

9. ensure Supabase backend has NOT been created

10. ensure the frontend can later be edited easily with Codex

The final result should feel like a high-end enterprise cybersecurity

investigation platform with the visual quality of the supplied reference,

while remaining an original design.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/0298e1fd-0493-4b14-9874-3e0b12690ecc).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```

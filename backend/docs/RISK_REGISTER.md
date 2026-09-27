# Risk Register — Budget Tracker

Repository: https://github.com/gkeerthi1/budget-tracker

## Introduction

This document tracks the Budget Tracker web application's risk management using
Probability / Consequence / Exposure (P/C/E) scoring. Risks are identified and
documented incrementally during development, re-analyzed weekly, and closed
once they are no longer valid. All identified risks, even historic ones, are
dated and shown below with their current status, week by week.

## Methodology

Each risk is scored using the P/C/E model from the course textbook (Laporte &
April, referencing the Therac-25 case).

- **P (Probability):** 1 = not likely, 5 = certain
- **C (Consequence):** 1 = minimal impact, 5 = unacceptable
- **Exposure (E) = P × C**
- **Category:** Technical, Management, or Other
- **Status:** P = In Progress (active), C = Completed (mitigated)

---

## Week of Aug 9 — Project Setup & Category CRUD

| ID | Risk Description | Category | P | C | E | Mitigation | Status |
|----|----|----|----|----|----|----|----|
| 1 | One team member's local setup was missing a package, which caused Flask's default password hashing to crash for them but not for others. | Other | 4 | 2 | 8 | Pinned password hashing to `pbkdf2:sha256` explicitly instead of relying on the platform default. | Keerthi | C |
| 2 | When the initial PR was pushed, the repository was empty, so the current PR branch was treated as the default and bypassed any PR review. | Management | 3 | 3 | 9 | Created a proper `master` branch and set it as default. From then on, every change goes through PR review. | Keerthi | C |
| 3 | GitHub's private-repo tier doesn't enforce branch protection rules, meaning PR changes could be merged without approval. | Other | 5 | 2 | 10 | Made the repository public, which enables branch protection rule enforcement. | Keerthi | C |
| 4 | If transaction dates are handled inconsistently, transactions can be assigned to the wrong month, making budget totals and overspending calculations incorrect. | Technical | 3 | 4 | 12 | Compare and store all dates in ISO format, kept to a single timezone. | Keerthi & Sachin | P |
| 5 | Recurring transactions, savings goals, and budget rollover all operate on the same budget data. Without a defined order of operations, results could become inconsistent. | Technical | 3 | 5 | 15 | Define and test the ordering of these operations; a dedicated integration test suite is needed for the full interaction flow. | Keerthi & Sachin | P |

Changes made this week: Risks 1, 2, 3 identified and closed. Risks 4 and 5 identified and still in progress.

## Week of Aug 16 – Aug 28 — No development

No commits this week. Open risks #4 and #5 were reviewed with no change to probability, consequence, or status.

## Week of Aug 29 — Monthly Budgets, Overspending Warnings, Dashboard (v1.0)

| ID | Risk Description | Category | P | C | E | Mitigation | Status |
|----|----|----|----|----|----|----|----|
| 6 | Tests were hardcoded with a fixed date (2026-08-01), so once filtered by the real current month, they returned nothing. | Technical | 4 | 3 | 12 | Updated all tests to use the real current date so monthly test data stays valid regardless of when tests run. | Keerthi | C |
| 7 | Deleting a category with existing transactions could break historic transaction totals. | Technical | 3 | 3 | 9 | When a category is deleted, its transactions have `category_id` set to `NULL` instead of being deleted or otherwise affected. | Sachin | C |
| 8 | Overall spending was calculated as the sum of category budgets rather than a fixed monthly limit, which affects the accuracy of the 80%/100% threshold alerts. | Technical | 3 | 3 | 9 | Identified during weekly risk review. Scoped to be addressed before system testing. | Sachin | P |

Risks 6 and 7 identified and closed. Risk 8 identified and scoped to finish before system testing. Risks 4 and 5 reviewed, still open.

## Week of Sep 6 — Recurring Transactions, Savings Goals, Budget Rollover, Month Comparison (v2.0)

Risk #5 addressed and closed this week. New risks identified:

| ID | Risk Description | Category | P | C | E | Mitigation | Status |
|----|----|----|----|----|----|----|----|
| 9 | Flask has no built-in task scheduler, so recurring transactions and budget rollover cannot trigger automatically each month. | Technical | 4 | 3 | 12 | Both are triggered on login instead, with rollover always applied before recurring-transaction generation to keep ordering consistent. | Keerthi | C |
| 10 | The Flask app uses a hardcoded secret key locally, which would be risky if exposed beyond local development. | Technical | 5 | 3 | 15 | Documented as a known, accepted out-of-scope limitation since no third-party integration or public deployment is planned. | Keerthi & Sachin | C |
| 11 | Backend logic is complete, but the Angular frontend is still in progress. It needs to be finished before system testing with Playwright. | Technical | 5 | 4 | 20 | Angular frontend with all features planned before system testing so the full flow can be exercised. 71 backend tests currently cover the backend logic. | Keerthi & Sachin | P |

Risk 9 (scheduling trigger) identified and closed. Risk 5 (budget rollover) thoroughly tested and closed — dedicated integration tests covering overspending, recurring transactions, and rollover interactions caught and fixed a few order-of-operations bugs. Risk 8 remains open, to be addressed before system testing. Risk 10 accepted as out-of-scope and closed. Risk 11 identified and left open. Risk 4 re-reviewed, still open (related to ISO date consistency).

**Summary of status as of Sep 12:**
Closed: #1, #2, #3, #5, #6, #7, #9, #10 (8 risks)
In-progress: #4, #8, #11 (3 risks)
Highest priority: Risk #8 (overall spending calculation) and Risk #11 (Angular frontend), both needed before the system testing deadline.

## Week of Sep 26 — Angular Frontend Complete, System Testing Prep

| ID | Risk Description | Category | P | C | E | Mitigation | Responsible | Status |
|----|----|----|----|----|----|----|----|
| 4 (update) | If transaction dates are handled inconsistently, transactions can be assigned to the wrong month, making budget calculations incorrect. | Technical | 3 | 4 | 12 | Backend already stored and compared all dates in ISO format. With the Angular frontend now built, the date input field also submits ISO-format (`yyyy-mm-dd`) dates, closing the last gap where inconsistent formatting could enter the system. | Keerthi & Sachin | C |
| 8 (update) | Overall spending is calculated as the sum of category budgets instead of a fixed monthly limit. | Technical | 3 | 3 | 9 | Given the approaching system testing deadline, reviewed and accepted as an out-of-scope limitation for this semester. The sum-of-categories approach still produces correct overspending warnings for tested scenarios; a fixed overall limit is noted as a possible future improvement. No further action planned. | Sachin | C |
| 11 (update) | Backend logic is complete, but the Angular frontend was still in progress and needed to be finished before system testing with Playwright. | Technical | 5 | 4 | 20 | Angular frontend built covering all Version 1 and Version 2 features — auth, category management, transactions with budget warnings, dashboard, month-to-month comparison, recurring transactions, and savings goals. Merged to master via PR on Sep 26. 71 backend tests remain passing; frontend is now ready for Playwright system testing. | Keerthi & Sachin | C |
| 12 (new) | Playwright test suite has not yet been written, and the System Testing Report is due Oct 2. Splitting test coverage between two team members increases coordination risk if scope or naming conventions diverge. | Management | 3 | 3 | 9 | Test files divided by feature area (Version 1 core flow vs. Version 2 features) between team members, using `data-testid` attributes already built into the UI for stable, non-brittle selectors. Prioritizing scenarios explicitly committed to in the project proposal first. | Keerthi & Sachin | P |

**Summary of status as of Sep 26:**
Closed: #1, #2, #3, #4, #5, #6, #7, #8, #9, #10, #11 (11 risks)
In-progress: #12 (1 risk)
Highest priority: Risk #12 — complete the Playwright system test suite before the Oct 2 deadline.
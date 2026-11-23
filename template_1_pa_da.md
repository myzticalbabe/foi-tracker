# Template 1 — PA District Attorney (Private Criminal Complaint)

**Channel (verified, Pa.R.Crim.P. 506 + county DA pages):** the affiant (you) completes
AOPC Form 411A and submits it to the **Office of the District Attorney** (attorney for
the Commonwealth), which approves or disapproves "without unreasonable delay."
Approved → DA transmits to the issuing authority (magisterial district judge).
Disapproved with reasons → you may petition the **court of common pleas** for review.

**Preconditions — do not skip:**
1. Report to the local police agency with jurisdiction FIRST. (York County: a referral
   is denied and bounced to police if you have not contacted them.)
2. Probable-cause standard applies to you as affiant exactly as to an officer —
   "mere allegation is not sufficient" (Monroe County DA).
3. Contents must satisfy Rule 504. Get Form 411A from the MDJ office, county DA, or
   pacourts.us. Filing fee ~$25 (verify current).
4. Felonies: some counties (e.g. Montgomery) will not approve felony charges on a
   private complaint — those must go through the police agency where it happened.

## Packet sections (packet_builder.py fills 1/3/4 from the matters log)
- [ ] Form 411A fully completed, statutes identified (ask County Detectives which
      18 Pa.C.S. sections apply if unsure)
- [ ] Narrative: thorough, detailed facts establishing probable cause, each claim
      tied to an exhibit number
- [ ] Exhibit list with sha256 (from `matters_log.py exhibit`)
- [ ] Police-contact record: agency, date, report/incident number (or written
      explanation why police route was unavailable)
- [ ] Approval gate: `matters_log.py approve` by the human, THEN hand-deliver/mail
      to DA Private Complaint Unit; log channel + proof via `mark-filed`

**Sources:** 234 Pa. Code Rule 506 (pacodeandbulletin.gov); Lancaster/Monroe/York/
Montgomery/Northampton County DA private-complaint pages; LegalClarity AOPC-411A guide.

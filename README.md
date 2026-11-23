# foi_tracker

Lawful-transparency toolkit: log FOI requests, criminal complaints, and
committee correspondence in one SQLite store, and build submission packets
from verified Pennsylvania templates.

- `matters_log.py` — the matters log (one SQLite store; every row carries
  channel-appropriate proof).
- `packet_builder.py` — assembles a submission packet from a matter row.
- `template_1_pa_da.md` — PA District Attorney private criminal complaint
  (Pa.R.Crim.P. 506, AOPC Form 411A).
- `template_2_pa_ag.md` — PA Attorney General complaint channel.
- `template_3_committee.md` — legislative committee correspondence.

SOUL LICENCE ONLY — see `LICENSE` (`LicenseRef-SoulForge-1.0`).

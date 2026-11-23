"""Filing-packet builder: renders a human-review packet from a matter + its exhibits.

The agent PREPARES. A human approves (matters_log.py approve), files through the
valid channel, and records proof (mark-filed). Nothing here sends anything.

Usage:
    python packet_builder.py <matter-id> [--out packet_<id>.md]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from matters_log import DB_PATH

TEMPLATES = {
    "foi": ("Freedom of Information Request", "records requested", "statutory response deadline"),
    "criminal_complaint": ("Criminal Complaint (DRAFT — requires sworn verification before filing)",
                            "alleged conduct", "filing channel (email is NOT filing; verify per agency)"),
    "committee": ("Legislative Committee Correspondence (DRAFT)",
                  "matter brought to the committee", "requested action"),
}


def build(matter_id: int) -> str:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    m = con.execute("SELECT * FROM matters WHERE id=?", (matter_id,)).fetchone()
    if not m:
        raise SystemExit(f"no matter #{matter_id}")
    exhibits = con.execute(
        "SELECT * FROM exhibits WHERE matter_id=? ORDER BY exhibit_no", (matter_id,)).fetchall()
    con.close()
    title, body_label, foot_label = TEMPLATES[m["matter_type"]]
    lines = [
        f"# {title}",
        "",
        f"**Matter:** #{m['id']} | **Recipient:** {m['recipient']}",
        f"**Subject:** {m['subject']}",
        f"**Reference:** {m['ref_no'] or '(none yet)'}",
        f"**Status:** {m['status']} — DO NOT FILE WHILE DRAFT",
        "",
        "## 1. Cover statement",
        "",
        f"> [Human to complete/verify: one-paragraph statement of {body_label}.]",
        "",
        "## 2. Factual narrative (each claim cites an exhibit)",
        "",
        "> [Human to complete/verify: numbered paragraphs. Every factual claim",
        ">  must cite Exhibit N. Remove any claim with no exhibit.]",
        "",
        "## 3. Exhibit list",
        "",
    ]
    if exhibits:
        for e in exhibits:
            lines.append(f"- **Exhibit {e['exhibit_no']}:** {e['title']} "
                         f"(`{e['path'] or 'no file'}` sha256:{e['sha256'] or '-'})")
            if e["description"]:
                lines.append(f"  {e['description']}")
    else:
        lines.append("_No exhibits attached. Attach with matters_log.py exhibit before approval._")
    lines += [
        "",
        "## 4. Filing record",
        "",
        f"- Channel: {m['channel'] or '(not filed)'}",
        f"- Proof: {m['proof'] or '(none — filing without proof is refused by mark-filed)'}",
        f"- {foot_label}: {m['deadline'] or '(none set)'}",
        "",
        "## 5. Approval",
        "",
        "- [ ] Human reviewed every claim against its exhibit",
        "- [ ] Recipient + channel verified as valid for this filing type",
        "- [ ] Approved via `matters_log.py approve` before any sending",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render a review packet for a matter")
    p.add_argument("matter_id", type=int)
    p.add_argument("--out", default="")
    args = p.parse_args(argv)
    text = build(args.matter_id)
    out = args.out or f"packet_{args.matter_id}.md"
    Path(out).write_text(text, encoding="utf-8")
    print(f"wrote {out} (review packet — nothing sent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Matters log: FOI requests, criminal complaints, committee correspondence.

One SQLite store. Every row carries channel-appropriate proof:
  email      -> provider message_id
  certified  -> USPS certified mail number
  portal     -> portal confirmation number
  in_person  -> receipt / docket stamp note

Usage:
    python matters_log.py init
    python matters_log.py add --type foi --recipient "..." --subject "..." --deadline 2026-12-09
    python matters_log.py report            # overdue + due within 7 days
    python matters_log.py list --status open
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).with_suffix(".db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS matters (
    id INTEGER PRIMARY KEY,
    matter_type TEXT NOT NULL CHECK (matter_type IN ('foi','criminal_complaint','committee')),
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    ref_no TEXT DEFAULT '',
    channel TEXT DEFAULT '' CHECK (channel IN ('','email','certified','portal','in_person')),
    sent_at TEXT DEFAULT '',
    proof TEXT DEFAULT '',
    deadline TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','filed','acknowledged','responded','closed','overdue')),
    notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS exhibits (
    id INTEGER PRIMARY KEY,
    matter_id INTEGER NOT NULL REFERENCES matters(id),
    exhibit_no TEXT NOT NULL,
    title TEXT NOT NULL,
    path TEXT DEFAULT '',
    sha256 TEXT DEFAULT '',
    description TEXT DEFAULT ''
);
"""


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def cmd_init(_args: argparse.Namespace) -> int:
    con = connect()
    con.executescript(SCHEMA)
    con.commit()
    con.close()
    print(f"initialized {DB_PATH}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    con = connect()
    cur = con.execute(
        "INSERT INTO matters (matter_type, recipient, subject, ref_no, channel, deadline, status, notes)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (args.type, args.recipient, args.subject, args.ref_no or "",
         args.channel or "", args.deadline or "", "draft", args.notes or ""),
    )
    con.commit()
    print(f"added matter id={cur.lastrowid} status=draft (nothing sent)")
    con.close()
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    """Human approval gate: draft -> approved. Filing/sending is a separate step."""
    con = connect()
    cur = con.execute(
        "UPDATE matters SET status='approved' WHERE id=? AND status='draft'", (args.id,))
    con.commit()
    ok = cur.rowcount == 1
    print(f"matter {args.id} {'approved' if ok else 'NOT approved (must be draft)'}")
    con.close()
    return 0 if ok else 1


def cmd_mark_filed(args: argparse.Namespace) -> int:
    """Record the actual filing. Requires prior approval and a proof reference."""
    if not args.proof:
        print("refusing: filing without proof (message_id / certified number / portal confirmation)")
        return 1
    con = connect()
    cur = con.execute(
        "UPDATE matters SET status='filed', channel=?, sent_at=?, proof=? "
        "WHERE id=? AND status='approved'",
        (args.channel, args.sent_at or date.today().isoformat(), args.proof, args.id),
    )
    con.commit()
    ok = cur.rowcount == 1
    print(f"matter {args.id} {'filed' if ok else 'NOT filed (must be approved first)'}")
    con.close()
    return 0 if ok else 1


def cmd_exhibit(args: argparse.Namespace) -> int:
    import hashlib
    sha = ""
    if args.path:
        p = Path(args.path)
        if p.is_file():
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
    con = connect()
    con.execute(
        "INSERT INTO exhibits (matter_id, exhibit_no, title, path, sha256, description)"
        " VALUES (?,?,?,?,?,?)",
        (args.matter, args.no, args.title, args.path or "", sha, args.description or ""),
    )
    con.commit()
    con.close()
    print(f"exhibit {args.no} attached to matter {args.matter} sha256={sha[:16] or '-'}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    con = connect()
    rows = con.execute(
        "SELECT id, matter_type, recipient, subject, status, deadline FROM matters"
        + (" WHERE status=?" if args.status else "") + " ORDER BY id",
        ((args.status,) if args.status else ()),
    ).fetchall()
    for r in rows:
        print(f"#{r['id']} [{r['matter_type']}/{r['status']}] {r['recipient']} — {r['subject']} (due {r['deadline'] or '-'})")
    print(f"total: {len(rows)}")
    con.close()
    return 0


def cmd_report(_args: argparse.Namespace) -> int:
    today = date.today().isoformat()
    soon = (date.today() + timedelta(days=7)).isoformat()
    con = connect()
    rows = con.execute(
        "SELECT id, matter_type, recipient, subject, deadline, status FROM matters"
        " WHERE status NOT IN ('responded','closed') AND deadline != '' ORDER BY deadline").fetchall()
    overdue = [r for r in rows if r["deadline"] < today]
    due = [r for r in rows if today <= r["deadline"] <= soon]
    print(f"OVERDUE ({len(overdue)}):")
    for r in overdue:
        print(f"  #{r['id']} [{r['matter_type']}] {r['recipient']} — {r['subject']} (was due {r['deadline']})")
    print(f"DUE WITHIN 7 DAYS ({len(due)}):")
    for r in due:
        print(f"  #{r['id']} [{r['matter_type']}] {r['recipient']} — {r['subject']} (due {r['deadline']})")
    con.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FOI / complaint / committee matters log")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    a = sub.add_parser("add"); a.set_defaults(func=cmd_add)
    a.add_argument("--type", required=True, choices=["foi", "criminal_complaint", "committee"])
    a.add_argument("--recipient", required=True)
    a.add_argument("--subject", required=True)
    a.add_argument("--ref-no", default="")
    a.add_argument("--channel", default="", choices=["", "email", "certified", "portal", "in_person"])
    a.add_argument("--deadline", default="")
    a.add_argument("--notes", default="")
    a2 = sub.add_parser("approve"); a2.set_defaults(func=cmd_approve); a2.add_argument("id", type=int)
    m = sub.add_parser("mark-filed"); m.set_defaults(func=cmd_mark_filed); m.add_argument("id", type=int)
    m.add_argument("--channel", required=True, choices=["email", "certified", "portal", "in_person"])
    m.add_argument("--proof", required=True)
    m.add_argument("--sent-at", default="")
    e = sub.add_parser("exhibit"); e.set_defaults(func=cmd_exhibit); e.add_argument("--matter", type=int, required=True)
    e.add_argument("--no", required=True); e.add_argument("--title", required=True)
    e.add_argument("--path", default=""); e.add_argument("--description", default="")
    l = sub.add_parser("list"); l.set_defaults(func=cmd_list); l.add_argument("--status", default="")
    sub.add_parser("report").set_defaults(func=cmd_report)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

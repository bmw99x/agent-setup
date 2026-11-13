from app.jobs.commands import command


@command("purge-drafts")
def purge_drafts(conn):
    deleted = conn.execute("DELETE FROM invoices WHERE status = 'DRAFT'").rowcount
    conn.commit()
    print(f"purged {deleted} drafts")

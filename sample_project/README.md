# Campus Queue

Campus Queue lets students reserve a place in a registrar office queue before
walking to the counter. Staff can advance the queue and mark a student as served.

The prototype stores queue entries in a local SQLite database. It does not yet
authenticate students, so anyone who knows a reservation code can view that
reservation. We plan to add sign-in before a public launch.

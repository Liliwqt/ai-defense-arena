"""Temporary native status presentation; no inference, storage or task ownership."""
from contextlib import contextmanager

import streamlit as st


@contextmanager
def temporary_activity(label, context=None):
    slot = st.empty()
    status = None
    context = " ".join(context.split())[:160] if context else None

    def update(label):
        nonlocal status
        if label.startswith('Waiting to retry…'):
            slot.info(label)
            status = None
        elif status is None:
            with slot.container():
                status = st.status(label, expanded=True)
                if context:
                    status.caption('Current context')
                    status.text(context)
        else:
            status.update(label=label)

    try:
        update(label)
        yield update
    finally:
        slot.empty()

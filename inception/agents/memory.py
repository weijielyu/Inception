"""Memory agent: the only writer of world state. Validates and commits deltas, keeps the
episodic log, and answers "what plot event is due now" on a wall-clock basis."""
from __future__ import annotations

from ..state import Commitment, HistoryEntry
from .base import Agent
from .prediction import StateDelta


class MemoryAgent(Agent):
    name = "memory"

    def commit(self, delta: StateDelta) -> list[str]:
        s = self.session
        with s.lock:
            st = s.state
            notes: list[str] = []
            by_name = {e.name.lower(): e for e in st.entities}
            for e in delta.entities_added:
                cur = by_name.get(e.name.lower())
                if cur is not None:
                    cur.state, cur.where, cur.hidden = e.state, e.where, e.hidden
                    notes.append(f"merged duplicate entity {e.name}")
                else:
                    st.entities.append(e)
                    by_name[e.name.lower()] = e
            for e in delta.entities_updated:
                cur = by_name.get(e.name.lower())
                if cur is None:
                    st.entities.append(e)
                    by_name[e.name.lower()] = e
                    notes.append(f"update for unknown entity {e.name}: added")
                else:
                    cur.state = e.state or cur.state
                    cur.where = e.where or cur.where
                    cur.hidden = e.hidden
            for name in delta.entities_removed:
                st.entities = [x for x in st.entities if x.name.lower() != name.lower()]
            if delta.player_position:
                st.player.position = delta.player_position
            for i in delta.inventory_add:
                if i not in st.player.inventory:
                    st.player.inventory.append(i)
            for i in delta.inventory_remove:
                if i in st.player.inventory:
                    st.player.inventory.remove(i)
                else:
                    notes.append(f"tried to remove missing inventory item {i}")
            st.player.health = max(0, min(10, st.player.health + delta.health_change))
            for x in delta.status_add:
                if x not in st.player.status:
                    st.player.status.append(x)
            st.player.status = [x for x in st.player.status if x not in delta.status_remove]
            for f in delta.new_facts:
                if f not in st.facts:
                    st.facts.append(f)
            st.flags.update(delta.flags)
            s.save()
        self.emit("commit", notes=notes, delta=delta.model_dump())
        return notes

    def record_turn(self, action: str, outcome: str, narration: str) -> None:
        s = self.session
        with s.lock:
            st = s.state
            st.turn += 1
            st.history.append(HistoryEntry(turn=st.turn, action=action, outcome=outcome, narration=narration))
            s.save()

    def add_commitments(self, items: list[Commitment]) -> None:
        with self.session.lock:
            self.session.state.commitments.extend(items)
            self.session.save()

    def due_commitments(self) -> list[Commitment]:
        """Plot beats whose wall-clock trigger has passed. Marks them fired."""
        s = self.session
        with s.lock:
            st = s.state
            now = st.elapsed()
            due = [c for c in st.commitments if not c.fired and c.trigger_seconds <= now]
            for c in due:
                c.fired = True
            if due:
                s.save()
        if due:
            self.emit("commitments_due", events=[c.event for c in due])
        return due

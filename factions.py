"""Computed faction analysis for Japan-VOTE.

Factions are induced from voting similarity. They are not declared in the data.
The same calculation supports a report/graph and a decision strategy.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations


def vote_map(data, member_id: str, exclude_bill_id: str | None = None) -> dict[str, str]:
    member = data.members[member_id]
    result = {}
    for bill_id, vote in member.vote_history.items():
        if bill_id != exclude_bill_id and vote in {"for", "against"}:
            result[bill_id] = vote
    for bill_id, bill in data.bills.items():
        if bill_id == exclude_bill_id:
            continue
        vote = bill.real_votes.get(member_id)
        if vote in {"for", "against"}:
            result[bill_id] = vote
    return result


def agreement(left: dict[str, str], right: dict[str, str]) -> tuple[float, int]:
    common = sorted(set(left) & set(right))
    if not common:
        return 0.0, 0
    same = sum(1 for bill_id in common if left[bill_id] == right[bill_id])
    return same / len(common), len(common)


def pairwise_similarities(data, exclude_bill_id: str | None = None) -> dict[tuple[str, str], tuple[float, int]]:
    maps = {member_id: vote_map(data, member_id, exclude_bill_id) for member_id in data.members}
    pairs = {}
    for left, right in combinations(sorted(data.members), 2):
        pairs[(left, right)] = agreement(maps[left], maps[right])
    return pairs


def compute_factions(data, exclude_bill_id: str | None = None, threshold: float = 0.72, min_common: int = 3) -> list[list[str]]:
    pairs = pairwise_similarities(data, exclude_bill_id)
    graph = {member_id: set() for member_id in data.members}
    for (left, right), (score, common) in pairs.items():
        if common >= min_common and score >= threshold:
            graph[left].add(right)
            graph[right].add(left)

    seen = set()
    factions = []
    for member_id in sorted(graph):
        if member_id in seen:
            continue
        stack = [member_id]
        component = []
        seen.add(member_id)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in sorted(graph[current]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        factions.append(sorted(component))
    factions.sort(key=lambda group: (-len(group), group[0]))
    return factions


def member_faction(data, member_id: str, exclude_bill_id: str | None = None) -> dict:
    factions = compute_factions(data, exclude_bill_id)
    pairs = pairwise_similarities(data, exclude_bill_id)
    for index, faction in enumerate(factions, start=1):
        if member_id not in faction:
            continue
        peer_scores = []
        for peer in faction:
            if peer == member_id:
                continue
            key = tuple(sorted((member_id, peer)))
            if key in pairs:
                peer_scores.append(pairs[key][0])
        cohesion = sum(peer_scores) / len(peer_scores) if peer_scores else 0.0
        return {
            "id": f"faction_{index}",
            "members": faction,
            "peers": [peer for peer in faction if peer != member_id],
            "cohesion": cohesion,
        }
    return {"id": "faction_0", "members": [member_id], "peers": [], "cohesion": 0.0}


def faction_projected_vote(data, member_id: str, bill_id: str) -> dict:
    bill = data.bills[bill_id]
    faction = member_faction(data, member_id, exclude_bill_id=bill_id)
    counts = defaultdict(int)
    evidence = []
    for peer_id in faction["peers"]:
        peer = data.members[peer_id]
        vote = bill.party_positions.get(peer.party)
        if vote in {"for", "against"}:
            counts[vote] += 1
            evidence.append((peer_id, vote))
    if not counts:
        vote = None
    elif counts["for"] > counts["against"]:
        vote = "for"
    elif counts["against"] > counts["for"]:
        vote = "against"
    else:
        vote = None
    return {
        **faction,
        "vote": vote,
        "counts": dict(counts),
        "evidence": evidence,
    }


def mermaid_graph(data, exclude_bill_id: str | None = None) -> str:
    pairs = pairwise_similarities(data, exclude_bill_id)
    lines = ["graph LR"]
    for member_id, member in data.members.items():
        lines.append(f'  {node_id(member_id)}["{member.name_en}"]')
    for (left, right), (score, common) in pairs.items():
        if common >= 3 and score >= 0.72:
            lines.append(f"  {node_id(left)} -- {score:.2f} / {common} --- {node_id(right)}")
    return "\n".join(lines)


def node_id(member_id: str) -> str:
    return member_id.replace("member_", "m_")

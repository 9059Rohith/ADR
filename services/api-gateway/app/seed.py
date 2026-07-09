"""SentinelArena — Seed Data.

Creates the venue graph, density evaluator, and SOP documents
for initialization. This provides a realistic, fully-functional
demo environment.

DOCUMENTED AS SIMULATED DATA: The venue layout, POIs, and SOP documents
are synthetic data designed for demonstration purposes. In production,
these would be loaded from the database.
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

from app.core.density_evaluator import DensityEvaluator
from app.core.pathfinding import (
    AccessibilityType,
    GraphEdge,
    GraphNode,
    VenueGraph,
)


def create_venue_graph() -> VenueGraph:
    """Create a realistic venue graph for the demo stadium.

    The stadium has:
    - 3 floors (Ground, Level 1, Level 2)
    - 12 zones (A-L)
    - 6 gates, multiple restrooms, food courts, medical stations
    - Elevators and ramps for accessibility

    All coordinates are in a 1000x600 SVG space.
    """
    graph = VenueGraph()

    # ── Ground Floor (Level 0) ──
    nodes_ground = [
        GraphNode("gate-1", "Gate 1 (Main Entrance)", "gate", 0, 100, 300, True, "zone-a"),
        GraphNode("gate-2", "Gate 2 (East)", "gate", 0, 500, 50, True, "zone-c"),
        GraphNode("gate-3", "Gate 3 (West)", "gate", 0, 500, 550, True, "zone-e"),
        GraphNode("gate-4", "Gate 4 (North)", "gate", 0, 900, 150, True, "zone-g"),
        GraphNode("gate-5", "Gate 5 (South)", "gate", 0, 900, 450, True, "zone-h"),
        GraphNode("gate-6", "Gate 6 (VIP)", "gate", 0, 900, 300, True, "zone-i"),
        GraphNode("lobby-main", "Main Lobby", "junction", 0, 200, 300, True, "zone-a"),
        GraphNode("corridor-north", "North Corridor", "junction", 0, 400, 150, True, "zone-b"),
        GraphNode("corridor-south", "South Corridor", "junction", 0, 400, 450, True, "zone-d"),
        GraphNode("corridor-east", "East Corridor", "junction", 0, 700, 300, True, "zone-f"),
        GraphNode("restroom-g1", "Restroom G1 (Ground)", "restroom", 0, 300, 100, True, "zone-b"),
        GraphNode("restroom-g2", "Restroom G2 (Ground)", "restroom", 0, 300, 500, True, "zone-d"),
        GraphNode("food-court-g", "Food Court (Ground)", "food_court", 0, 350, 300, True, "zone-a"),
        GraphNode("medical-g", "Medical Station (Ground)", "medical", 0, 600, 300, True, "zone-f"),
        GraphNode("info-desk", "Information Desk", "info_desk", 0, 250, 300, True, "zone-a"),
        GraphNode("elevator-1-g", "Elevator 1 (Ground)", "elevator", 0, 500, 200, True, "zone-c"),
        GraphNode("elevator-2-g", "Elevator 2 (Ground)", "elevator", 0, 500, 400, True, "zone-e"),
        GraphNode("stairs-1-g", "Stairs 1 (Ground)", "stairs", 0, 450, 150, False, "zone-b"),
        GraphNode("stairs-2-g", "Stairs 2 (Ground)", "stairs", 0, 450, 450, False, "zone-d"),
        GraphNode("ramp-1-g", "Ramp 1 (Ground)", "ramp", 0, 550, 200, True, "zone-c"),
    ]

    # ── Level 1 ──
    nodes_level1 = [
        GraphNode("concourse-1", "Level 1 Concourse", "junction", 1, 400, 300, True, "zone-j"),
        GraphNode("seating-north", "North Stand Seating", "seating", 1, 400, 100, True, "zone-c"),
        GraphNode("seating-south", "South Stand Seating", "seating", 1, 400, 500, True, "zone-e"),
        GraphNode("restroom-l1", "Restroom L1", "restroom", 1, 350, 200, True, "zone-j"),
        GraphNode(
            "food-court-l1", "Food Court (Level 1)", "food_court", 1, 550, 300, True, "zone-j"
        ),
        GraphNode("elevator-1-l1", "Elevator 1 (Level 1)", "elevator", 1, 500, 200, True, "zone-j"),
        GraphNode("elevator-2-l1", "Elevator 2 (Level 1)", "elevator", 1, 500, 400, True, "zone-j"),
        GraphNode("stairs-1-l1", "Stairs 1 (Level 1)", "stairs", 1, 450, 150, False, "zone-j"),
        GraphNode("stairs-2-l1", "Stairs 2 (Level 1)", "stairs", 1, 450, 450, False, "zone-j"),
        GraphNode("ramp-1-l1", "Ramp 1 (Level 1)", "ramp", 1, 550, 200, True, "zone-j"),
    ]

    # ── Level 2 ──
    nodes_level2 = [
        GraphNode("concourse-2", "Level 2 Concourse", "junction", 2, 400, 300, True, "zone-k"),
        GraphNode("vip-lounge", "VIP Lounge", "vip", 2, 600, 300, True, "zone-l"),
        GraphNode("press-box", "Press Box", "press", 2, 700, 200, True, "zone-l"),
        GraphNode("restroom-l2", "Restroom L2", "restroom", 2, 350, 400, True, "zone-k"),
        GraphNode("elevator-1-l2", "Elevator 1 (Level 2)", "elevator", 2, 500, 200, True, "zone-k"),
        GraphNode("elevator-2-l2", "Elevator 2 (Level 2)", "elevator", 2, 500, 400, True, "zone-k"),
    ]

    for node in nodes_ground + nodes_level1 + nodes_level2:
        graph.add_node(node)

    # ── Ground Floor Edges ──
    ground_edges = [
        GraphEdge("gate-1", "lobby-main", 30.0),
        GraphEdge("lobby-main", "info-desk", 15.0),
        GraphEdge("lobby-main", "food-court-g", 50.0),
        GraphEdge("lobby-main", "corridor-north", 80.0),
        GraphEdge("lobby-main", "corridor-south", 80.0),
        GraphEdge("corridor-north", "restroom-g1", 25.0),
        GraphEdge("corridor-north", "gate-2", 60.0),
        GraphEdge("corridor-north", "stairs-1-g", 20.0, AccessibilityType.WALKWAY),
        GraphEdge("corridor-north", "elevator-1-g", 30.0),
        GraphEdge("corridor-north", "ramp-1-g", 35.0),
        GraphEdge("corridor-south", "restroom-g2", 25.0),
        GraphEdge("corridor-south", "gate-3", 60.0),
        GraphEdge("corridor-south", "stairs-2-g", 20.0, AccessibilityType.WALKWAY),
        GraphEdge("corridor-south", "elevator-2-g", 30.0),
        GraphEdge("corridor-north", "corridor-east", 120.0),
        GraphEdge("corridor-south", "corridor-east", 120.0),
        GraphEdge("corridor-east", "medical-g", 30.0),
        GraphEdge("corridor-east", "gate-4", 80.0),
        GraphEdge("corridor-east", "gate-5", 80.0),
        GraphEdge("corridor-east", "gate-6", 40.0),
        GraphEdge("food-court-g", "corridor-north", 60.0),
        GraphEdge("food-court-g", "corridor-south", 60.0),
        # Vertical connections (Ground → Level 1)
        GraphEdge("stairs-1-g", "stairs-1-l1", 15.0, AccessibilityType.STAIRS),
        GraphEdge("stairs-2-g", "stairs-2-l1", 15.0, AccessibilityType.STAIRS),
        GraphEdge("elevator-1-g", "elevator-1-l1", 5.0, AccessibilityType.ELEVATOR),
        GraphEdge("elevator-2-g", "elevator-2-l1", 5.0, AccessibilityType.ELEVATOR),
        GraphEdge("ramp-1-g", "ramp-1-l1", 40.0, AccessibilityType.RAMP),
    ]

    # ── Level 1 Edges ──
    level1_edges = [
        GraphEdge("stairs-1-l1", "concourse-1", 20.0),
        GraphEdge("stairs-2-l1", "concourse-1", 20.0),
        GraphEdge("elevator-1-l1", "concourse-1", 15.0),
        GraphEdge("elevator-2-l1", "concourse-1", 15.0),
        GraphEdge("ramp-1-l1", "concourse-1", 25.0),
        GraphEdge("concourse-1", "seating-north", 60.0),
        GraphEdge("concourse-1", "seating-south", 60.0),
        GraphEdge("concourse-1", "restroom-l1", 30.0),
        GraphEdge("concourse-1", "food-court-l1", 40.0),
        # Vertical connections (Level 1 → Level 2)
        GraphEdge("elevator-1-l1", "elevator-1-l2", 5.0, AccessibilityType.ELEVATOR),
        GraphEdge("elevator-2-l1", "elevator-2-l2", 5.0, AccessibilityType.ELEVATOR),
    ]

    # ── Level 2 Edges ──
    level2_edges = [
        GraphEdge("elevator-1-l2", "concourse-2", 15.0),
        GraphEdge("elevator-2-l2", "concourse-2", 15.0),
        GraphEdge("concourse-2", "vip-lounge", 50.0),
        GraphEdge("concourse-2", "press-box", 70.0),
        GraphEdge("concourse-2", "restroom-l2", 25.0),
    ]

    for edge in ground_edges + level1_edges + level2_edges:
        graph.add_edge(edge)

    return graph


def create_density_evaluator() -> DensityEvaluator:
    """Create and configure the density evaluator with registered zones."""
    evaluator = DensityEvaluator()

    zones = [
        ("zone-a", "Zone A — Main Lobby"),
        ("zone-b", "Zone B — North Concourse"),
        ("zone-c", "Zone C — North Stand"),
        ("zone-d", "Zone D — South Concourse"),
        ("zone-e", "Zone E — South Stand"),
        ("zone-f", "Zone F — East Wing"),
        ("zone-g", "Zone G — North Gates"),
        ("zone-h", "Zone H — South Gates"),
        ("zone-i", "Zone I — VIP Area"),
        ("zone-j", "Zone J — Level 1 Concourse"),
        ("zone-k", "Zone K — Level 2 Concourse"),
        ("zone-l", "Zone L — Press & VIP Level 2"),
    ]

    for zone_id, zone_name in zones:
        evaluator.register_zone(zone_id, zone_name)

    return evaluator


def get_sop_documents() -> list[dict[str, str]]:
    """Return seed SOP documents for RAG retrieval.

    In production, these would be loaded from MongoDB Atlas with $vectorSearch embeddings.
    For the MVP, we provide 12 realistic SOP document chunks.
    """
    return [
        {
            "title": "Crowd Management Protocol",
            "section": "§3.1 — Density Thresholds and Response Levels",
            "content": (
                "The venue operates under a four-tier density management system:\n"
                "- NORMAL (<75%): Standard operations. Regular monitoring every 5 minutes.\n"
                "- WARNING (75-84%): Deploy 2 additional crowd marshals per affected zone. "
                "Open auxiliary circulation routes. Increase monitoring to every 2 minutes.\n"
                "- CRITICAL (85-94%): Activate overflow gates. Restrict new entry to affected zones. "
                "Issue fan advisory via app and PA system. Notify emergency services on standby.\n"
                "- EMERGENCY (≥95%): Initiate controlled evacuation per §4.2. "
                "All staff to designated positions. Emergency services activated."
            ),
        },
        {
            "title": "Crowd Management Protocol",
            "section": "§3.2 — Halftime Egress Management",
            "content": (
                "Halftime presents the highest crowd density risk due to simultaneous movement:\n"
                "- Pre-position 4 additional marshals at main concourse intersections 5 minutes before halftime.\n"
                "- Stagger food court service activation: west wing opens 2 min before halftime, east wing at halftime.\n"
                "- Deploy queue management barriers at restroom zones B and D.\n"
                "- Monitor density surge pattern: expect 15-25% increase in concourse zones within 3 minutes of halftime whistle."
            ),
        },
        {
            "title": "Evacuation Protocol",
            "section": "§4.2 — Controlled Egress Procedure",
            "content": (
                "When evacuation is triggered by control room authorization:\n"
                "Phase 1 (T+0 min): Halt all new entries. PA announcement + app push notification. "
                "All turnstiles switched to exit-only mode.\n"
                "Phase 2 (T+2 min): Open all emergency exits (Gates E1-E8). Deploy all available staff "
                "to guide flow using designated route cards.\n"
                "Phase 3 (T+5 min): Medical teams positioned at assembly points A (north parking), "
                "B (east lawn), C (south plaza). Wheelchair assistance available at all elevator banks.\n"
                "Phase 4 (T+10 min): Emergency services coordination. Head count verification. "
                "Incident documentation initiated for post-event review."
            ),
        },
        {
            "title": "Medical Response Protocol",
            "section": "§2.1 — On-Site Medical Triage",
            "content": (
                "Medical response follows standard triage levels:\n"
                "- Level 1 (Green/Minor): Heat exhaustion, minor cuts, headaches. "
                "Handled at first aid stations in Zones A, F, and J. No escalation needed.\n"
                "- Level 2 (Yellow/Moderate): Suspected fractures, severe dehydration, allergic reactions. "
                "Medical team deployment required. Notify control room. Clear path to nearest first aid station.\n"
                "- Level 3 (Red/Severe): Cardiac events, loss of consciousness, crush injuries. "
                "Emergency services callout immediately. Clear vehicle access route to venue entrance Gate 1. "
                "Control room to coordinate with hospital emergency department."
            ),
        },
        {
            "title": "Weather Contingency Protocol",
            "section": "§5.1 — Adverse Weather Operations",
            "content": (
                "Weather monitoring is continuous via integration with weather API:\n"
                "- Light rain: Open covered concourse areas. Redirect fans from exposed Zones C and E "
                "to covered Zones J and K. Deploy anti-slip mats at all entrances.\n"
                "- Heavy rain/thunderstorm: Suspend outdoor activities. All fans directed to covered areas. "
                "Lightning protocol: no re-entry to open zones until 30 min after last lightning strike.\n"
                "- Extreme heat (>38°C): Activate misting stations in Zones A and F. "
                "Increase water distribution points. Medical teams on high alert for heat-related illness.\n"
                "- Severe weather warning: Follow evacuation protocol §4.2 if conditions warrant."
            ),
        },
        {
            "title": "VIP & Dignitary Protocol",
            "section": "§6.1 — VIP Access and Security",
            "content": (
                "VIP guests enter via Gate 6 (dedicated VIP entrance):\n"
                "- Pre-arrival: Security sweep of VIP Lounge (Level 2) 1 hour before event.\n"
                "- Arrival: Dedicated escort from Gate 6 via Elevator 1 to VIP Lounge. "
                "Avoid public concourse routes.\n"
                "- During event: Dedicated steward assigned per 10 VIP guests. "
                "Separate restroom facilities on Level 2.\n"
                "- Emergency: VIP evacuation via dedicated route (Elevator 1 → Gate 6). "
                "Priority medical response if needed."
            ),
        },
        {
            "title": "Incident Reporting Protocol",
            "section": "§7.1 — Incident Classification and Reporting",
            "content": (
                "All incidents must be reported within 5 minutes of occurrence:\n"
                "- Low severity: Minor disturbance, lost property, general complaint. "
                "Report via volunteer app. Acknowledgement within 15 minutes.\n"
                "- Medium severity: Altercation, suspicious package, minor injury. "
                "Report via volunteer app with photo evidence. Control room acknowledges within 5 minutes. "
                "Deploy nearest available security team.\n"
                "- High severity: Physical violence, weapon sighting, structural damage. "
                "Immediate radio contact with control room. Lock down affected zone. "
                "Emergency services notified automatically.\n"
                "- Critical severity: Active threat, fire, structural collapse. "
                "Immediate evacuation of affected zone per §4.2. All channels activated."
            ),
        },
        {
            "title": "Accessibility Protocol",
            "section": "§8.1 — Accessible Services and Routes",
            "content": (
                "The venue provides full accessibility support:\n"
                "- Wheelchair-accessible routes: All primary paths avoid stairs. "
                "Ramps available between Ground and Level 1. Elevators serve all 3 levels.\n"
                "- Accessible restrooms: Available in Zones B (Ground), J (Level 1), and K (Level 2).\n"
                "- Hearing assistance: Induction loop system in Zones C and E (seating areas).\n"
                "- Visual assistance: Braille signage at all major junctions. "
                "Audio navigation available via the fan app.\n"
                "- Service animals: Welcome in all public areas. Relief areas at Zones A and F.\n"
                "- Wheelchair spaces: Designated viewing areas in Zones C and E with companion seating."
            ),
        },
        {
            "title": "Food and Beverage Operations",
            "section": "§9.1 — Concession Management",
            "content": (
                "Food courts operate in Zones A (Ground) and J (Level 1):\n"
                "- Pre-match: Full service from gates opening. Queue time target: <10 minutes.\n"
                "- Halftime: Peak demand period. All counters operational. "
                "Deploy queue management staff. Mobile vendors circulate in seating zones.\n"
                "- Post-match: Reduced service (50% counters). Close 30 minutes after final whistle.\n"
                "- Allergen management: Clear labeling on all items. "
                "Dedicated allergen-free preparation area in Zone J food court.\n"
                "- Alcohol service: Restricted to designated zones. "
                "Cut-off 30 minutes before end of event. ID verification required."
            ),
        },
        {
            "title": "Communication Protocol",
            "section": "§10.1 — Multi-Channel Communication",
            "content": (
                "Control room communicates via multiple channels:\n"
                "- PA System: Venue-wide and zone-specific announcements. "
                "Scripts pre-approved for common scenarios (delays, weather, emergency).\n"
                "- Fan App: Push notifications for crowd advisories, route changes, "
                "event updates. Supports EN, HI, TA, TE, ES.\n"
                "- Staff Radio: Channel 1 (general), Channel 2 (security), "
                "Channel 3 (medical), Channel 4 (VIP).\n"
                "- Volunteer App: Task assignments, incident reports, AI-generated instructions "
                "in volunteer's preferred language.\n"
                "- External: Emergency services liaison via dedicated phone line."
            ),
        },
        {
            "title": "Historical Incident Database",
            "section": "Match Day Pattern #12 — High-Density Near-Miss",
            "content": (
                "Date: 2024-03-15 | Event: Quarter-Final Match | Attendance: 9,200/10,000\n"
                "Incident: Zone C reached 92% density during halftime egress. "
                "Crowd crush near-miss at North Concourse intersection.\n"
                "Contributing factors: Rain forced fans indoors simultaneously. "
                "Food court queue extended into main corridor. Insufficient marshals deployed.\n"
                "Resolution: Emergency auxiliary gates opened. Crowd redirected to South Concourse. "
                "Density reduced to 78% within 8 minutes.\n"
                "Lessons learned: Pre-position additional marshals for wet weather events. "
                "Stagger food court opening. Install real-time density monitoring in all concourse zones.\n"
                "Follow-up actions: Density monitoring system deployed (current system). "
                "Wet weather SOP updated (§5.1). Staffing model revised for high-attendance events."
            ),
        },
        {
            "title": "Post-Event Operations",
            "section": "§11.1 — Controlled Venue Clearing",
            "content": (
                "Post-event clearing follows a phased approach:\n"
                "- Phase 1 (T+0): Open all exit gates. PA announcement of exit routes. "
                "Deploy all marshals to guide flow.\n"
                "- Phase 2 (T+5): Zone-by-zone clearing starting from upper levels. "
                "Elevator priority for wheelchair users and elderly.\n"
                "- Phase 3 (T+15): Sweep of all zones for remaining attendees. "
                "Lost property collection.\n"
                "- Phase 4 (T+30): Final security sweep. Venue handover to cleaning crew.\n"
                "Target: Full venue clear within 30 minutes for events <8,000. "
                "45 minutes for events >8,000."
            ),
        },
    ]


async def seed_mongodb(db: Any) -> None:
    """Automatically seed MongoDB Atlas with demo users, venue layout, and SOP documents.

    Only inserts if the respective collections are empty, preventing duplicate data.
    Provides instant out-of-the-box readiness for testing and demonstration.
    """
    import logging
    from datetime import datetime
    from uuid import uuid4

    from app.core.auth import hash_password

    logger = logging.getLogger(__name__)

    try:
        # 1. Seed Demo Users
        if await db.users.count_documents({}) == 0:
            now = datetime.now(UTC)
            demo_users = [
                {
                    "id": "user-admin-demo",
                    "email": "admin@sentinelarena.com",
                    "hashed_password": hash_password("SentinelAdmin2026!"),
                    "display_name": "Demo Administrator",
                    "role": "admin",
                    "locale": "en",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": "user-organizer-demo",
                    "email": "organizer@sentinelarena.com",
                    "hashed_password": hash_password("SentinelOrg2026!"),
                    "display_name": "Lead Organizer",
                    "role": "organizer",
                    "locale": "en",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": "user-volunteer-demo",
                    "email": "volunteer@sentinelarena.com",
                    "hashed_password": hash_password("SentinelVol2026!"),
                    "display_name": "Field Volunteer",
                    "role": "volunteer",
                    "locale": "es",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": "user-fan-demo",
                    "email": "fan@sentinelarena.com",
                    "hashed_password": hash_password("SentinelFan2026!"),
                    "display_name": "Stadium Fan",
                    "role": "fan",
                    "locale": "en",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
            ]
            await db.users.insert_many(demo_users)
            logger.info("Seeded 4 demo users into MongoDB Atlas")

        # 2. Seed Venue
        if await db.venues.count_documents({}) == 0:
            venue_doc = {
                "id": "venue-demo",
                "name": "SentinelArena Stadium",
                "description": "Smart Stadium & Tournament Operations Platform Demo Environment",
                "total_capacity": 10000,
                "address": "100 Stadium Way, Tech City",
                "created_at": datetime.now(UTC),
            }
            await db.venues.insert_one(venue_doc)
            logger.info("Seeded demo venue into MongoDB Atlas")

        # 3. Seed Zones
        if await db.zones.count_documents({}) == 0:
            zones_data = [
                {
                    "id": "zone-a",
                    "venue_id": "venue-demo",
                    "code": "A",
                    "name": "Zone A — Main Lobby",
                    "capacity": 1000,
                    "floor_level": 0,
                },
                {
                    "id": "zone-b",
                    "venue_id": "venue-demo",
                    "code": "B",
                    "name": "Zone B — North Concourse",
                    "capacity": 800,
                    "floor_level": 0,
                },
                {
                    "id": "zone-c",
                    "venue_id": "venue-demo",
                    "code": "C",
                    "name": "Zone C — North Stand",
                    "capacity": 2000,
                    "floor_level": 1,
                },
                {
                    "id": "zone-d",
                    "venue_id": "venue-demo",
                    "code": "D",
                    "name": "Zone D — South Concourse",
                    "capacity": 800,
                    "floor_level": 0,
                },
                {
                    "id": "zone-e",
                    "venue_id": "venue-demo",
                    "code": "E",
                    "name": "Zone E — South Stand",
                    "capacity": 2000,
                    "floor_level": 1,
                },
                {
                    "id": "zone-f",
                    "venue_id": "venue-demo",
                    "code": "F",
                    "name": "Zone F — East Wing",
                    "capacity": 600,
                    "floor_level": 0,
                },
                {
                    "id": "zone-g",
                    "venue_id": "venue-demo",
                    "code": "G",
                    "name": "Zone G — North Gates",
                    "capacity": 500,
                    "floor_level": 0,
                },
                {
                    "id": "zone-h",
                    "venue_id": "venue-demo",
                    "code": "H",
                    "name": "Zone H — South Gates",
                    "capacity": 500,
                    "floor_level": 0,
                },
                {
                    "id": "zone-i",
                    "venue_id": "venue-demo",
                    "code": "I",
                    "name": "Zone I — VIP Area",
                    "capacity": 300,
                    "floor_level": 0,
                },
                {
                    "id": "zone-j",
                    "venue_id": "venue-demo",
                    "code": "J",
                    "name": "Zone J — Level 1 Concourse",
                    "capacity": 800,
                    "floor_level": 1,
                },
                {
                    "id": "zone-k",
                    "venue_id": "venue-demo",
                    "code": "K",
                    "name": "Zone K — Level 2 Concourse",
                    "capacity": 500,
                    "floor_level": 2,
                },
                {
                    "id": "zone-l",
                    "venue_id": "venue-demo",
                    "code": "L",
                    "name": "Zone L — Press & VIP Level 2",
                    "capacity": 200,
                    "floor_level": 2,
                },
            ]
            await db.zones.insert_many(zones_data)
            logger.info("Seeded 12 stadium zones into MongoDB Atlas")

        # 4. Seed SOP Documents (RAG Knowledge Base)
        if await db.sop_documents.count_documents({}) == 0:
            sop_docs = [
                {
                    "id": str(uuid4()),
                    "venue_id": "venue-demo",
                    "title": doc["title"],
                    "section": doc["section"],
                    "content": doc["content"],
                    "created_at": datetime.now(UTC),
                }
                for doc in get_sop_documents()
            ]
            await db.sop_documents.insert_many(sop_docs)
            logger.info("Seeded %d SOP documents into MongoDB Atlas", len(sop_docs))

        # 5. Seed POIs & Edges (Navigation Graph)
        if await db.pois.count_documents({}) == 0:
            graph = create_venue_graph()
            pois = [
                {
                    "id": node.id,
                    "venue_id": "venue-demo",
                    "zone_id": node.zone_id,
                    "name": node.name,
                    "poi_type": node.poi_type,
                    "floor_level": node.floor_level,
                    "x_coord": node.x,
                    "y_coord": node.y,
                    "is_accessible": node.is_accessible,
                }
                for node in graph.get_all_nodes()
            ]
            if pois:
                await db.pois.insert_many(pois)
                logger.info("Seeded %d POIs into MongoDB Atlas", len(pois))

        if await db.edges.count_documents({}) == 0:
            graph = create_venue_graph()
            edges = [
                {
                    "id": str(uuid4()),
                    "venue_id": "venue-demo",
                    "from_poi_id": edge.from_node_id,
                    "to_poi_id": edge.to_node_id,
                    "distance_meters": edge.distance_meters,
                    "accessibility": edge.accessibility.value,
                    "is_bidirectional": edge.is_bidirectional,
                    "congestion_weight": edge.congestion_weight,
                }
                for edge in graph.get_all_edges()
            ]
            if edges:
                await db.edges.insert_many(edges)
                logger.info("Seeded %d navigation edges into MongoDB Atlas", len(edges))

    except Exception as exc:
        logger.warning("Error seeding MongoDB Atlas: %s", exc)

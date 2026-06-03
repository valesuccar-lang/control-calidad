"""seed masters data — 25 defects, initial machines and fabrics

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02
"""
from alembic import op
from datetime import datetime

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

DEFECTS = [
    ("D-001", "Rasgadura", "STRUCTURAL", "HIGH"),
    ("D-002", "Mancha de aceite", "APPEARANCE", "HIGH"),
    ("D-003", "Variación de color", "APPEARANCE", "MEDIUM"),
    ("D-004", "Error de tejido", "STRUCTURAL", "HIGH"),
    ("D-005", "Encogimiento", "DIMENSIONAL", "MEDIUM"),
    ("D-006", "Hilo suelto", "STRUCTURAL", "LOW"),
    ("D-007", "Agujero", "STRUCTURAL", "CRITICAL"),
    ("D-008", "Mancha de tinta", "APPEARANCE", "HIGH"),
    ("D-009", "Deformación", "DIMENSIONAL", "MEDIUM"),
    ("D-010", "Pelusa excesiva", "APPEARANCE", "LOW"),
    ("D-011", "Costura irregular", "STRUCTURAL", "MEDIUM"),
    ("D-012", "Destiñe", "APPEARANCE", "HIGH"),
    ("D-013", "Trama descorrida", "STRUCTURAL", "HIGH"),
    ("D-014", "Marca de pliegue", "APPEARANCE", "LOW"),
    ("D-015", "Resistencia baja", "STRUCTURAL", "CRITICAL"),
    ("D-016", "Textura irregular", "APPEARANCE", "MEDIUM"),
    ("D-017", "Burbujas", "APPEARANCE", "MEDIUM"),
    ("D-018", "Deshilachado", "STRUCTURAL", "LOW"),
    ("D-019", "Nudo visible", "APPEARANCE", "LOW"),
    ("D-020", "Elongación excesiva", "DIMENSIONAL", "MEDIUM"),
    ("D-021", "Diferencia de peso", "DIMENSIONAL", "HIGH"),
    ("D-022", "Error de orillo", "STRUCTURAL", "MEDIUM"),
    ("D-023", "Contaminación", "APPEARANCE", "HIGH"),
    ("D-024", "Brillo irregular", "APPEARANCE", "LOW"),
    ("D-025", "Ancho fuera de spec", "DIMENSIONAL", "HIGH"),
]


def upgrade() -> None:
    now = datetime.utcnow()
    conn = op.get_bind()
    for defect_id, name, category, severity in DEFECTS:
        conn.execute(
            "INSERT INTO defects (defect_id, name, category, severity, status, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, 'ACTIVE', %s, %s) "
            "ON CONFLICT (defect_id) DO NOTHING",
            (defect_id, name, category, severity, now, now),
        )

    machines = [
        ("M-001", "Tejedora Rapier A", "Sulzer G6300"),
        ("M-002", "Tejedora Rapier B", "Sulzer G6300"),
        ("M-003", "Tejedora Circular 1", "Mayer&Cie E3.2"),
        ("M-004", "Tejedora Circular 2", "Mayer&Cie E3.2"),
        ("M-005", "Tundidora 1", "Lafer TX50"),
    ]
    for machine_id, name, model in machines:
        conn.execute(
            "INSERT INTO machines (machine_id, name, model, status, created_at, updated_at) "
            "VALUES (%s, %s, %s, 'ACTIVE', %s, %s) ON CONFLICT DO NOTHING",
            (machine_id, name, model, now, now),
        )


def downgrade() -> None:
    op.execute("DELETE FROM defects WHERE defect_id LIKE 'D-0%'")
    op.execute("DELETE FROM machines WHERE machine_id LIKE 'M-0%'")

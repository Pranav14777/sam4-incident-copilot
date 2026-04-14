import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "sam4.db")


def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        DELETE FROM maintenance_history;
        DELETE FROM incidents;
        DELETE FROM assets;
    """)

    # Real SAM4-style assets with full passport data
    assets = [
        (1, "Booster Pump 1", "Pump", "Water Supply - Zone A", "Water Treatment Plant Noord", "Water", "critical", "2018-03-15", 1200.0, 120.0, 400.0, 211.0, 1482, 0.92, "Coupling"),
        (2, "Booster Pump 2", "Pump", "Water Supply - Zone B", "Water Treatment Plant Noord", "Water", "high", "2019-07-22", 950.0, 275.0, 400.0, 485.0, 1480, 0.88, "Coupling"),
        (3, "Feed Pump 3", "Pump", "Chemical Dosing Unit", "Chemical Processing Plant Oost", "Chemical", "high", "2020-01-10", 800.0, 315.0, 690.0, 290.0, 2970, 0.91, "Direct Drive"),
        (4, "Cooling Water Pump 1", "Pump", "Cooling Circuit Line 1", "Chemical Processing Plant Oost", "Chemical", "medium", "2021-05-20", 600.0, 75.0, 400.0, 142.0, 1475, 0.85, "Coupling"),
        (5, "Slurry Pump A", "Pump", "Ore Processing Line 2", "Mining Site Limburg", "Mining", "critical", "2017-11-05", 1800.0, 315.0, 690.0, 310.0, 1485, 0.79, "Coupling"),
        (6, "Drive Motor 7", "Motor", "Conveyor Belt Unit 3", "Mining Site Limburg", "Mining", "high", "2019-03-12", 1400.0, 160.0, 400.0, 298.0, 1480, 0.93, "Direct Drive"),
    ]
    cursor.executemany("""
        INSERT INTO assets (id, name, asset_type, location, site, industry,
        criticality, install_date, downtime_cost_per_hour,
        rated_power_kw, voltage_v, current_a, rpm, efficiency, transmission_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, assets)

    # Real SAM4-style incidents with accurate ESA indicators and failure modes
    incidents = [
        (1, 1, "Booster Pump 1", "Requires Immediate Action", "Current unbalance > 10%", "Stator winding fault", "critical", "Water Treatment Plant Noord", "2024-11-16 08:23:00", "open"),
        (2, 2, "Booster Pump 2", "Requires Action", "Rotor bar harmonics elevated", "Broken rotor bar", "warning", "Water Treatment Plant Noord", "2024-11-14 14:10:00", "open"),
        (3, 3, "Feed Pump 3", "Requires Immediate Action", "Current unbalance > 15%", "Stator winding fault", "critical", "Chemical Processing Plant Oost", "2024-11-13 09:45:00", "open"),
        (4, 4, "Cooling Water Pump 1", "Requires Monitoring", "Bearing frequency signature", "Bearing wear - outer race", "warning", "Chemical Processing Plant Oost", "2024-11-12 07:15:00", "open"),
        (5, 5, "Slurry Pump A", "Requires Immediate Action", "Current unbalance > 12%", "Rotor eccentricity fault", "critical", "Mining Site Limburg", "2024-11-10 07:30:00", "triaged"),
        (6, 6, "Drive Motor 7", "Requires Action", "Shaft frequency harmonics", "Shaft misalignment", "warning", "Mining Site Limburg", "2024-11-09 11:20:00", "open"),
        (7, 1, "Booster Pump 1", "Requires Action", "Current unbalance > 8%", "Stator winding fault - early stage", "warning", "Water Treatment Plant Noord", "2024-11-04 10:00:00", "resolved"),
        (8, 5, "Slurry Pump A", "Requires Immediate Action", "Current unbalance > 18%", "Coupling fault", "critical", "Mining Site Limburg", "2024-09-15 06:00:00", "resolved"),
    ]
    cursor.executemany("""
        INSERT INTO incidents (id, asset_id, asset_name, health_status, indicator,
        failure_mode, severity, location, detected_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, incidents)

    # Realistic maintenance history matching SAM4 domains
    maintenance = [
        (1, 1, "Corrective", "Inspected MCC cable connections after current unbalance alert. Found loose terminal on phase 2. Re-torqued and tested.", "2024-11-04 15:00:00", "TechTeam-Noord"),
        (2, 1, "Preventive", "Routine megger test and insulation resistance check. All phases within spec.", "2024-08-10 09:00:00", "TechTeam-Noord"),
        (3, 2, "Preventive", "Vibration analysis and lubrication of drive-end bearing. No anomalies detected.", "2024-09-01 10:00:00", "TechTeam-Noord"),
        (4, 3, "Corrective", "Emergency shutdown following phase imbalance alarm. Replaced stator winding on phase 3.", "2024-07-18 14:00:00", "TechTeam-Oost"),
        (5, 4, "Preventive", "Bearing inspection and grease replenishment. Outer race showing early wear pattern — flagged for monitoring.", "2024-10-05 08:30:00", "TechTeam-Oost"),
        (6, 5, "Corrective", "Emergency coupling replacement after mechanical failure. Full alignment check performed.", "2024-09-16 07:00:00", "TechTeam-Limburg"),
        (7, 5, "Preventive", "Full pump overhaul. Impeller replaced, shaft run-out measured and corrected.", "2024-06-30 09:00:00", "TechTeam-Limburg"),
        (8, 6, "Preventive", "Shaft alignment check using laser alignment tool. Minor misalignment corrected.", "2024-10-20 11:00:00", "TechTeam-Limburg"),
    ]
    cursor.executemany("""
        INSERT INTO maintenance_history (id, asset_id, maintenance_type, description, performed_at, performed_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, maintenance)

    conn.commit()
    conn.close()
    print("Database seeded successfully.")


if __name__ == "__main__":
    seed()
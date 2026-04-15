import math
import matplotlib.pyplot as plt
import streamlit as st

G0 = 9.81
LEO_VELOCITY = 7800
ESCAPE_VELOCITY = 11200


def ideal_stage_delta_v(isp, m0, mf):
    return isp * G0 * math.log(m0 / mf)


def calculate_ideal_multistage(stages, payload_mass, gravity_loss=1500, drag_loss=200):
    total_delta_v = 0.0
    stage_results = []

    current_total_mass = payload_mass + sum(
        stage["dry_mass"] + stage["fuel_mass"] for stage in stages
    )

    for stage in stages:
        m0 = current_total_mass
        mf = m0 - stage["fuel_mass"]
        dv = ideal_stage_delta_v(stage["isp"], m0, mf)
        total_delta_v += dv

        stage_results.append({
            "name": stage["name"],
            "m0": m0,
            "mf": mf,
            "isp": stage["isp"],
            "delta_v": dv,
        })

        current_total_mass = mf - stage["dry_mass"]

    total_losses = gravity_loss + drag_loss
    net_delta_v = total_delta_v - total_losses
    return stage_results, total_delta_v, total_losses, net_delta_v


def air_density(height):
    rho0 = 1.225
    h_scale = 8500
    return rho0 * math.exp(-height / h_scale)


def drag_force(rho, cd, area, velocity):
    return 0.5 * rho * cd * area * velocity**2


def orbit_check(final_velocity):
    if final_velocity >= ESCAPE_VELOCITY:
        return "Escape velocity reached"
    if final_velocity >= LEO_VELOCITY:
        return "Low Earth Orbit achievable"
    return "Not enough velocity for orbit"


def simulate_with_drag(stages, payload_mass, dt=0.1, cd=1.5, area=60.0):
    time = 0.0
    velocity = 0.0
    height = 0.0

    total_mass = payload_mass + sum(
        stage["dry_mass"] + stage["fuel_mass"] for stage in stages
    )

    times = [time]
    velocities = [velocity]
    heights = [height]
    drags = [0.0]
    stage_time_ranges = []

    for stage in stages:
        fuel_mass = stage["fuel_mass"]
        thrust = stage["thrust"]
        burn_rate = stage["burn_rate"]
        dry_mass = stage["dry_mass"]
        name = stage["name"]

        burn_time = fuel_mass / burn_rate
        elapsed = 0.0
        stage_start = time

        while elapsed < burn_time:
            step = min(dt, burn_time - elapsed)

            total_mass -= burn_rate * step

            rho = air_density(height)
            fd = drag_force(rho, cd, area, velocity)
            acceleration = (thrust - fd) / total_mass - G0

            velocity += acceleration * step
            height += velocity * step

            if height < 0:
                height = 0

            time += step
            elapsed += step

            times.append(time)
            velocities.append(velocity)
            heights.append(height)
            drags.append(fd)

        stage_time_ranges.append((name, stage_start, time))
        total_mass -= dry_mass

    return {
        "times": times,
        "velocities": velocities,
        "heights": heights,
        "drags": drags,
        "final_velocity": velocity,
        "final_height": height,
        "stage_time_ranges": stage_time_ranges,
    }


def simulate_no_drag(stages, payload_mass, dt=0.1):
    time = 0.0
    velocity = 0.0
    height = 0.0

    total_mass = payload_mass + sum(
        stage["dry_mass"] + stage["fuel_mass"] for stage in stages
    )

    times = [time]
    velocities = [velocity]
    heights = [height]

    for stage in stages:
        fuel_mass = stage["fuel_mass"]
        thrust = stage["thrust"]
        burn_rate = stage["burn_rate"]
        dry_mass = stage["dry_mass"]

        burn_time = fuel_mass / burn_rate
        elapsed = 0.0

        while elapsed < burn_time:
            step = min(dt, burn_time - elapsed)

            total_mass -= burn_rate * step
            acceleration = (thrust / total_mass) - G0

            velocity += acceleration * step
            height += velocity * step

            time += step
            elapsed += step

            times.append(time)
            velocities.append(velocity)
            heights.append(height)

        total_mass -= dry_mass

    return {
        "times": times,
        "velocities": velocities,
        "heights": heights,
        "final_velocity": velocity,
        "final_height": height,
    }


def run_payload_sensitivity(stages, payload_values, dt, cd, area):
    results = []
    for payload in payload_values:
        sim = simulate_with_drag(stages, payload, dt=dt, cd=cd, area=area)
        results.append({
            "payload": payload,
            "final_velocity": sim["final_velocity"],
            "final_height": sim["final_height"],
        })
    return results


def plot_delta_v(stage_results, total_losses, net_delta_v):
    labels = [s["name"] for s in stage_results] + ["Losses", "Net Delta-V"]
    values = [s["delta_v"] for s in stage_results] + [-total_losses, net_delta_v]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, values)
    ax.axhline(0)
    ax.set_title("Multi-Stage Rocket Delta-V Analysis")
    ax.set_xlabel("Stages")
    ax.set_ylabel("Delta-V (m/s)")

    for bar in bars:
        value = bar.get_height()
        x = bar.get_x() + bar.get_width() / 2
        if value >= 0:
            ax.text(x, value + 100, f"{value:.0f}", ha="center", va="bottom")
        else:
            ax.text(x, value - 100, f"{value:.0f}", ha="center", va="top")

    fig.tight_layout()
    return fig


def plot_velocity_comparison(sim_no_drag, sim_drag):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sim_no_drag["times"], sim_no_drag["velocities"], label="No Drag", linewidth=2)
    ax.plot(sim_drag["times"], sim_drag["velocities"], linestyle="--", label="With Drag", linewidth=2)
    ax.set_title("Velocity Comparison")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Velocity (m/s)")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    return fig


def plot_height_comparison(sim_no_drag, sim_drag):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sim_no_drag["times"], sim_no_drag["heights"], label="No Drag", linewidth=2)
    ax.plot(sim_drag["times"], sim_drag["heights"], linestyle="--", label="With Drag", linewidth=2)
    ax.set_title("Height Comparison")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Height (m)")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    return fig


def plot_drag_graph(sim_drag):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sim_drag["times"], sim_drag["drags"])
    ax.set_title("Drag Force vs Time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Drag Force (N)")
    ax.grid(True)
    fig.tight_layout()
    return fig


def plot_payload_graphs(results):
    payloads = [r["payload"] for r in results]
    velocities = [r["final_velocity"] for r in results]
    heights = [r["final_height"] for r in results]

    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(payloads, velocities, marker="o")
    ax1.set_title("Payload Mass vs Final Velocity")
    ax1.set_xlabel("Payload Mass (kg)")
    ax1.set_ylabel("Final Velocity (m/s)")
    ax1.grid(True)
    fig1.tight_layout()

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.plot(payloads, heights, marker="o")
    ax2.set_title("Payload Mass vs Final Height")
    ax2.set_xlabel("Payload Mass (kg)")
    ax2.set_ylabel("Final Height (m)")
    ax2.grid(True)
    fig2.tight_layout()

    return fig1, fig2


st.set_page_config(page_title="Rocket Simulation Prototype", layout="wide")
st.title("Multi-Stage Rocket Simulation Prototype")
st.write("Interactive simulation of rocket performance under ideal and drag conditions.")

stages = [
    {"name": "Stage 1", "dry_mass": 30000, "fuel_mass": 400000, "isp": 300, "thrust": 7_600_000, "burn_rate": 2500},
    {"name": "Stage 2", "dry_mass": 8000, "fuel_mass": 100000, "isp": 340, "thrust": 1_000_000, "burn_rate": 600},
    {"name": "Stage 3", "dry_mass": 2000, "fuel_mass": 20000, "isp": 360, "thrust": 250_000, "burn_rate": 120},
]

with st.sidebar:
    st.header("Parameters")
    payload_mass = st.slider("Payload Mass (kg)", 1000, 15000, 5000, 500)
    cd = st.slider("Drag Coefficient (Cd)", 0.1, 2.0, 1.5, 0.1)
    area = st.slider("Cross-Sectional Area (m²)", 5.0, 80.0, 60.0, 5.0)
    dt = st.slider("Time Step", 0.05, 0.5, 0.1, 0.05)

stage_results, total_delta_v, total_losses, net_delta_v = calculate_ideal_multistage(stages, payload_mass)
sim_drag = simulate_with_drag(stages, payload_mass, dt=dt, cd=cd, area=area)
sim_no_drag = simulate_no_drag(stages, payload_mass, dt=dt)

c1, c2, c3 = st.columns(3)
c1.metric("Final Velocity", f"{sim_drag['final_velocity']:.2f} m/s")
c2.metric("Final Height", f"{sim_drag['final_height']:.2f} m")
c3.metric("Orbit Check", orbit_check(sim_drag["final_velocity"]))

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Delta-V Analysis",
    "Velocity Comparison",
    "Height Comparison",
    "Drag Analysis",
    "Payload Sensitivity",
])

with tab1:
    st.pyplot(plot_delta_v(stage_results, total_losses, net_delta_v))

with tab2:
    st.pyplot(plot_velocity_comparison(sim_no_drag, sim_drag))

with tab3:
    st.pyplot(plot_height_comparison(sim_no_drag, sim_drag))

with tab4:
    st.pyplot(plot_drag_graph(sim_drag))
    st.write("Drag is strongest at low altitude and decreases as air density drops.")

with tab5:
    sensitivity_results = run_payload_sensitivity(
        stages,
        payload_values=[2000, 5000, 10000],
        dt=dt,
        cd=cd,
        area=area,
    )
    fig_v, fig_h = plot_payload_graphs(sensitivity_results)
    st.pyplot(fig_v)
    st.pyplot(fig_h)

st.subheader("Model Limitations")
st.write("""
- Vertical flight only  
- Constant thrust  
- Simplified atmosphere model  
- No pitch maneuver or orbital insertion mechanics
""")
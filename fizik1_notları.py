import math
import matplotlib.pyplot as plt

G0 = 9.81  # m/s^2
LEO_VELOCITY = 7800      # Approx. orbital velocity for Low Earth Orbit (m/s)
ESCAPE_VELOCITY = 11200  # Escape velocity from Earth (m/s)


def ideal_stage_delta_v(isp, m0, mf):
    return isp * G0 * math.log(m0 / mf)


def calculate_ideal_multistage(stages, payload_mass, gravity_loss=1500, drag_loss=200):
    total_delta_v = 0.0
    stage_results = []

    current_total_mass = payload_mass + sum(
        stage["dry_mass"] + stage["fuel_mass"] for stage in stages
    )

    for stage in stages:
        name = stage["name"]
        dry_mass = stage["dry_mass"]
        fuel_mass = stage["fuel_mass"]
        isp = stage["isp"]

        m0 = current_total_mass
        mf = m0 - fuel_mass

        dv = ideal_stage_delta_v(isp, m0, mf)
        total_delta_v += dv

        stage_results.append({
            "name": name,
            "m0": m0,
            "mf": mf,
            "isp": isp,
            "delta_v": dv,
        })

        current_total_mass = mf - dry_mass

    total_losses = gravity_loss + drag_loss
    net_delta_v = total_delta_v - total_losses

    return stage_results, total_delta_v, total_losses, net_delta_v


def air_density(height):
    rho0 = 1.225
    h_scale = 8500
    return rho0 * math.exp(-height / h_scale)


def drag_force(rho, cd, area, velocity):
    return 0.5 * rho * cd * area * velocity**2


def simulate_multistage_rocket_with_drag(stages, payload_mass, dt=0.1, cd=1.5, area=60.0):
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
    accelerations = [0.0]

    stage_time_ranges = []
    stage_sim_results = []

    for stage in stages:
        name = stage["name"]
        dry_mass = stage["dry_mass"]
        fuel_mass = stage["fuel_mass"]
        thrust = stage["thrust"]
        burn_rate = stage["burn_rate"]

        burn_time = fuel_mass / burn_rate
        elapsed = 0.0
        stage_start = time

        start_velocity = velocity
        start_height = height

        while elapsed < burn_time:
            step = min(dt, burn_time - elapsed)

            burned_fuel = burn_rate * step
            total_mass -= burned_fuel

            rho = air_density(height)
            fd = drag_force(rho, cd, area, velocity)

            acceleration = (thrust - fd) / total_mass - G0

            velocity += acceleration * step
            height += velocity * step
            time += step
            elapsed += step

            if height < 0:
                height = 0

            times.append(time)
            velocities.append(velocity)
            heights.append(height)
            drags.append(fd)
            accelerations.append(acceleration)

        stage_end = time
        stage_time_ranges.append((name, stage_start, stage_end))

        stage_sim_results.append({
            "name": name,
            "burn_time": burn_time,
            "start_velocity": start_velocity,
            "end_velocity": velocity,
            "start_height": start_height,
            "end_height": height,
        })

        total_mass -= dry_mass

    return {
        "times": times,
        "velocities": velocities,
        "heights": heights,
        "drags": drags,
        "accelerations": accelerations,
        "stage_time_ranges": stage_time_ranges,
        "stage_sim_results": stage_sim_results,
        "final_velocity": velocity,
        "final_height": height,
        "final_mass": total_mass,
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

    return times, velocities, heights


def orbit_check(final_velocity):
    if final_velocity >= ESCAPE_VELOCITY:
        return "Escape velocity reached."
    elif final_velocity >= LEO_VELOCITY:
        return "Low Earth Orbit velocity achievable."
    else:
        return "Not enough velocity for orbit."


def annotate_bars(ax, bars):
    for bar in bars:
        value = bar.get_height()
        x = bar.get_x() + bar.get_width() / 2

        if value >= 0:
            ax.text(x, value + 100, f"{value:.0f}", ha="center", va="bottom", fontsize=9)
        else:
            ax.text(x, value - 100, f"{value:.0f}", ha="center", va="top", fontsize=9)


def plot_delta_v(stage_results, total_losses, net_delta_v):
    labels = [stage["name"] for stage in stage_results] + ["Losses", "Net Delta-V"]
    values = [stage["delta_v"] for stage in stage_results] + [-total_losses, net_delta_v]

    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    bars = ax.bar(labels, values)

    ax.axhline(0)
    ax.set_title("Multi-Stage Rocket Delta-V Analysis")
    ax.set_xlabel("Stages")
    ax.set_ylabel("Delta-V (m/s)")
    annotate_bars(ax, bars)

    plt.tight_layout()
    plt.savefig("delta_v_graph.png", dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def plot_velocity_time(times, velocities, stage_time_ranges, title, filename):
    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    ax.plot(times, velocities)

    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Velocity (m/s)")

    ymax = max(velocities)
    for name, start_t, end_t in stage_time_ranges:
        ax.axvline(end_t, linestyle="--")
        mid = (start_t + end_t) / 2
        ax.text(mid, ymax * 0.95, name, ha="center", va="top", fontsize=9)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def plot_height_time(times, heights, stage_time_ranges, title, filename):
    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    ax.plot(times, heights)

    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Height (m)")

    ymax = max(heights)
    for name, start_t, end_t in stage_time_ranges:
        ax.axvline(end_t, linestyle="--")
        mid = (start_t + end_t) / 2
        ax.text(mid, ymax * 0.95, name, ha="center", va="top", fontsize=9)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def plot_drag_time(times, drags, stage_time_ranges):
    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    ax.plot(times, drags)

    ax.set_title("Drag Force vs Time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Drag Force (N)")

    ymax = max(drags)
    for name, start_t, end_t in stage_time_ranges:
        ax.axvline(end_t, linestyle="--")
        mid = (start_t + end_t) / 2
        ax.text(mid, ymax * 0.95 if ymax > 0 else 1, name, ha="center", va="top", fontsize=9)

    plt.tight_layout()
    plt.savefig("drag_force_graph.png", dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def plot_velocity_comparison(times1, vel1, times2, vel2):
    plt.figure(figsize=(10, 6))
    plt.plot(times1, vel1, label="No Drag", linewidth=2)
    plt.plot(times2, vel2, linestyle="--", label="With Drag", linewidth=2)

    plt.title("Velocity Comparison (Drag vs No Drag)")
    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (m/s)")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("comparison_velocity.png", dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def plot_height_comparison(times1, h1, times2, h2):
    plt.figure(figsize=(10, 6))
    plt.plot(times1, h1, label="No Drag", linewidth=2)
    plt.plot(times2, h2, linestyle="--", label="With Drag", linewidth=2)

    plt.title("Height Comparison (Drag vs No Drag)")
    plt.xlabel("Time (s)")
    plt.ylabel("Height (m)")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("comparison_height.png", dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def run_payload_sensitivity_analysis(stages, payload_values, dt=0.1, cd=1.5, area=60.0):
    results = []

    for payload in payload_values:
        sim = simulate_multistage_rocket_with_drag(
            stages,
            payload,
            dt=dt,
            cd=cd,
            area=area
        )

        results.append({
            "payload": payload,
            "final_velocity": sim["final_velocity"],
            "final_height": sim["final_height"]
        })

    return results


def plot_payload_sensitivity(results):
    payloads = [r["payload"] for r in results]
    velocities = [r["final_velocity"] for r in results]
    heights = [r["final_height"] for r in results]

    plt.figure(figsize=(10, 6))
    plt.plot(payloads, velocities, marker="o")
    plt.title("Payload Mass vs Final Velocity")
    plt.xlabel("Payload Mass (kg)")
    plt.ylabel("Final Velocity (m/s)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("payload_vs_velocity.png", dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(payloads, heights, marker="o")
    plt.title("Payload Mass vs Final Height")
    plt.xlabel("Payload Mass (kg)")
    plt.ylabel("Final Height (m)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("payload_vs_height.png", dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def print_ideal_results(stage_results, total_delta_v, total_losses, net_delta_v):
    print("=== IDEAL DELTA-V ANALYSIS ===")
    for stage in stage_results:
        print(f"{stage['name']}:")
        print(f"  Initial mass (m0): {stage['m0']:.2f} kg")
        print(f"  Final mass (mf):   {stage['mf']:.2f} kg")
        print(f"  Isp:               {stage['isp']} s")
        print(f"  Delta-V:           {stage['delta_v']:.2f} m/s")
        print()

    print(f"Total ideal Delta-V: {total_delta_v:.2f} m/s")
    print(f"Total losses:        {total_losses:.2f} m/s")
    print(f"Net Delta-V:         {net_delta_v:.2f} m/s")
    print()


def print_drag_simulation_results(sim):
    print("=== TIME-BASED FLIGHT SIMULATION WITH DRAG ===")
    for stage_info in sim["stage_sim_results"]:
        print(f"{stage_info['name']}:")
        print(f"  Burn time:         {stage_info['burn_time']:.2f} s")
        print(f"  Start velocity:    {stage_info['start_velocity']:.2f} m/s")
        print(f"  End velocity:      {stage_info['end_velocity']:.2f} m/s")
        print(f"  Start height:      {stage_info['start_height']:.2f} m")
        print(f"  End height:        {stage_info['end_height']:.2f} m")
        print()

    print(f"Final simulated velocity: {sim['final_velocity']:.2f} m/s")
    print(f"Final simulated height:   {sim['final_height']:.2f} m")
    print(f"Final mass after staging: {sim['final_mass']:.2f} kg")
    print(f"Orbit check:             {orbit_check(sim['final_velocity'])}")
    print()


def print_payload_sensitivity_results(results):
    print("=== PAYLOAD SENSITIVITY ANALYSIS ===")
    for r in results:
        print(f"Payload: {r['payload']} kg")
        print(f"  Final velocity: {r['final_velocity']:.2f} m/s")
        print(f"  Final height:   {r['final_height']:.2f} m")
        print(f"  Orbit check:    {orbit_check(r['final_velocity'])}")
        print()


def main():
    stages = [
        {
            "name": "Stage 1",
            "dry_mass": 30000,
            "fuel_mass": 400000,
            "isp": 300,
            "thrust": 7_600_000,
            "burn_rate": 2500,
        },
        {
            "name": "Stage 2",
            "dry_mass": 8000,
            "fuel_mass": 100000,
            "isp": 340,
            "thrust": 1_000_000,
            "burn_rate": 600,
        },
        {
            "name": "Stage 3",
            "dry_mass": 2000,
            "fuel_mass": 20000,
            "isp": 360,
            "thrust": 250_000,
            "burn_rate": 120,
        },
    ]

    payload_mass = 5000

    stage_results, total_delta_v, total_losses, net_delta_v = calculate_ideal_multistage(
        stages, payload_mass
    )

    sim_drag = simulate_multistage_rocket_with_drag(
        stages,
        payload_mass,
        dt=0.1,
        cd=1.5,
        area=60.0,
    )

    times_no_drag, vel_no_drag, h_no_drag = simulate_no_drag(stages, payload_mass)

    print_ideal_results(stage_results, total_delta_v, total_losses, net_delta_v)
    print_drag_simulation_results(sim_drag)

    plot_delta_v(stage_results, total_losses, net_delta_v)
    plot_velocity_time(
        sim_drag["times"],
        sim_drag["velocities"],
        sim_drag["stage_time_ranges"],
        "Velocity vs Time (With Drag)",
        "velocity_graph_drag.png"
    )
    plot_height_time(
        sim_drag["times"],
        sim_drag["heights"],
        sim_drag["stage_time_ranges"],
        "Height vs Time (With Drag)",
        "height_graph_drag.png"
    )
    plot_drag_time(sim_drag["times"], sim_drag["drags"], sim_drag["stage_time_ranges"])
    plot_velocity_comparison(times_no_drag, vel_no_drag, sim_drag["times"], sim_drag["velocities"])
    plot_height_comparison(times_no_drag, h_no_drag, sim_drag["times"], sim_drag["heights"])

    payload_values = [2000, 5000, 10000]
    sensitivity_results = run_payload_sensitivity_analysis(
        stages,
        payload_values,
        dt=0.1,
        cd=1.5,
        area=60.0
    )
    print_payload_sensitivity_results(sensitivity_results)
    plot_payload_sensitivity(sensitivity_results)

    print("Graphs saved successfully:")
    print("- delta_v_graph.png")
    print("- velocity_graph_drag.png")
    print("- height_graph_drag.png")
    print("- drag_force_graph.png")
    print("- comparison_velocity.png")
    print("- comparison_height.png")
    print("- payload_vs_velocity.png")
    print("- payload_vs_height.png")

    print("\nModel limitations:")
    print("- Vertical flight only")
    print("- Constant thrust")
    print("- Simplified atmospheric density model")
    print("- No pitch maneuver or orbital insertion mechanics")


if __name__ == "__main__":
    main()
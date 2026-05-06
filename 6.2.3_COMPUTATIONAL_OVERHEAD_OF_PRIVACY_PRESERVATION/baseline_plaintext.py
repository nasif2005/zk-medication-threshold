import time
import statistics


def baseline_check(history_q, history_t, q_current, t_current, window, max_quantity):
    """
    Plaintext baseline:
    1. Rolling-window threshold check
    2. State update by overwriting an empty or expired slot

    Returns True if the request is accepted and the state is updated.
    Returns False otherwise.
    """

    # Step 1: compute active sum
    active_sum = 0
    for q, t in zip(history_q, history_t):
        if t != 0 and 0 <= (t_current - t) < window:
            active_sum += q

    # Step 2: threshold condition
    if active_sum + q_current > max_quantity:
        return False

    # Step 3: find overwrite slot
    for i in range(len(history_q)):
        if history_t[i] == 0 or (t_current - history_t[i]) >= window:
            history_q[i] = q_current
            history_t[i] = t_current
            return True

    return False


def build_input(k):
    """
    Build the same synthetic history pattern used in the zk experiments.
    """

    history_q = [20, 15] + [0] * (k - 2)
    history_t = [90, 80] + [0] * (k - 2)

    q_current = 10
    t_current = 100
    window = 30
    max_quantity = 60

    return history_q, history_t, q_current, t_current, window, max_quantity


def run_single(k):
    """
    Single measured execution for a given k.
    """

    history_q, history_t, q_current, t_current, window, max_quantity = build_input(k)

    start = time.perf_counter()
    baseline_check(
        history_q.copy(),
        history_t.copy(),
        q_current,
        t_current,
        window,
        max_quantity,
    )
    end = time.perf_counter()

    return end - start


def run_experiment(k, runs=10000):
    """
    Run the plaintext baseline multiple times to obtain a stable average.
    """

    times = [run_single(k) for _ in range(runs)]

    avg_s = statistics.mean(times)

    return {
        "avg_s": avg_s,
        "avg_us": avg_s * 1_000_000,
        "min_s": min(times),
        "max_s": max(times),
    }


if __name__ == "__main__":
    k_values = [10, 15, 20]
    runs = 10000

    print(f"Plaintext baseline over {runs} runs")
    print("k\tavg_time(s)\tavg_time(us)\tmin(s)\t\tmax(s)")

    for k in k_values:
        result = run_experiment(k, runs=runs)
        print(
            f"{k}\t"
            f"{result['avg_s']:.8f}\t"
            f"{result['avg_us']:.3f}\t\t"
            f"{result['min_s']:.8f}\t"
            f"{result['max_s']:.8f}"
        )
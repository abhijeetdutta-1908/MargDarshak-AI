"""Visit-order optimisation over a distance matrix.

nearest_neighbor() builds a greedy tour from the start point; two_opt() then repeatedly reverses
segments while that shortens the route, and or_opt() relocates short runs of stops. The two local
searches alternate until neither helps. See tests/test_external.py for the measured optimality gap
against brute force.
"""

Matrix = list[list[float]]


class RouteOptimizer:
    def __init__(self, km: Matrix, minutes: Matrix | None = None, start: int = 0, return_to_start: bool = False):
        self.km = km
        self.minutes = minutes
        self.start = start
        self.return_to_start = return_to_start
        self.n = len(km)

    @staticmethod
    def calculate_distance_matrix(points: list[tuple[float, float]], road_factor: float = 1.3) -> Matrix:
        from app.ml.recommendation import haversine_km

        return [[0.0 if i == j else haversine_km(a, b) * road_factor for j, b in enumerate(points)]
                for i, a in enumerate(points)]

    def _cost(self, order: list[int], m: Matrix) -> float:
        legs = sum(m[a][b] for a, b in zip(order, order[1:], strict=False))
        return legs + (m[order[-1]][order[0]] if self.return_to_start and len(order) > 1 else 0)

    def calculate_total_distance(self, order: list[int]) -> float:
        return round(self._cost(order, self.km), 2)

    def calculate_estimated_duration(self, order: list[int]) -> float:
        return round(self._cost(order, self.minutes), 1) if self.minutes else 0.0

    def nearest_neighbor(self) -> list[int]:
        order, left = [self.start], set(range(self.n)) - {self.start}
        while left:
            nxt = min(left, key=lambda j: (self.km[order[-1]][j], j))
            order.append(nxt)
            left.remove(nxt)
        return order

    def two_opt(self, order: list[int]) -> list[int]:
        best, best_cost = order[:], self._cost(order, self.km)
        improved = True
        while improved:
            improved = False
            for i in range(1, len(best) - 1):  # index 0 (the start) stays fixed
                for j in range(i + 1, len(best)):
                    cand = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                    cost = self._cost(cand, self.km)
                    if cost < best_cost - 1e-9:
                        best, best_cost, improved = cand, cost, True
        return best

    def or_opt(self, order: list[int]) -> list[int]:
        """Move runs of 1-3 consecutive stops to a better position (escapes many 2-opt local optima)."""
        best, best_cost = order[:], self._cost(order, self.km)
        improved = True
        while improved:
            improved = False
            for size in (1, 2, 3):
                for i in range(1, len(best) - size + 1):
                    seg, rest = best[i:i + size], best[:i] + best[i + size:]
                    for j in range(1, len(rest) + 1):
                        if j == i:
                            continue
                        for s in (seg, seg[::-1]):
                            cand = rest[:j] + s + rest[j:]
                            cost = self._cost(cand, self.km)
                            if cost < best_cost - 1e-9:
                                best, best_cost, improved = cand, cost, True
        return best

    def improve(self, order: list[int]) -> list[int]:
        """Alternate 2-opt and Or-opt until neither finds an improvement."""
        while True:
            new = self.or_opt(self.two_opt(order))
            if self._cost(new, self.km) >= self._cost(order, self.km) - 1e-9:
                return new
            order = new

    def optimize(self) -> dict:
        if self.n <= 1:
            return {"order": list(range(self.n)), "total_distance_km": 0.0, "total_duration_minutes": 0.0,
                    "initial_distance_km": 0.0}
        naive = [self.start] + [i for i in range(self.n) if i != self.start]
        order = self.improve(self.nearest_neighbor())
        legs = order + ([order[0]] if self.return_to_start else [])
        return {
            "order": order,
            "legs": [{"from": a, "to": b, "distance_km": round(self.km[a][b], 2),
                      "duration_minutes": round(self.minutes[a][b], 1) if self.minutes else None}
                     for a, b in zip(legs, legs[1:], strict=False)],
            "total_distance_km": self.calculate_total_distance(order),
            "total_duration_minutes": self.calculate_estimated_duration(order),
            "initial_distance_km": self.calculate_total_distance(naive),  # input order, for comparison
        }

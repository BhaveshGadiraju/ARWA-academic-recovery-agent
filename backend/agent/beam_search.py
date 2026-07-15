from copy import deepcopy


class BeamSearchPlanner:
    """
    Uses heuristic beam search to efficiently explore
    recovery strategies without evaluating every
    possible task combination.
    """

    def __init__(

        self,

        evaluator,

        beam_width=5,

    ):

        self.evaluator = evaluator

        self.beam_width = beam_width

    # ---------------------------------------------

    def search(

        self,

        tasks,

        state,

    ):

        ranked = sorted(

            tasks,

            key=self._priority,

            reverse=True,

        )

        beam = [

            []

        ]

        for task in ranked:

            candidates = []

            for plan in beam:

                # Keep existing plan
                candidates.append(plan)

                # Expand plan
                expanded = deepcopy(plan)
                expanded.append(task)

                if self._within_time(

                    expanded,

                    state.available_time,

                ):

                    candidates.append(expanded)

            # Evaluate every candidate
            scored = []

            for plan in candidates:

                score = self.evaluator.evaluate(

                    plan,

                    state,

                )["recovery_score"]

                scored.append(

                    (

                        score,

                        plan,

                    )

                )

            # Keep only the best K plans
            scored.sort(

                key=lambda x: x[0],

                reverse=True,

            )

            beam = [

                p

                for _, p in scored[:self.beam_width]

            ]

        return beam

    # ---------------------------------------------

    def _priority(

        self,

        task,

    ):

        return (

            task["points_value"] * 3

            + max(

                0,

                72 - task["due_in_hours"],

            )

            - task["difficulty"] * 2

            - task["estimated_time"]

        )

    # ---------------------------------------------

    def _within_time(

        self,

        tasks,

        limit,

    ):

        total = sum(

            t["estimated_time"]

            for t in tasks

        )

        return total <= limit
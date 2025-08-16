# utils/parent_selection.py
import numpy as np
from typing import List, Dict
import math


class ChessParentSelector:
    def __init__(self, lambda_param=10, alpha_midpoint=0.5, k_parallel=2):
        self.lambda_param = lambda_param  # Sigmoid sharpness
        self.alpha_midpoint = alpha_midpoint  # Midpoint accuracy
        self.k_parallel = k_parallel  # Number of parallel improvements

    def select_parents(self, archive: List[Dict]) -> List[str]:
        """
        Select k parents using paper-exact algorithm

        Args:
            archive: List of agent metadata with performance and children info

        Returns:
            List of selected parent agent IDs
        """

        # Step 1: Define eligible set E_t (agents with performance < 1.0)
        eligible_agents = [agent for agent in archive if agent['performance'] < 1.0]

        if not eligible_agents:
            # All agents are perfect - select from full archive
            eligible_agents = archive

        # Step 2: Calculate selection probabilities
        weights = []
        for agent in eligible_agents:
            # Performance score (α_i)
            alpha_i = agent['performance']

            # Children count (n_i)
            n_i = agent['functioning_children_count']

            # Sigmoid-scaled performance (s_i)
            s_i = 1 / (1 + math.exp(-self.lambda_param * (alpha_i - self.alpha_midpoint)))

            # Novelty bonus (h_i) - favors agents with fewer children
            h_i = 1 / (1 + n_i)

            # Unnormalized weight (w_i)
            w_i = s_i * h_i
            weights.append(w_i)

        # Step 3: Normalize to get selection probabilities (p_i)
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]

        # Step 4: Sample k parents (with replacement)
        selected_indices = np.random.choice(
            len(eligible_agents),
            size=self.k_parallel,
            replace=True,
            p=probabilities
        )

        selected_parents = [eligible_agents[i]['agent_id'] for i in selected_indices]

        return selected_parents

    def update_children_count(self, archive: List[Dict], parent_id: str, child_successful: bool):
        """Update functioning children count for parent"""
        for agent in archive:
            if agent['agent_id'] == parent_id:
                if child_successful:
                    agent['functioning_children_count'] += 1
                break
"""A simple policy-gradient reinforcement-learning agent."""

from collections import defaultdict
import json
import math
import random
from pathlib import Path

from .rl_features import FEATURE_NAMES, extract_move_features

DEFAULT_RL_WEIGHTS = {
    "finish": 7.0,
    "capture": 0.8,
    "double": 2.0,
    "progress": 2.0,

    # Old binary danger features
    #"lands_in_danger": -0.5,
    #"escapes_danger": 0.5,

    # New count-based danger features
    "current_danger_count": 0.0,
    "landing_danger_count": -1.5,
    "danger_reduction": 1.0,

    "captured_piece_progress": 0.5,
}

class RLAgent:
    """
    A linear softmax policy.

    It scores each legal move like this:

        score = sum(weight[feature] * feature_value)

    During training, it samples moves from a softmax distribution.
    During evaluation, it chooses the highest-scoring move.
    """

    def __init__(
        self,
        weights=None,
        training=True,
        temperature=1.0,
        weight_clip=10.0,
    ):
        self.weights = weights or DEFAULT_RL_WEIGHTS.copy()
        self.training = training
        self.temperature = temperature
        self.weight_clip = weight_clip

        self.current_episode_grad = defaultdict(float)
        self.current_episode_move_count = 0
        self.completed_episodes = []

    def score_features(self, features):
        return sum(
            self.weights[name] * features.get(name, 0.0)
            for name in FEATURE_NAMES
        )

    def get_move_probabilities(self, move_features):
        """
        Softmax over legal moves.
        """
        scores = [
            self.score_features(features) / self.temperature
            for features in move_features
        ]

        # Numerical stability
        max_score = max(scores)
        exp_scores = [math.exp(score - max_score) for score in scores]
        total = sum(exp_scores)

        return [value / total for value in exp_scores]

    def choose_index_from_probs(self, probs):
        r = random.random()
        cumulative = 0.0

        for index, prob in enumerate(probs):
            cumulative += prob
            if r <= cumulative:
                return index

        return len(probs) - 1

    def __call__(self, state, color, roll, legal_moves):
        if not legal_moves:
            return None

        move_features = [
            extract_move_features(state, color, move)
            for move in legal_moves
        ]

        if self.training:
            probs = self.get_move_probabilities(move_features)
            chosen_index = self.choose_index_from_probs(probs)
            chosen_features = move_features[chosen_index]

            # Policy-gradient update term:
            # chosen_features - expected_features
            expected_features = {name: 0.0 for name in FEATURE_NAMES}

            for prob, features in zip(probs, move_features):
                for name in FEATURE_NAMES:
                    expected_features[name] += prob * features[name]

            for name in FEATURE_NAMES:
                self.current_episode_grad[name] += (
                    chosen_features[name] - expected_features[name]
                )

            self.current_episode_move_count += 1

            return legal_moves[chosen_index]

        # Evaluation mode: choose best move deterministically.
        best_index = max(
            range(len(legal_moves)),
            key=lambda index: self.score_features(move_features[index]),
        )
        return legal_moves[best_index]

    def start_episode(self):
        self.current_episode_grad = defaultdict(float)
        self.current_episode_move_count = 0

    def end_episode(self, reward):
        """
        Store this episode's gradient and reward.

        We normalize by number of moves so one long game doesn't dominate
        the batch update too much.
        """
        if self.current_episode_move_count > 0:
            normalized_grad = {
                name: self.current_episode_grad[name] / self.current_episode_move_count
                for name in FEATURE_NAMES
            }
        else:
            normalized_grad = {name: 0.0 for name in FEATURE_NAMES}

        self.completed_episodes.append(
            {
                "reward": reward,
                "grad": normalized_grad,
            }
        )

        self.start_episode()

    def update_from_batch(self, learning_rate=0.1):
        """
        Update weights after a batch of games.

        Uses reward - average_reward as the advantage, which reduces noise.
        """
        if not self.completed_episodes:
            return

        average_reward = sum(
            episode["reward"] for episode in self.completed_episodes
        ) / len(self.completed_episodes)

        batch_grad = {name: 0.0 for name in FEATURE_NAMES}

        for episode in self.completed_episodes:
            advantage = episode["reward"] - average_reward

            for name in FEATURE_NAMES:
                batch_grad[name] += advantage * episode["grad"][name]

        batch_size = len(self.completed_episodes)

        for name in FEATURE_NAMES:
            self.weights[name] += learning_rate * batch_grad[name] / batch_size

            # Clip weights so they don't explode.
            self.weights[name] = max(
                -self.weight_clip,
                min(self.weight_clip, self.weights[name]),
            )

        self.completed_episodes = []

    def save_weights(self, filename):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as file:
            json.dump(self.weights, file, indent=2)

        return path

    def load_weights(self, filename):
        with Path(filename).open("r") as file:
            loaded_weights = json.load(file)

        self.weights = DEFAULT_RL_WEIGHTS.copy()
        self.weights.update(loaded_weights)

        self.weights = {
            name: self.weights.get(name, DEFAULT_RL_WEIGHTS.get(name, 0.0))
            for name in FEATURE_NAMES
        }

    def pretty_weights(self):
        return {
            name: round(self.weights[name], 4)
            for name in FEATURE_NAMES
        }
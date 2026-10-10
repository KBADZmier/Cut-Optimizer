"""Stałe konfiguracyjne optymalizatora."""

import logging

# Mnożnik skalujący milimetry do liczb całkowitych (CP-SAT operuje na int).
SCALE = 10

#budzety
TOTAL_TIME_BUDGET_SECONDS = 240.0
NUM_OPTIMIZATION_STAGES = 3

NUM_SEARCH_WORKERS = 8

PROFILE_COUNT_GAP_TOLERANCE = 1.0


STRICT_GAP_TOLERANCE = 0.0001


PROFILE_LENGTH_GAP_TOLERANCE = 6000.0 * SCALE

logger = logging.getLogger(__name__)
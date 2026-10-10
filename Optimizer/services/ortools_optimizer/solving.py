
from ortools.sat.python import cp_model
from .constants import (
    NUM_OPTIMIZATION_STAGES,
    NUM_SEARCH_WORKERS,
    PROFILE_COUNT_GAP_TOLERANCE,
    PROFILE_LENGTH_GAP_TOLERANCE,
    STRICT_GAP_TOLERANCE,
    TOTAL_TIME_BUDGET_SECONDS,
    logger,
)
from .types import ModelVariables, ScaledInputs


def solve_lexicographic(
    model: cp_model.CpModel,
    variables: ModelVariables,
    scaled: ScaledInputs,
) -> cp_model.CpSolver:
    total_waste = sum(variables.waste)
    total_profiles = sum(variables.profile_used)
    total_profile_length = sum(
        scaled.profile_lengths[index] * variables.profile_used[index]
        for index in range(len(variables.profile_used))
    )

    stage_time_budget = TOTAL_TIME_BUDGET_SECONDS / NUM_OPTIMIZATION_STAGES

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = NUM_SEARCH_WORKERS

    best_waste = _solve_stage(
        model, solver, variables, total_waste, "minimalny odpad", stage_time_budget
    )
    model.Add(total_waste == best_waste)
    _apply_solution_as_hint(model, solver, variables)

    best_profiles = _solve_stage(
        model,
        solver,
        variables,
        total_profiles,
        "minimalna liczba profili",
        stage_time_budget,
        absolute_gap_limit=PROFILE_COUNT_GAP_TOLERANCE,
    )
    model.Add(total_profiles == best_profiles)
    _apply_solution_as_hint(model, solver, variables)

    _solve_stage(
        model,
        solver,
        variables,
        total_profile_length,
        "minimalna długość profili",
        stage_time_budget,
        absolute_gap_limit=PROFILE_LENGTH_GAP_TOLERANCE,
    )

    return solver


def _solve_stage(
    model: cp_model.CpModel,
    solver: cp_model.CpSolver,
    variables: ModelVariables,
    objective_expression,
    stage_name: str,
    time_budget_seconds: float,
    absolute_gap_limit: float = STRICT_GAP_TOLERANCE,
    strict_phase_fraction: float = 0.2,
) -> int:
    
    model.Minimize(objective_expression)

    if absolute_gap_limit > STRICT_GAP_TOLERANCE:
        strict_time_budget = max(1.0, time_budget_seconds * strict_phase_fraction)
        solver.parameters.max_time_in_seconds = strict_time_budget
        solver.parameters.absolute_gap_limit = STRICT_GAP_TOLERANCE

        status = solver.Solve(model)

        if status == cp_model.OPTIMAL:

            return solver.Value(objective_expression)

        if status == cp_model.FEASIBLE:
            _apply_solution_as_hint(model, solver, variables)

        remaining_time_budget = max(
            1.0, time_budget_seconds - strict_time_budget
        )
        solver.parameters.max_time_in_seconds = remaining_time_budget
        solver.parameters.absolute_gap_limit = absolute_gap_limit
    else:
        solver.parameters.max_time_in_seconds = time_budget_seconds
        solver.parameters.absolute_gap_limit = absolute_gap_limit

    status = solver.Solve(model)

    if status == cp_model.INFEASIBLE:
        raise ValueError(
            "OR-Tools potwierdził, że problem jest niewykonalny "
            f"(etap: {stage_name})."
        )

    if status == cp_model.MODEL_INVALID:
        raise ValueError(
            f"OR-Tools zgłosił nieprawidłowy model (etap: {stage_name}). "
            f"Szczegóły walidacji: {model.Validate()}"
        )

    if status == cp_model.UNKNOWN:
        raise ValueError(
            "OR-Tools nie zakończył obliczeń w wyznaczonym czasie "
            f"(etap: {stage_name}). Limit: {time_budget_seconds:.1f} s."
        )

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise ValueError(
            f"Nieoczekiwany status OR-Tools: {status} (etap: {stage_name})"
        )

    if status == cp_model.FEASIBLE:
        logger.warning(
            "Etap '%s': solver zwrócił rozwiązanie FEASIBLE (nie OPTIMAL) "
            "po przekroczeniu limitu %.1f s, nawet z tolerancją %.4f. "
            "Wynik dla tego kryterium może nie być najlepszy z możliwych "
            "-- rozważ zwiększenie TOTAL_TIME_BUDGET_SECONDS albo "
            "tolerancji.",
            stage_name,
            time_budget_seconds,
            absolute_gap_limit,
        )
    elif absolute_gap_limit > STRICT_GAP_TOLERANCE:
        # OPTIMAL, ale tylko w granicach świadomie przyjętej tolerancji --
        # nie mylić z dowiedzioną, ścisłą optymalnością.
        logger.info(
            "Etap '%s': wynik OPTIMALNY W GRANICACH TOLERANCJI %.1f "
            "(nie ściśle udowodniony jako bezwzględne minimum).",
            stage_name,
            absolute_gap_limit,
        )

    return solver.Value(objective_expression)


def _apply_solution_as_hint(
    model: cp_model.CpModel,
    solver: cp_model.CpSolver,
    variables: ModelVariables,
) -> None:

    model.clear_hints()

    for variable in variables.assignment.values():
        model.add_hint(variable, solver.Value(variable))

    for variable_list in (
        variables.profile_used,
        variables.cut_count,
        variables.material_length,
        variables.remaining,
        variables.waste,
    ):
        for variable in variable_list:
            model.add_hint(variable, solver.Value(variable))